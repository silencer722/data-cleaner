import pandas as pd
from pathlib import Path

def load_data(file_path):

    df = pd.read_csv(file_path)

    return df

def inspect_data(df):

    missing = df.isna().sum()
    missing = missing[missing > 0]

    report = {
        "rows" : df.shape[0],
        "columns" : df.shape[1],
        "missing_values" : missing.to_dict(),
        "dtypes" : df.dtypes,
        "duplicate_rows" : df.duplicated().sum()
    }
    return report

def validate_data(df):
    """Check data quality rules without modifying the DataFrame."""

    checks = {}

    if "Transaction ID" in df.columns:
        checks["duplicate_transaction_ids"] = int(
            df["Transaction ID"].duplicated().sum()
        )

    if "Transaction Date" in df.columns:
        dates = pd.to_datetime(
            df["Transaction Date"],
            errors="coerce",
        )
        checks["invalid_transaction_dates"] = int(
            dates.isna().sum()
        )

    if "Price Per Unit" in df.columns:
        prices = df["Price Per Unit"]
        checks["nonpositive_prices"] = int(
            (prices.notna() & prices.le(0)).sum()
        )

    if "Quantity" in df.columns:
        quantities = df["Quantity"]
        checks["nonpositive_quantities"] = int(
            (quantities.notna() & quantities.le(0)).sum()
        )

    required = ["Price Per Unit", "Quantity", "Total Spent"]

    if all(column in df.columns for column in required):
        complete = df[required].notna().all(axis=1)

        expected = (
            df.loc[complete, "Price Per Unit"]
            * df.loc[complete, "Quantity"]
        )

        difference = (
            df.loc[complete, "Total Spent"] - expected
        ).abs()

        checks["total_spent_mismatches"] = int(
            difference.gt(0.01).sum()
        )

    if "Discount Applied" in df.columns:
        discounts = df["Discount Applied"].dropna()

        checks["invalid_discount_values"] = int(
            (~discounts.isin([True, False])).sum()
        )

    return checks

def generate_report(report):
    lines = []

    lines.append("DATA QUALITY REPORT")
    lines.append("===================")
    lines.append("")

    lines.append(f"Rows: {report['rows']}")
    lines.append(f"Columns: {report['columns']}")
    lines.append("")

    lines.append("Cleaning summary:")

    filled_values = report.get("filled_values", {})

    if filled_values:
        for column, count in filled_values.items():
            lines.append(f"- {column}: {count} values recovered")
    else:
        lines.append("- No recovery counts provided")

    lines.append("")

    # Missing values
    lines.append("Missing values:")

    if report["missing_values"]:
        for column, count in report["missing_values"].items():
            lines.append(f"- {column}: {count}")
    else:
        lines.append("- None")

    lines.append("")

    # Data types
    lines.append("Data types:")

    for column, dtype in report["dtypes"].items():
        lines.append(f"- {column}: {dtype}")

    lines.append("")
    lines.append("Validation checks:")

    validation = report.get("validation", {})

    if validation:
        for check, count in validation.items():
            label = check.replace("_", " ").capitalize()
            lines.append(f"- {label}: {count}")
    else:
        lines.append("- Not run")

    # Duplicate rows
    lines.append(f"Duplicate rows: {report['duplicate_rows']}")

    return "\n".join(lines)


def save_report(report_text ,file_path):
    with open(file_path, "w") as file:
        file.write(report_text)

def standardize_types(df):
    """Convert columns to appropriate data types."""

    standardized = df.copy()

    # Ensure numeric columns contain numeric values.
    numeric_columns = [
        "Price Per Unit",
        "Quantity",
        "Total Spent",
    ]

    for column in numeric_columns:
        if column in standardized.columns:
            standardized[column] = pd.to_numeric(
                standardized[column],
                errors="raise",
            )

    # Use nullable integers when every known quantity is whole.
    if "Quantity" in standardized.columns:
        quantity = standardized["Quantity"]
        known_quantities = quantity.dropna()

        if known_quantities.mod(1).eq(0).all():
            standardized["Quantity"] = quantity.astype("Int64")

    # Convert transaction dates to datetime.
    if "Transaction Date" in standardized.columns:
        standardized["Transaction Date"] = pd.to_datetime(
            standardized["Transaction Date"],
            errors="coerce",
        )

    # Convert recognized discount values to a nullable Boolean type.
    if "Discount Applied" in standardized.columns:
        discounts = standardized["Discount Applied"]

        discount_map = {
            True: True,
            False: False,
            "True": True,
            "False": False,
            "true": True,
            "false": False,
            "TRUE": True,
            "FALSE": False,
        }

        converted = discounts.map(discount_map)

        # Preserve unexpected values rather than silently discarding them.
        recognized = discounts.isna() | converted.notna()

        if recognized.all():
            standardized["Discount Applied"] = converted.astype(
                "boolean"
            )

    return standardized


