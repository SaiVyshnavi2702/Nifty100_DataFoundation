import os
import sqlite3
import pandas as pd


try:
    from .normaliser import (
        normalize_year,
        normalize_period,
        normalize_ticker,
        normalize_column_name,
    )
except ImportError:
    from normaliser import (
        normalize_year,
        normalize_period,
        normalize_ticker,
        normalize_column_name,
    )



CORE_PATH = os.path.join("data", "raw", "core")
SUPPORTING_PATH = os.path.join("data", "raw", "supporting")

DB_PATH = os.path.join("data", "nifty100.db")
SCHEMA_PATH = os.path.join("src", "db", "schema.sql")
AUDIT_PATH = os.path.join("data", "load_audit.csv")


FILES = {
    "analysis": os.path.join(
        CORE_PATH,
        "analysis.xlsx"
    ),

    "balancesheet": os.path.join(
        CORE_PATH,
        "balancesheet.xlsx"
    ),

    "cashflow": os.path.join(
        CORE_PATH,
        "cashflow.xlsx"
    ),

    "companies": os.path.join(
        CORE_PATH,
        "companies.xlsx"
    ),

    "documents": os.path.join(
        CORE_PATH,
        "documents.xlsx"
    ),

    "profitandloss": os.path.join(
        CORE_PATH,
        "profitandloss.xlsx"
    ),

    "prosandcons": os.path.join(
        CORE_PATH,
        "prosandcons.xlsx"
    ),

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
    "sectors",
    "peer_groups",
    "analysis",
    "balancesheet",
    "profitandloss",
    "cashflow",
    "financial_ratios",
    "market_cap",
    "stock_prices",
    "documents",
    "prosandcons"
]


UNIQUE_KEY_TABLES = {
    "balancesheet": [
        "company_id",
        "period"
    ],

    "profitandloss": [
        "company_id",
        "period"
    ],

    "cashflow": [
        "company_id",
        "period"
    ],

    "financial_ratios": [
        "company_id",
        "period"
    ],

    "market_cap": [
        "company_id",
        "period"
    ],

    "stock_prices": [
        "company_id",
        "date"
    ]
}


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

        df["period"] = df["year"].apply(
            normalize_period
        )

        df["year"] = df["year"].apply(
            normalize_year
        )

    if "date" in df.columns:

        parsed_dates = pd.to_datetime(
            df["date"],
            errors="coerce"
        )

        df["date"] = parsed_dates.dt.strftime(
            "%Y-%m-%d"
        )

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
            "File not found: {}".format(
                path
            )
        )

    absolute_path = os.path.abspath(path)
    absolute_core_path = os.path.abspath(CORE_PATH)

    if absolute_path.startswith(
        absolute_core_path + os.sep
    ):

        header_row = 1

    else:

        header_row = 0

    print(
        "Reading Excel with header row:",
        header_row
    )

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

        print(
            "File:",
            path
        )

        df = load_excel_file(
            path
        )

        if name == "companies":

            df = normalize_company_table(
                df
            )

        datasets[name] = df

        print(
            "Rows:",
            len(df)
        )

        print(
            "Columns:",
            len(df.columns)
        )

        print(
            "Column names:"
        )

        print(
            list(df.columns)
        )

    return datasets


def initialize_database(connection):

    if not os.path.exists(
        SCHEMA_PATH
    ):

        raise FileNotFoundError(
            "Schema file not found: {}".format(
                SCHEMA_PATH
            )
        )

    with open(
        SCHEMA_PATH,
        "r",
        encoding="utf-8"
    ) as file:

        schema = file.read()

    connection.executescript(
        schema
    )


def validate_dataset_columns(
    table_name,
    df,
    connection
):

    database_columns = connection.execute(
        "PRAGMA table_info({})".format(
            table_name
        )
    ).fetchall()

    if not database_columns:

        raise RuntimeError(
            "Database table does not exist: {}".format(
                table_name
            )
        )

    database_column_names = {
        row[1]
        for row in database_columns
    }

    dataframe_columns = set(
        df.columns
    )

    missing_in_database = (
        dataframe_columns
        - database_column_names
    )

    if missing_in_database:

        raise RuntimeError(
            "Table '{}' is missing these columns: {}".format(
                table_name,
                sorted(
                    missing_in_database
                )
            )
        )


def check_duplicate_keys(
    table_name,
    df
):

    if table_name not in UNIQUE_KEY_TABLES:

        return

    keys = UNIQUE_KEY_TABLES[
        table_name
    ]

    missing_keys = [
        key
        for key in keys
        if key not in df.columns
    ]

    if missing_keys:

        raise RuntimeError(
            "Table '{}' is missing key columns: {}".format(
                table_name,
                missing_keys
            )
        )

    duplicate_count = df.duplicated(
        subset=keys,
        keep=False
    ).sum()

    if duplicate_count == 0:

        print(
            "Duplicate key check: PASSED"
        )

        return

    print(
        "\nDUPLICATE DATA DETECTED"
    )

    print(
        "Table:",
        table_name
    )

    print(
        "Keys:",
        keys
    )

    print(
        "Duplicate rows:",
        duplicate_count
    )

    duplicate_rows = df[
        df.duplicated(
            subset=keys,
            keep=False
        )
    ]

    display_columns = list(
        keys
    )

    if "year" in duplicate_rows.columns:

        display_columns.append(
            "year"
        )

    if "period" in duplicate_rows.columns:

        display_columns.append(
            "period"
        )

    print(
        duplicate_rows[
            list(
                dict.fromkeys(
                    display_columns
                )
            )
        ]
        .sort_values(keys)
        .to_string(
            index=False
        )
    )

    raise RuntimeError(
        "Duplicate logical keys found in {}".format(
            table_name
        )
    )


