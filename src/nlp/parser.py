import re
from pathlib import Path

import pandas as pd


# Excel file that contains the analysis data
INPUT_FILE = Path("data/raw/core/analysis.xlsx")

# Folder where the output files will be stored
OUTPUT_DIR = Path("output")

# Output CSV files
PARSED_FILE = OUTPUT_DIR / "analysis_parsed.csv"
FAILURES_FILE = OUTPUT_DIR / "parse_failures.csv"


# These are the columns we need to extract from the Excel file
TARGET_FIELDS = [
    "compounded_sales_growth",
    "compounded_profit_growth",
    "stock_price_cagr",
    "roe",
]


# This pattern handles values such as:
# 10 Years: 21%
# 5 Years: 24%
# 3 Years: 17%
# 1 Year: -2%
# TTM: 43%
# Last Year: 12%
#
# It captures the number of years when one is present,
# and also captures the percentage value.
PATTERN = re.compile(
    r"(?:(\d+)\s*Years?|TTM|Last\s+Year)\s*:?\s*(-?[\d.]+)%"
)


def parse_value(text):
    """
    Extract the period and percentage from an Excel cell.
    """

    # Ignore empty cells
    if pd.isna(text):
        return None

    # Convert the cell value to text
    text = str(text)

    # Try to find a matching value
    match = PATTERN.search(text)

    # If nothing matches, return None
    if not match:
        return None

    # Get the percentage value
    value_pct = float(match.group(2))

    # TTM and Last Year do not have a numeric period.
    # For those values, we keep the period as None.
    if match.group(1):
        period_years = int(match.group(1))
    else:
        period_years = None

    return period_years, value_pct


def main():
    # Make sure the output folder exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Read the Excel file.
    # The column names are on the second row,
    # so header=1 is used.
    df = pd.read_excel(INPUT_FILE, header=1)

    # Store successfully parsed values here
    parsed_rows = []

    # Store values that could not be parsed here
    failure_rows = []

    # Go through each company in the Excel file
    for _, row in df.iterrows():

        # Get the company ID
        company_id = row["company_id"]

        # Process each of the required columns
        for metric_type in TARGET_FIELDS:

            # Get the value from the current cell
            text = row[metric_type]

            # Try to extract the period and percentage
            result = parse_value(text)

            # If the value could not be read,
            # save it in the failure file
            if result is None:
                failure_rows.append({
                    "company_id": company_id,
                    "metric_type": metric_type,
                    "raw_text": text,
                })
                continue

            # Get the extracted period and percentage
            period_years, value_pct = result

            # Save the successfully parsed value
            parsed_rows.append({
                "company_id": company_id,
                "metric_type": metric_type,
                "period_years": period_years,
                "value_pct": value_pct,
            })

    # Turn the successful results into a DataFrame
    parsed_df = pd.DataFrame(
        parsed_rows,
        columns=[
            "company_id",
            "metric_type",
            "period_years",
            "value_pct",
        ],
    )

    # Turn the failed results into a DataFrame
    failures_df = pd.DataFrame(
        failure_rows,
        columns=[
            "company_id",
            "metric_type",
            "raw_text",
        ],
    )

    # Save the successful results
    parsed_df.to_csv(PARSED_FILE, index=False)

    # Save the failed results
    failures_df.to_csv(FAILURES_FILE, index=False)

    # Print a simple summary
    print("Parsed records:", len(parsed_df))
    print("Parse failures:", len(failures_df))
    print("Created:", PARSED_FILE)
    print("Created:", FAILURES_FILE)


# Run the program
if __name__ == "__main__":
    main()
