import os
import glob
import pandas as pd

from normaliser import (
    normalize_year,
    normalize_ticker,
    normalize_column_name
)


CORE_PATH = os.path.join("data", "raw", "core")
SUPPORTING_PATH = os.path.join("data", "raw", "supporting")


FILES = {
    "analysis": os.path.join(CORE_PATH, "analysis.xlsx"),
    "balancesheet": os.path.join(CORE_PATH, "balancesheet.xlsx"),
    "cashflow": os.path.join(CORE_PATH, "cashflow.xlsx"),
    "companies": os.path.join(CORE_PATH, "companies.xlsx"),
    "documents": os.path.join(CORE_PATH, "documents.xlsx"),
    "profitandloss": os.path.join(CORE_PATH, "profitandloss.xlsx"),
    "prosandcons": os.path.join(CORE_PATH, "prosandcons.xlsx"),

    "financial_ratios": os.path.join(
        SUPPORTING_PATH, "financial_ratios.xlsx"
    ),
    "market_cap": os.path.join(
        SUPPORTING_PATH, "market_cap.xlsx"
    ),
    "peer_groups": os.path.join(
        SUPPORTING_PATH, "peer_groups.xlsx"
    ),
    "sectors": os.path.join(
        SUPPORTING_PATH, "sectors.xlsx"
    ),
    "stock_prices": os.path.join(
        SUPPORTING_PATH, "stock_prices.xlsx"
    ),
}


def clean_dataframe(df):
    """
    Clean column names and string values.
    """

    df = df.copy()

    df.columns = [
        normalize_column_name(column)
        for column in df.columns
    ]

    for column in df.columns:

        if df[column].dtype == "object":

            df[column] = df[column].apply(
                lambda value:
                value.strip()
                if isinstance(value, str)
                else value
            )

    return df


def normalize_common_columns(df):
    """
    Normalize common identifier and year columns.
    """

    df = df.copy()

    if "company_id" in df.columns:
        df["company_id"] = df["company_id"].apply(
            normalize_ticker
        )

    if "year" in df.columns:
        df["year"] = df["year"].apply(
            normalize_year
        )

    if "date" in df.columns:
        df["date"] = pd.to_datetime(
            df["date"],
            errors="coerce"
        )

    return df


def load_excel_file(path):
    """
    Load one of the supplied Excel files.

    header=1 is important because the first row of the
    source files contains a descriptive title.
    """

    if not os.path.exists(path):
        raise FileNotFoundError(
            "File not found: {}".format(path)
        )

    if path.startswith(CORE_PATH):
        header_row = 1
    else:
        header_row = 0

    df = pd.read_excel(
        path,
        header=header_row
    )

    df = clean_dataframe(df)

    df = normalize_common_columns(df)

    return df


def load_all_files():
    """
    Load all 12 source Excel files.
    """

    datasets = {}

    for name, path in FILES.items():

        print("\nLoading:", name)
        print("File:", path)

        df = load_excel_file(path)

        datasets[name] = df

        print("Rows:", len(df))
        print("Columns:", len(df.columns))
        print("Column names:")
        print(list(df.columns))

    return datasets


def print_summary(datasets):
    """
    Print a simple summary of every loaded dataset.
    """

    print("\n" + "=" * 70)
    print("NIFTY 100 DATA FOUNDATION - LOAD SUMMARY")
    print("=" * 70)

    for name, df in datasets.items():

        print(
            "{:<20} rows={:<6} columns={}".format(
                name,
                len(df),
                len(df.columns)
            )
        )

    print("=" * 70)


def main():

    print("Starting Nifty 100 Excel loader...")

    datasets = load_all_files()

    print_summary(datasets)

    print("\nExcel loading completed successfully.")


if __name__ == "__main__":
    main()