def load_datasets_to_database(
    connection,
    datasets
):

    audit_records = []

    for table_name in LOAD_ORDER:

        print(
            "\nPreparing table:",
            table_name
        )

        df = datasets[
            table_name
        ].copy()

        source_file = FILES[
            table_name
        ]

        try:

            validate_dataset_columns(
                table_name,
                df,
                connection
            )

            check_duplicate_keys(
                table_name,
                df
            )

            rows_to_load = len(df)

            print(
                "Loading {} rows into '{}'...".format(
                    rows_to_load,
                    table_name
                )
            )

            df.to_sql(
                table_name,
                connection,
                if_exists="append",
                index=False
            )

            database_count = connection.execute(
                "SELECT COUNT(*) FROM {}".format(
                    table_name
                )
            ).fetchone()[0]

            print(
                "Rows currently in database:",
                database_count
            )

            audit_records.append(
                {
                    "table_name": table_name,
                    "source_file": source_file,
                    "source_rows": rows_to_load,
                    "database_rows": database_count,
                    "status": "SUCCESS"
                }
            )

        except Exception as error:

            audit_records.append(
                {
                    "table_name": table_name,
                    "source_file": source_file,
                    "source_rows": len(df),
                    "database_rows": 0,
                    "status": "FAILED: {}".format(
                        error
                    )
                }
            )

            raise

    return audit_records


def write_load_audit(
    audit_records
):

    audit_directory = os.path.dirname(
        AUDIT_PATH
    )

    if audit_directory:

        os.makedirs(
            audit_directory,
            exist_ok=True
        )

    audit_df = pd.DataFrame(
        audit_records
    )

    audit_df.to_csv(
        AUDIT_PATH,
        index=False
    )

    print(
        "\nLoad audit written to:",
        AUDIT_PATH
    )


def verify_tables(connection):

    expected_tables = {
        "companies",
        "sectors",
        "peer_groups",
        "analysis",
        "balancesheet",
        "profitandloss",
        "cashflow",
        "financial_ratios",
        "market_cap",
        "stock_prices",
        "documents",
        "prosandcons"
    }

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

    missing_tables = (
        expected_tables
        - actual_tables
    )

    if missing_tables:

        raise RuntimeError(
            "Missing tables: {}".format(
                sorted(
                    missing_tables
                )
            )
        )

    print(
        "\nSchema verification: PASSED"
    )

    print(
        "Tables created:",
        len(actual_tables)
    )


def verify_foreign_keys(connection):

    value = connection.execute(
        "PRAGMA foreign_keys"
    ).fetchone()[0]

    if value != 1:

        raise RuntimeError(
            "SQLite foreign_keys pragma is not enabled"
        )

    print(
        "Foreign keys: ENABLED"
    )

    violations = connection.execute(
        "PRAGMA foreign_key_check"
    ).fetchall()

    if violations:

        print(
            "Foreign key check: FAILED"
        )

        for violation in violations:

            print(
                violation
            )

        raise RuntimeError(
            "Foreign key violations detected."
        )

    print(
        "Foreign key check: PASSED"
    )


def verify_database(connection):

    print("\n")
    print(
        "=" * 70
    )

    print(
        "DATABASE VERIFICATION"
    )

    print(
        "=" * 70
    )

    verify_tables(
        connection
    )

    verify_foreign_keys(
        connection
    )

    print(
        "\nTable row counts:"
    )

    for table_name in [
        "companies",
        "sectors",
        "peer_groups",
        "analysis",
        "balancesheet",
        "profitandloss",
        "cashflow",
        "financial_ratios",
        "market_cap",
        "stock_prices",
        "documents",
        "prosandcons"
    ]:

        count = connection.execute(
            "SELECT COUNT(*) FROM {}".format(
                table_name
            )
        ).fetchone()[0]

        print(
            "{:<20} rows={}".format(
                table_name,
                count
            )
        )

    print(
        "=" * 70
    )


def main():

    print(
        "Starting Nifty 100 Excel loader..."
    )

    db_directory = os.path.dirname(
        DB_PATH
    )

    if db_directory:

        os.makedirs(
            db_directory,
            exist_ok=True
        )

    datasets = load_all_files()

    print("\n")
    print(
        "=" * 70
    )

    print(
        "SOURCE DATA SUMMARY"
    )

    print(
        "=" * 70
    )

    for name, df in datasets.items():

        print(
            "{:<20} rows={:<6} columns={}".format(
                name,
                len(df),
                len(df.columns)
            )
        )

    print(
        "=" * 70
    )

    print(
        "\nOpening SQLite database:",
        DB_PATH
    )

    connection = sqlite3.connect(
        DB_PATH
    )

    try:

        connection.execute(
            "PRAGMA foreign_keys = ON"
        )

        initialize_database(
            connection
        )

        verify_tables(
            connection
        )

        audit_records = (
            load_datasets_to_database(
                connection,
                datasets
            )
        )

        connection.commit()

        verify_database(
            connection
        )

        write_load_audit(
            audit_records
        )

        print(
            "\nSQLite database loading completed successfully."
        )

        print(
            "Day 05 full data load completed."
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
