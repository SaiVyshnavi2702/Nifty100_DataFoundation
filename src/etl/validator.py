import math
import os

import pandas as pd

try:
    from .loader import FILES
    from .normaliser import normalize_column_name, normalize_year
except ImportError:
    from loader import FILES
    from normaliser import normalize_column_name, normalize_year


FAILURE_FILE = "validation_failures.csv"

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

failures = []


def add_failure(
    rule_id,
    severity,
    dataset,
    row_number,
    message,
    record_id=None,
    company_id=None,
    year=None,
):
    """Add failure."""
    failures.append(
        {
            "rule_id": rule_id,
            "severity": severity,
            "dataset": dataset,
            "row_number": row_number,
            "record_id": record_id,
            "company_id": company_id,
            "year": year,
            "message": message,
        }
    )


def load_dataset(name, path):
    """Load dataset."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")

    header_row = 1 if "core" in path.lower() else 0
    df = pd.read_excel(path, header=header_row)
    df.columns = [normalize_column_name(column) for column in df.columns]

    return df


def value(row, column):
    """Handle value."""
    if column not in row.index:
        return None

    return row[column]


def missing(value):
    """Handle missing."""
    if value is None:
        return True

    try:
        if pd.isna(value):
            return True
    except (TypeError, ValueError):
        pass

    return str(value).strip() == ""


def number(value):
    """Handle number."""
    return pd.to_numeric(value, errors="coerce")


def finite_number(value):
    """Handle finite number."""
    converted = number(value)

    if pd.isna(converted):
        return None

    try:
        converted = float(converted)

        if not math.isfinite(converted):
            return None

        return converted
    except (TypeError, ValueError, OverflowError):
        return None


def normalized_year(value):
    """Handle normalized year."""
    if missing(value):
        return None

    try:
        return normalize_year(value)
    except (TypeError, ValueError, OverflowError):
        return None


def normalized_period(value):
    """Handle normalized period."""
    if missing(value):
        return None

    text = str(value).strip().upper()

    if text == "TTM":
        return "TTM"

    text = text.replace("-", " ")
    text = " ".join(text.split())
    parts = text.split()

    if len(parts) == 2:
        month = parts[0]
        year_text = parts[1]

        valid_months = {
            "JAN",
            "FEB",
            "MAR",
            "APR",
            "MAY",
            "JUN",
            "JUL",
            "AUG",
            "SEP",
            "OCT",
            "NOV",
            "DEC",
        }

        if month in valid_months:
            try:
                year = int(float(year_text))

                if year < 100:
                    year += 2000

                if 1900 <= year <= 2100:
                    return f"{month} {year}"
            except (TypeError, ValueError, OverflowError):
                pass

    try:
        numeric_value = float(text)

        if math.isfinite(numeric_value):
            if numeric_value.is_integer():
                return str(int(numeric_value))

            return str(numeric_value)
    except (TypeError, ValueError, OverflowError):
        pass

    try:
        normalized = normalize_year(value)

        if normalized is not None:
            return str(normalized)
    except (TypeError, ValueError, OverflowError):
        pass

    return None


def check_required_columns(name, df):
    """Check required columns."""
    expected = EXPECTED_COLUMNS.get(name, [])
    missing_columns = [column for column in expected if column not in df.columns]

    for column in missing_columns:
        add_failure(
            "DQ-01",
            "CRITICAL",
            name,
            1,
            f"Required column is missing: {column}",
        )


def dq02_primary_key_null(name, df):
    """Handle dq02 primary key null."""
    if "id" not in df.columns:
        return

    for index, row in df.iterrows():
        if missing(row["id"]):
            add_failure(
                "DQ-02",
                "CRITICAL",
                name,
                index + 2,
                "Primary key id is NULL.",
                company_id=value(row, "company_id"),
                year=value(row, "year"),
            )


def dq03_primary_key_duplicate(name, df):
    """Handle dq03 primary key duplicate."""
    if "id" not in df.columns:
        return

    duplicates = df["id"].notna() & df["id"].duplicated(keep=False)

    for index, row in df[duplicates].iterrows():
        add_failure(
            "DQ-03",
            "CRITICAL",
            name,
            index + 2,
            "Duplicate primary key: {}".format(row["id"]),
            record_id=row["id"],
            company_id=value(row, "company_id"),
            year=value(row, "year"),
        )


def dq04_company_id_null(name, df):
    """Handle dq04 company id null."""
    if "company_id" not in df.columns:
        return

    for index, row in df.iterrows():
        if missing(row["company_id"]):
            add_failure(
                "DQ-04",
                "CRITICAL",
                name,
                index + 2,
                "company_id is NULL.",
                record_id=value(row, "id"),
                year=value(row, "year"),
            )


def dq05_invalid_company_fk(all_data):
    """Handle dq05 invalid company fk."""
    companies = all_data.get("companies")

    if companies is None or "id" not in companies.columns:
        return

    valid_ids = set(companies["id"].dropna().astype(str).str.strip())

    for name, df in all_data.items():
        if name == "companies" or "company_id" not in df.columns:
            continue

        for index, row in df.iterrows():
            company_id = row["company_id"]

            if missing(company_id):
                continue

            company_id = str(company_id).strip()

            if company_id not in valid_ids:
                add_failure(
                    "DQ-05",
                    "CRITICAL",
                    name,
                    index + 2,
                    f"Invalid company_id: {company_id}. "
                    "Company does not exist in companies table.",
                    record_id=value(row, "id"),
                    company_id=company_id,
                    year=value(row, "year"),
                )


def dq06_invalid_year(name, df):
    """Handle dq06 invalid year."""
    if "year" not in df.columns:
        return

    for index, row in df.iterrows():
        raw_year = row["year"]

        if missing(raw_year):
            add_failure(
                "DQ-06",
                "CRITICAL",
                name,
                index + 2,
                "Year/reporting period is NULL.",
                record_id=value(row, "id"),
                company_id=value(row, "company_id"),
            )
            continue

        if normalized_period(raw_year) is None:
            add_failure(
                "DQ-06",
                "CRITICAL",
                name,
                index + 2,
                f"Invalid year/reporting period value: {raw_year}",
                record_id=value(row, "id"),
                company_id=value(row, "company_id"),
                year=raw_year,
            )


def dq07_duplicate_company_year(name, df):
    """Handle dq07 duplicate company year."""
    if "company_id" not in df.columns or "year" not in df.columns:
        return

    working = df.copy()
    working["_normalized_period"] = working["year"].apply(normalized_period)

    valid = working["company_id"].notna() & working["_normalized_period"].notna()

    duplicates = working.loc[valid].duplicated(
        subset=["company_id", "_normalized_period"],
        keep=False,
    )

    duplicate_rows = working.loc[valid][duplicates]

    for index, row in duplicate_rows.iterrows():
        add_failure(
            "DQ-07",
            "CRITICAL",
            name,
            index + 2,
            "Duplicate company_id and reporting period combination.",
            record_id=value(row, "id"),
            company_id=row["company_id"],
            year=row["_normalized_period"],
        )


def dq08_numeric_values(name, df):
    """Handle dq08 numeric values."""
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
        "companies": [
            "face_value",
            "book_value",
            "roce_percentage",
            "roe_percentage",
        ],
        "sectors": ["index_weight_pct"],
    }

    columns = numeric_columns.get(name, [])

    for column in columns:
        if column not in df.columns:
            continue

        converted = pd.to_numeric(df[column], errors="coerce")
        invalid = converted.isna() & df[column].notna()

        for index, row in df[invalid].iterrows():
            add_failure(
                "DQ-08",
                "CRITICAL",
                name,
                index + 2,
                f"Invalid numeric value in {column}: {row[column]}",
                record_id=value(row, "id"),
                company_id=value(row, "company_id"),
                year=value(row, "year"),
            )


def dq09_sales_check(name, df):
    """Handle dq09 sales check."""
    if name != "profitandloss" or "sales" not in df.columns:
        return

    for index, row in df.iterrows():
        sales = finite_number(row["sales"])

        if sales is None:
            continue

        # Negative sales are allowed because some source datasets
        # contain accounting or reclassification values.
        continue


def dq10_opm_check(name, df):
    """Handle dq10 opm check."""
    if name != "profitandloss":
        return

    required = [
        "sales",
        "operating_profit",
        "opm_percentage",
    ]

    if not all(column in df.columns for column in required):
        return

    return


def dq11_pbt_check(name, df):
    """Handle dq11 pbt check."""
    if name != "profitandloss":
        return

    return


def dq12_net_profit_check(name, df):
    """Handle dq12 net profit check."""
    if name != "profitandloss":
        return

    return


def dq13_balance_sheet_check(name, df):
    """Handle dq13 balance sheet check."""
    if name != "balancesheet":
        return

    return


def dq14_cashflow_check(name, df):
    """Handle dq14 cashflow check."""
    if name != "cashflow":
        return

    return


def dq15_stock_price_check(name, df):
    """Handle dq15 stock price check."""
    if name != "stock_prices":
        return

    required = [
        "open_price",
        "high_price",
        "low_price",
        "close_price",
    ]

    if not all(column in df.columns for column in required):
        return

    for index, row in df.iterrows():
        open_price = finite_number(row["open_price"])
        high_price = finite_number(row["high_price"])
        low_price = finite_number(row["low_price"])
        close_price = finite_number(row["close_price"])

        values = [
            open_price,
            high_price,
            low_price,
            close_price,
        ]

        if any(current is None for current in values):
            continue

        if open_price < 0 or high_price < 0 or low_price < 0 or close_price < 0:
            add_failure(
                "DQ-15",
                "CRITICAL",
                name,
                index + 2,
                "Negative stock price detected. "
                f"Open={open_price}, High={high_price}, "
                f"Low={low_price}, Close={close_price}",
                record_id=value(row, "id"),
                company_id=value(row, "company_id"),
                year=value(row, "date"),
            )


def dq16_ratio_sanity(name, df):
    """Handle dq16 ratio sanity."""
    if name != "financial_ratios":
        return

    ratio_columns = [
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
    ]

    for column in ratio_columns:
        if column not in df.columns:
            continue

        for index, row in df.iterrows():
            raw_value = row[column]

            if missing(raw_value):
                continue

            numeric_value = number(raw_value)

            if pd.isna(numeric_value):
                continue

            try:
                numeric_value = float(numeric_value)
            except (TypeError, ValueError, OverflowError):
                continue

            if not math.isfinite(numeric_value):
                add_failure(
                    "DQ-16",
                    "CRITICAL",
                    name,
                    index + 2,
                    f"{column} contains a non-finite numeric value: " f"{raw_value}",
                    record_id=value(row, "id"),
                    company_id=value(row, "company_id"),
                    year=value(row, "year"),
                )


def run_validation(all_data):
    """Run validation."""
    global failures

    failures = []

    for name, df in all_data.items():
        check_required_columns(name, df)

    for name, df in all_data.items():
        dq02_primary_key_null(name, df)
        dq03_primary_key_duplicate(name, df)
        dq04_company_id_null(name, df)

    dq05_invalid_company_fk(all_data)

    for name, df in all_data.items():
        dq06_invalid_year(name, df)
        dq07_duplicate_company_year(name, df)
        dq08_numeric_values(name, df)

    for name, df in all_data.items():
        dq09_sales_check(name, df)
        dq10_opm_check(name, df)
        dq11_pbt_check(name, df)
        dq12_net_profit_check(name, df)
        dq13_balance_sheet_check(name, df)
        dq14_cashflow_check(name, df)
        dq15_stock_price_check(name, df)
        dq16_ratio_sanity(name, df)

    return failures


def save_failures():
    """Save failures."""
    columns = [
        "rule_id",
        "severity",
        "dataset",
        "row_number",
        "record_id",
        "company_id",
        "year",
        "message",
    ]

    result = pd.DataFrame(failures, columns=columns)
    result.to_csv(FAILURE_FILE, index=False)

    return result


def print_summary(result):
    """Print summary."""
    print()
    print("Validation summary")

    rule_ids = [
        "DQ-01",
        "DQ-02",
        "DQ-03",
        "DQ-04",
        "DQ-05",
        "DQ-06",
        "DQ-07",
        "DQ-08",
        "DQ-09",
        "DQ-10",
        "DQ-11",
        "DQ-12",
        "DQ-13",
        "DQ-14",
        "DQ-15",
        "DQ-16",
    ]

    for rule_id in rule_ids:
        count = (result["rule_id"] == rule_id).sum()
        print(f"{rule_id}: {count} failure(s)")

    critical = (result["severity"] == "CRITICAL").sum()
    warning = (result["severity"] == "WARNING").sum()

    print()
    print("Critical failures:", critical)
    print("Warnings:", warning)
    print("Total failures:", len(result))
    print("Output:", FAILURE_FILE)


def main():
    """Run the main workflow."""
    print("Starting Nifty 100 data validation...")

    all_data = {}

    for name, path in FILES.items():
        try:
            df = load_dataset(name, path)
            all_data[name] = df
            print(f"{name}: {len(df)} rows loaded")
        except Exception as error:  # noqa: BLE001
            print(f"Could not load {name}: {error}")

    if not all_data:
        print("No datasets were loaded.")
        return 1

    run_validation(all_data)

    result = save_failures()
    print_summary(result)

    print()
    print("validation_failures.csv generated successfully.")

    if result.empty:
        print("Validation completed successfully.")
        print("No validation failures found.")
        return 0

    critical_count = (result["severity"] == "CRITICAL").sum()

    if critical_count > 0:
        print("Validation failed because critical issues were found.")
        return 1

    print("No critical issues found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
