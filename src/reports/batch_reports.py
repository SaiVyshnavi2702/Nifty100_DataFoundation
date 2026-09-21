"""
Day 34 - Batch Report Generation

Generates company tearsheets for all companies in the database.

Companies with fewer than 3 years of Profit & Loss data
are skipped and written to output/skipped_tearsheets.csv.
"""

import sqlite3
from pathlib import Path

import pandas as pd

from src.reports.tearsheet import generate_tearsheet

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DB_PATH = PROJECT_ROOT / "data" / "nifty100.db"

OUTPUT_DIR = PROJECT_ROOT / "reports" / "tearsheets"

SKIPPED_FILE = PROJECT_ROOT / "output" / "skipped_tearsheets.csv"


def get_company_tickers():
    """Return all company tickers from the database."""

    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found: {DB_PATH}")

    with sqlite3.connect(DB_PATH) as connection:
        df = pd.read_sql_query(
            """
            SELECT id
            FROM companies
            ORDER BY id
            """,
            connection,
        )

    return df["id"].astype(str).str.strip().tolist()


def get_year_count(ticker):
    """Return the number of distinct valid financial years."""

    with sqlite3.connect(DB_PATH) as connection:
        result = connection.execute(
            """
            SELECT COUNT(DISTINCT year)
            FROM profitandloss
            WHERE company_id = ?
              AND year IS NOT NULL
              AND year != ?
            """,
            (ticker, "TTM"),
        ).fetchone()

    return int(result[0] or 0)


def generate_company_batch():
    """Generate tearsheets for all eligible companies."""

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    SKIPPED_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    tickers = get_company_tickers()

    generated = []
    skipped = []

    print(f"Total companies found: {len(tickers)}")

    print()

    for index, ticker in enumerate(
        tickers,
        start=1,
    ):

        print(f"[{index}/{len(tickers)}] Processing {ticker}...")

        year_count = get_year_count(ticker)

        if year_count < 3:

            skipped.append(
                {
                    "ticker": ticker,
                    "years_available": year_count,
                    "reason": "Fewer than 3 years of data",
                }
            )

            print(f"  SKIPPED - only {year_count} year(s) of data")

            continue

        try:

            output_file = generate_tearsheet(ticker)

            generated.append(
                {
                    "ticker": ticker,
                    "file": str(output_file),
                    "years_available": year_count,
                }
            )

            print(f"  CREATED - {output_file.name}")

        except Exception as error:  # noqa: BLE001

            print(f"  ERROR - {error}")

    skipped_df = pd.DataFrame(
        skipped,
        columns=[
            "ticker",
            "years_available",
            "reason",
        ],
    )

    skipped_df.to_csv(
        SKIPPED_FILE,
        index=False,
    )

    print()
    print("Batch generation completed.")
    print(f"Total companies: {len(tickers)}")
    print(f"Generated tearsheets: {len(generated)}")
    print(f"Skipped companies: {len(skipped)}")
    print(f"Skipped file: {SKIPPED_FILE}")


def main():
    """Run Day 34 company batch generation."""

    generate_company_batch()


if __name__ == "__main__":
    main()