def clean_data(df):
    """Clean recoverable Item and Price Per Unit values."""

    cleaned = df.copy()

    # Use records with known items and prices as reference data.
    reference = df.dropna(
        subset=["Category", "Item", "Price Per Unit"]
    )

    # Build a lookup for unique prices by category and item.
    price_groups = (
        reference.groupby(["Category", "Item"])["Price Per Unit"]
        .agg(["first", "nunique"])
    )

    price_lookup = price_groups.loc[
        price_groups["nunique"] == 1, "first"
    ].to_dict()

    # Fill missing prices when the item uniquely identifies a price.
    mask = (
        cleaned["Price Per Unit"].isna()
        & cleaned["Category"].notna()
        & cleaned["Item"].notna()
    )

    cleaned.loc[mask, "Price Per Unit"] = [
        price_lookup.get((category, item))
        for category, item in zip(
            cleaned.loc[mask, "Category"],
            cleaned.loc[mask, "Item"],
        )
    ]

    # Recover prices mathematically when possible.
    mask = (
        cleaned["Price Per Unit"].isna()
        & cleaned["Quantity"].notna()
        & cleaned["Total Spent"].notna()
        & cleaned["Quantity"].ne(0)
    )

    cleaned.loc[mask, "Price Per Unit"] = (
        cleaned.loc[mask, "Total Spent"]
        / cleaned.loc[mask, "Quantity"]
    ).round(2)

    # Build a lookup for unique items by category and price.
    item_groups = (
        reference.groupby(["Category", "Price Per Unit"])["Item"]
        .agg(["first", "nunique"])
    )

    item_lookup = item_groups.loc[
        item_groups["nunique"] == 1, "first"
    ].to_dict()

    # Fill missing items only when the category and price
    # uniquely identify the item.
    mask = (
        cleaned["Item"].isna()
        & cleaned["Category"].notna()
        & cleaned["Price Per Unit"].notna()
    )

    cleaned.loc[mask, "Item"] = [
        item_lookup.get((category, price))
        for category, price in zip(
            cleaned.loc[mask, "Category"],
            cleaned.loc[mask, "Price Per Unit"],
        )
    ]

    return cleaned

def run_pipeline(input_path, output_path, report_path):
    """Load, clean, inspect, and save a dataset."""

    # 1. Load the original dataset.
    original_df = load_data(input_path)

    # 2. Standardize data types.
    standardized_df = standardize_types(original_df)

    # 3. Clean the dataset.
    cleaned_df = clean_data(standardized_df)

    # 4. Inspect the cleaned data.
    report = inspect_data(cleaned_df)

    # 5. Record how many missing values were recovered.
    report["filled_values"] = {
        column: int(
            (
                original_df[column].isna()
                & cleaned_df[column].notna()
            ).sum()
        )
        for column in ["Item", "Price Per Unit"]
        if column in original_df.columns
    }

    # 6. Validate the cleaned dataset.
    report["validation"] = validate_data(cleaned_df)

    # 7. Generate the quality report.
    report_text = generate_report(report)

    # 8. Create output directories if necessary.
    Path(output_path).parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    Path(report_path).parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # 9. Save the cleaned dataset and report.
    cleaned_df.to_csv(output_path, index=False)
    save_report(report_text, report_path)

    return cleaned_df, report


if __name__ == "__main__":
    cleaned_df, report = run_pipeline(
        input_path="input/messy_data.csv",
        output_path="output/cleaned_data.csv",
        report_path="output/data_quality_report.txt",
    )

    print("Pipeline completed successfully!")
    print(f"Rows: {cleaned_df.shape[0]}")
    print(f"Columns: {cleaned_df.shape[1]}")

    print("\nMissing values after cleaning:")
    print(cleaned_df.isna().sum().to_string())

    print("\nFiles saved:")
    print("- output/cleaned_data.csv")
    print("- output/data_quality_report.txt")