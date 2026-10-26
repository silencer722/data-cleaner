import unittest
import tempfile
from pathlib import Path

import pandas as pd

from src.cleaner import (
    clean_data,
    inspect_data,
    generate_report,
    run_pipeline,
    validate_data,
    standardize_types,
)


class TestCleaner(unittest.TestCase):

    def setUp(self):
        self.df = pd.DataFrame({
            "Category": ["Fruit", "Fruit", "Fruit", "Bakery"],
            "Item": ["Apple", "Apple", None, "Bread"],
            "Price Per Unit": [1.5, None, 1.5, 2.0],
            "Quantity": [2.0, 2.0, 1.0, 3.0],
            "Total Spent": [3.0, 3.0, 1.5, 6.0],
            "Discount Applied": [False, True, None, False],
        })

    def test_clean_data_fills_recoverable_values(self):
        cleaned = clean_data(self.df)

        self.assertEqual(cleaned.loc[1, "Price Per Unit"], 1.5)
        self.assertEqual(cleaned.loc[2, "Item"], "Apple")

    def test_clean_data_does_not_modify_original(self):
        original = self.df.copy(deep=True)

        clean_data(self.df)

        pd.testing.assert_frame_equal(self.df, original)

    def test_clean_data_preserves_unrecoverable_values(self):
        unknown = pd.DataFrame({
            "Category": ["Unknown"],
            "Item": ["Mystery"],
            "Price Per Unit": [None],
            "Quantity": [None],
            "Total Spent": [None],
            "Discount Applied": [None],
        })

        data = pd.concat([self.df, unknown], ignore_index=True)
        cleaned = clean_data(data)

        self.assertTrue(pd.isna(cleaned.loc[4, "Price Per Unit"]))

    def test_inspect_data_counts_missing_and_duplicate_rows(self):
        df = pd.DataFrame({
            "value": [1, None, 1],
            "name": ["a", "a", "a"],
        })

        report = inspect_data(df)

        self.assertEqual(report["rows"], 3)
        self.assertEqual(report["columns"], 2)
        self.assertEqual(report["missing_values"], {"value": 1})
        self.assertEqual(report["duplicate_rows"], 1)

    def test_generate_report_contains_summary(self):
        report = inspect_data(self.df)
        report_text = generate_report(report)

        self.assertIn("DATA QUALITY REPORT", report_text)
        self.assertIn("Rows: 4", report_text)
        self.assertIn("Columns: 6", report_text)
        self.assertIn("Data types:", report_text)
        self.assertIn("- Category:", report_text)
        self.assertIn("Duplicate rows:", report_text)

    def test_pipeline_creates_output_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            input_path = temp_path / "input.csv"
            output_path = temp_path / "output" / "cleaned.csv"
            report_path = temp_path / "output" / "report.txt"

            self.df.to_csv(input_path, index=False)

            cleaned, report = run_pipeline(
                input_path,
                output_path,
                report_path,
            )

            self.assertTrue(output_path.exists())
            self.assertTrue(report_path.exists())
            self.assertEqual(cleaned.shape, self.df.shape)
            self.assertEqual(report["rows"], 4)
            self.assertEqual(report["filled_values"]["Item"], 1)
            self.assertEqual(report["filled_values"]["Price Per Unit"], 1)
    def test_validate_data_detects_known_problems(self):
        df = pd.DataFrame({
            "Transaction ID": ["TXN_1", "TXN_1", "TXN_3"],
            "Transaction Date": [
                "2024-01-01",
                "not-a-date",
                "2024-01-03",
            ],
            "Price Per Unit": [2.0, 3.0, -1.0],
            "Quantity": [2.0, 2.0, 1.0],
            "Total Spent": [4.0, 99.0, -1.0],
            "Discount Applied": [True, "unknown", None],
        })

        checks = validate_data(df)

        self.assertEqual(checks["duplicate_transaction_ids"], 1)
        self.assertEqual(checks["invalid_transaction_dates"], 1)
        self.assertEqual(checks["nonpositive_prices"], 1)
        self.assertEqual(checks["nonpositive_quantities"], 0)
        self.assertEqual(checks["total_spent_mismatches"], 1)
        self.assertEqual(checks["invalid_discount_values"], 1)

    def test_standardize_types(self):
        df = pd.DataFrame({
            "Transaction Date": [
                "2024-01-01",
                "2024-01-02",
            ],
            "Quantity": [2.0, None],
            "Discount Applied": [True, None],
        })

        result = standardize_types(df)

        self.assertTrue(
            pd.api.types.is_datetime64_any_dtype(
                result["Transaction Date"]
            )
        )
        self.assertEqual(str(result["Quantity"].dtype), "Int64")
        self.assertEqual(
            str(result["Discount Applied"].dtype),
            "boolean",
        )
        self.assertTrue(pd.isna(result.loc[1, "Quantity"]))
        self.assertTrue(pd.isna(result.loc[1, "Discount Applied"]))

if __name__ == "__main__":
    unittest.main()