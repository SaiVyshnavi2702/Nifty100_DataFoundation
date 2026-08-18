import os

import pandas as pd

from loader import FILES
from normaliser import normalize_year, normalize_column_name


EXPECTED_COLUMNS = {
    "analysis": [
        "id",
        "company_id",
        "compounded_sales_growth",
        "compounded_profit_growth",
        "stock_price_cagr",
        "roe",
    ],

    "balancesheet": [
        "id",
        "company_id",
        "year",
        "equity_capital",
        "reserves",
        "borrowings",
        "other_liabilities",
        "total_liabilities",
        "fixed_assets",
        "cwip",
        "investments",
        "other_asset",
        "total_assets",
    ],

    "cashflow": [
        "id",
        "company_id",
        "year",
        "operating_activity",
        "investing_activity",
        "financing_activity",
        "net_cash_flow",
    ],

    "companies": [
        "id",
        "company_logo",
        "company_name",
        "chart_link",
        "about_company",
        "website",
        "nse_profile",
        "bse_profile",
        "face_value",
        "book_value",
        "roce_percentage",
        "roe_percentage",
    ],

    "documents": [
        "id",
        "company_id",
        "year",
        "annual_report",
    ],

    "profitandloss": [
        "id",
        "company_id",
        "year",
        "sales",
        "expenses",
        "operating_profit",
        "opm_percentage",
        "other_income",
        "interest",
        "depreciation",
        "profit_before_tax",
        "tax_percentage",
        "net_profit",
        "eps",
        "dividend_payout",
    ],

    "prosandcons": [
        "id",
        "company_id",
        "pros",
        "cons",
    ],

    "financial_ratios": [
        "id",
        "company_id",
        "year",
        "net_profit_margin_pct",
        "operating_profit_margin_pct",
        "return_on_equity_pct",
        "debt_to_equity",
        "interest_coverage",
        "asset_turnover",
        "free_cash_flow_cr",
        "capex_cr",
        "earnings_per_share",
        "book_value_per_share",
        "dividend_payout_ratio_pct",
        "total_debt_cr",
        "cash_from_operations_cr",
    ],

    "market_cap": [
        "id",
        "company_id",
        "year",
        "market_cap_crore",
        "enterprise_value_crore",
        "pe_ratio",
        "pb_ratio",
        "ev_ebitda",
        "dividend_yield_pct",
    ],

    "peer_groups": [
        "id",
        "peer_group_name",
        "company_id",
        "is_benchmark",
    ],

    "sectors": [
        "id",
        "company_id",
        "broad_sector",
        "sub_sector",
        "index_weight_pct",
        "market_cap_category",
    ],

    "stock_prices": [
        "id",
        "company_id",
        "date",
        "open_price",
        "high_price",
        "low_price",
        "close_price",
        "volume",
        "adjusted_close",
    ],
}


def load_dataset(name, path):
    """
    Load one Excel dataset using the same header structure
    as the project loader.
    """

    if not os.path.exists(path):
        raise FileNotFoundError(
            "File not found: {}".format(path)
        )

    if "core" in path:
        header_row = 1
    else:
        header_row = 0

    df = pd.read_excel(
        path,
        header=header_row
    )

    df.columns = [
        normalize_column_name(column)
        for column in df.columns
    ]

    return df

def check_required_columns(name, df):
    """
    Check whether the expected columns are present.
    """

    expected = EXPECTED_COLUMNS[name]
    actual = list(df.columns)

    missing = [
        column
        for column in expected
        if column not in actual
    ]

    if missing:
        return False, "Missing columns: {}".format(
            ", ".join(missing)
        )

    return True, "All expected columns are present."


def check_not_empty(df):
    """
    Check that the dataset contains records.
    """

    if df.empty:
        return False, "Dataset contains no records."

    return True, "Dataset contains {} records.".format(
        len(df)
    )


def check_id_column(df):
    """
    Check that the ID column exists and does not contain
    missing values.
    """

    if "id" not in df.columns:
        return False, "ID column is missing."

    missing_count = df["id"].isna().sum()

    if missing_count > 0:
        return False, "{} missing ID values found.".format(
            missing_count
        )

    return True, "ID values are present."


def check_company_id(df):
    """
    Check company identifiers where the dataset uses them.
    """

    if "company_id" not in df.columns:
        return True, "Company ID check not required."

    missing_count = df["company_id"].isna().sum()

    if missing_count > 0:
        return False, "{} missing company IDs found.".format(
            missing_count
        )

    return True, "Company IDs are present."


def check_year(df):
    """
    Check financial period values after applying the
    project's standard year normalisation.

    TTM is accepted because some financial datasets
    contain trailing-twelve-month records.
    """

    if "year" not in df.columns:
        return True, "Year check not required."

    values = df["year"].dropna()

    if values.empty:
        return False, "Year column contains no usable values."

    invalid_count = 0

    for value in values:

        normalized = normalize_year(value)

        if normalized is None:
            invalid_count += 1

    if invalid_count > 0:
        return False, "{} invalid year values found.".format(
            invalid_count
        )

    return True, "Year values look valid."

