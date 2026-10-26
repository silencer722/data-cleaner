# Retail Store Sales — Data Cleaning Pipeline

A reusable Python data-cleaning pipeline built with pandas.
The project focuses on recovering missing values when the
available data supports a reliable inference, standardizing
data types, validating data quality, and generating reports.

## Features

- Load CSV datasets using pandas.
- Inspect missing values, data types, and duplicate rows.
- Recover missing Item values using category and price relationships.
- Recover missing Price Per Unit values using known relationships
  and transaction totals when sufficient information is available.
- Standardize numeric, date, quantity, and discount data types.
- Validate transaction IDs, dates, prices, quantities, totals,
  and discount values.
- Generate a data-quality report.
- Run automated tests with Python's unittest framework.

## Project Structure

    data-cleaner/
    ├── input/
    ├── output/
    ├── src/
    │   └── cleaner.py
    ├── tests/
    │   └── test_cleaner.py
    ├── .gitignore
    ├── README.md
    └── requirements.txt

## Requirements

- Python 3.12 or a compatible Python version
- pandas

## Installation

Create a virtual environment:

    python3 -m venv .venv

Activate it on Linux:

    source .venv/bin/activate

Install dependencies:

    pip install -r requirements.txt

## Input Dataset

Place the source CSV file at:

    input/messy_data.csv

The dataset is not included in this repository. Obtain it from
a source whose license permits your intended use.

## Run the Pipeline

From the project root directory, execute:

    .venv/bin/python src/cleaner.py

The pipeline generates:

    output/cleaned_data.csv
    output/data_quality_report.txt

The original input file is preserved.

## Run the Tests

Execute:

    .venv/bin/python -m unittest discover -s tests -v

The tests cover cleaning behavior, missing-value handling,
data inspection, report generation, type standardization,
validation, and pipeline output.

## Data Quality and Missing Values

The cleaning process only recovers values when the available
relationships provide a sufficiently unambiguous result.

Missing values in Quantity, Total Spent, and Discount Applied
are preserved when they cannot be reliably inferred.

The report summarizes recovered values, remaining missing
values, data types, duplicates, and validation results.

## Current Dataset Results

For the dataset currently tested:

- Rows processed: 12,575
- Columns: 11
- Item values recovered: 1,213
- Price Per Unit values recovered: 609
- Duplicate transaction IDs: 0
- Invalid transaction dates: 0
- Nonpositive prices: 0
- Nonpositive quantities: 0
- Total Spent mismatches: 0
- Invalid discount values: 0

These results describe the current dataset and are not
guaranteed for other input files.