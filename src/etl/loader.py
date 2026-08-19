import os
import sqlite3
import pandas as pd

from normaliser import (
    normalize_year,
    normalize_ticker,
    normalize_column_name
)


CORE_PATH = os.path.join("data", "raw", "core")
SUPPORTING_PATH = os.path.join("data", "raw", "supporting")

DB_PATH = "data/nifty100.db"
SCHEMA_PATH = os.path.join("src", "db", "schema.sql")


FILES = {
    "analysis": os.path.join(CORE_PATH, "analysis.xlsx"),
    "balancesheet": os.path.join(CORE_PATH, "balancesheet.xlsx"),
    "cashflow": os.path.join(CORE_PATH, "cashflow.xlsx"),
    "companies": os.path.join(CORE_PATH, "companies.xlsx"),
    "profitandloss": os.path.join(CORE_PATH, "profitandloss.xlsx"),
    "financial_ratios": os.path.join(
        SUPPORTING_PATH,
        "financial_ratios.xlsx"
    ),
    "market_cap": os.path.join(
        SUPPORTING_PATH,
        "market_cap.xlsx"
    ),
    "peer_groups": os.path.join(
        SUPPORTING_PATH,
        "peer_groups.xlsx"
    ),
    "sectors": os.path.join(
        SUPPORTING_PATH,
        "sectors.xlsx"
    ),
    "stock_prices": os.path.join(
        SUPPORTING_PATH,
        "stock_prices.xlsx"
    )
}


LOAD_ORDER = [
    "companies",
    "analysis",
    "balancesheet",
    "cashflow",
    "profitandloss",
    "financial_ratios",
    "market_cap",
    "peer_groups",
    "sectors",
    "stock_prices"
]


def clean_dataframe(df):
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
        ).dt.strftime("%Y-%m-%d")

    return df


def normalize_company_table(df):
    df = df.copy()

    if "id" in df.columns:
        df["id"] = df["id"].apply(
            normalize_ticker
        )

    return df


def load_excel_file(path):
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
    datasets = {}

    for name, path in FILES.items():
        print("\nLoading:", name)
        print("File:", path)

        df = load_excel_file(path)

        if name == "companies":
            df = normalize_company_table(df)

        datasets[name] = df

        print("Rows:", len(df))
        print("Columns:", len(df.columns))
        print("Column names:")
        print(list(df.columns))

    return datasets


def initialize_database(connection):
    if not os.path.exists(SCHEMA_PATH):
        raise FileNotFoundError(
            "Schema file not found: {}".format(SCHEMA_PATH)
        )

    with open(
        SCHEMA_PATH,
        "r",
        encoding="utf-8"
    ) as file:
        schema = file.read()

    connection.executescript(schema)


def load_datasets_to_database(connection, datasets):
    unique_key_tables = {
        "balancesheet": ["company_id", "year"],
        "profitandloss": ["company_id", "year"],
        "cashflow": ["company_id", "year"],
        "financial_ratios": ["company_id", "year"],
        "market_cap": ["company_id", "year"],
        "stock_prices": ["company_id", "date"]
    }

    for table_name in LOAD_ORDER:
        df = datasets[table_name].copy()

        if table_name in unique_key_tables:
            keys = unique_key_tables[table_name]

            duplicate_mask = df.duplicated(
                subset=keys,
                keep="first"
            )

            duplicate_count = duplicate_mask.sum()

            if duplicate_count > 0:
                print("\nDUPLICATE DATA DETECTED")
                print("Table:", table_name)
                print("Keys:", keys)
                print("Duplicate rows:", duplicate_count)

                print(
                    df[
                        df.duplicated(
                            subset=keys,
                            keep=False
                        )
                    ][keys].sort_values(keys).to_string(
                        index=False
                    )
                )

                df = df.drop_duplicates(
                    subset=keys,
                    keep="first"
                )

                print(
                    "Rows after duplicate removal:",
                    len(df)
                )

        print(
            "\nLoading {} rows into table '{}'...".format(
                len(df),
                table_name
            )
        )

        df.to_sql(
            table_name,
            connection,
            if_exists="append",
            index=False
        )

        count = connection.execute(
            "SELECT COUNT(*) FROM {}".format(table_name)
        ).fetchone()[0]

        print(
            "Inserted rows: {}".format(count)
        )

def verify_tables(connection):
    expected_tables = [
        "companies",
        "sectors",
        "peer_groups",
        "analysis",
        "balancesheet",
        "profitandloss",
        "cashflow",
        "financial_ratios",
        "market_cap",
        "stock_prices"
    ]

    actual_tables = connection.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        AND name NOT LIKE 'sqlite_%'
        ORDER BY name
        """
    ).fetchall()

    actual_tables = {
        row[0]
        for row in actual_tables
    }

    expected_tables = set(expected_tables)

    missing_tables = expected_tables - actual_tables

    if missing_tables:
        raise RuntimeError(
            "Missing tables: {}".format(
                sorted(missing_tables)
            )
        )

    print("\nSchema verification: PASSED")
    print("Tables created: {}".format(len(actual_tables)))


def verify_foreign_keys(connection):
    value = connection.execute(
        "PRAGMA foreign_keys"
    ).fetchone()[0]

    if value != 1:
        raise RuntimeError(
            "SQLite foreign_keys pragma is not enabled"
        )

    print("Foreign keys: ENABLED")

    violations = connection.execute(
        "PRAGMA foreign_key_check"
    ).fetchall()

    if violations:
        print("Foreign key check: FAILED")

        for violation in violations:
            print(violation)

        raise RuntimeError(
            "Foreign key violations detected."
        )

    print("Foreign key check: PASSED")


def verify_database(connection):
    print("\n" + "=" * 70)
    print("DATABASE VERIFICATION")
    print("=" * 70)

    verify_tables(connection)
    verify_foreign_keys(connection)

    print("\nTable row counts:")

    for table_name in LOAD_ORDER:
        count = connection.execute(
            "SELECT COUNT(*) FROM {}".format(table_name)
        ).fetchone()[0]

        print(
            "{:<20} rows={}".format(
                table_name,
                count
            )
        )

    print("=" * 70)


def print_summary(datasets):
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

    db_directory = os.path.dirname(DB_PATH)

    if db_directory:
        os.makedirs(
            db_directory,
            exist_ok=True
        )

    datasets = load_all_files()

    print_summary(datasets)

    print("\nCreating SQLite database:", DB_PATH)

    connection = sqlite3.connect(DB_PATH)

    try:
        connection.execute(
            "PRAGMA foreign_keys = ON"
        )

        initialize_database(connection)

        verify_tables(connection)

        load_datasets_to_database(
            connection,
            datasets
        )

        verify_database(connection)

        connection.commit()

        print(
            "\nSQLite database loading completed successfully."
        )

    except Exception:
        connection.rollback()

        print(
            "\nDatabase loading failed."
        )

        raise

    finally:
        connection.close()


if __name__ == "__main__":
    main()  