def check_date(df):
    """
    Check date values for datasets that contain dates.
    """

    if "date" not in df.columns:
        return True, "Date check not required."

    converted = pd.to_datetime(
        df["date"],
        errors="coerce"
    )

    invalid_count = (
        converted.isna() & df["date"].notna()
    ).sum()

    if invalid_count > 0:
        return False, "{} invalid date values found.".format(
            invalid_count
        )

    return True, "Date values look valid."


def check_numeric_columns(name, df):
    """
    Check the main numeric fields in financial datasets.

    Text fields such as company names and descriptions are
    intentionally excluded from this check.
    """

    numeric_columns = {
        "balancesheet": [
            "equity_capital",
            "reserves",
            "borrowings",
            "other_liabilities",
            "total_liabilities",
            "fixed_assets",
            "cwip",
            "investments",
            "other_asset",
            "total_assets",
        ],

        "cashflow": [
            "operating_activity",
            "investing_activity",
            "financing_activity",
            "net_cash_flow",
        ],

        "profitandloss": [
            "sales",
            "expenses",
            "operating_profit",
            "opm_percentage",
            "other_income",
            "interest",
            "depreciation",
            "profit_before_tax",
            "tax_percentage",
            "net_profit",
            "eps",
            "dividend_payout",
        ],

        "financial_ratios": [
            "net_profit_margin_pct",
            "operating_profit_margin_pct",
            "return_on_equity_pct",
            "debt_to_equity",
            "interest_coverage",
            "asset_turnover",
            "free_cash_flow_cr",
            "capex_cr",
            "earnings_per_share",
            "book_value_per_share",
            "dividend_payout_ratio_pct",
            "total_debt_cr",
            "cash_from_operations_cr",
        ],

        "market_cap": [
            "market_cap_crore",
            "enterprise_value_crore",
            "pe_ratio",
            "pb_ratio",
            "ev_ebitda",
            "dividend_yield_pct",
        ],

        "stock_prices": [
            "open_price",
            "high_price",
            "low_price",
            "close_price",
            "volume",
            "adjusted_close",
        ],
    }

    columns = numeric_columns.get(name, [])

    if not columns:
        return True, "Numeric field check not required."

    invalid_columns = []

    for column in columns:

        if column not in df.columns:
            continue

        converted = pd.to_numeric(
            df[column],
            errors="coerce"
        )

        invalid_count = (
            converted.isna() & df[column].notna()
        ).sum()

        if invalid_count > 0:
            invalid_columns.append(
                "{} ({} invalid values)".format(
                    column,
                    invalid_count
                )
            )

    if invalid_columns:
        return False, "Invalid numeric values: {}".format(
            ", ".join(invalid_columns)
        )

    return True, "Numeric fields look valid."


def validate_dataset(name, path):
    """
    Run all validation checks for one dataset.
    """

    print("\n" + "-" * 70)
    print("Validating: {}".format(name))
    print("File: {}".format(path))
    print("-" * 70)

    try:
        df = load_dataset(name, path)
    except Exception as error:
        print("[FAIL] Could not load dataset: {}".format(error))
        return False

    checks = [
        ("Required columns", check_required_columns(name, df)),
        ("Dataset not empty", check_not_empty(df)),
        ("ID values", check_id_column(df)),
        ("Company IDs", check_company_id(df)),
        ("Year values", check_year(df)),
        ("Date values", check_date(df)),
        ("Numeric fields", check_numeric_columns(name, df)),
    ]

    dataset_passed = True

    for check_name, result in checks:

        passed, message = result

        if passed:
            print("[PASS] {} - {}".format(
                check_name,
                message
            ))
        else:
            print("[FAIL] {} - {}".format(
                check_name,
                message
            ))
            dataset_passed = False

    return dataset_passed


def main():
    """
    Validate all Nifty 100 datasets and print a summary.
    """

    print("Starting Nifty 100 data validation...")

    results = {}

    for name, path in FILES.items():
        results[name] = validate_dataset(name, path)

    print("\n" + "=" * 70)
    print("NIFTY 100 DATA VALIDATION SUMMARY")
    print("=" * 70)

    passed_count = 0
    failed_count = 0

    for name, passed in results.items():

        if passed:
            print("{:<20} PASS".format(name))
            passed_count += 1
        else:
            print("{:<20} FAIL".format(name))
            failed_count += 1

    print("=" * 70)
    print(
        "Datasets checked : {}".format(
            len(results)
        )
    )
    print(
        "Datasets passed  : {}".format(
            passed_count
        )
    )
    print(
        "Datasets failed  : {}".format(
            failed_count
        )
    )
    print("=" * 70)

    if failed_count == 0:
        print("\nValidation completed successfully.")
        return 0

    print("\nValidation completed with issues.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())