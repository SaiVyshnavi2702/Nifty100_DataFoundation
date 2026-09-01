import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

from src.screener.engine import DB_PATH, load_data
from src.screener.presets import PRESETS


PROJECT_ROOT = Path(__file__).resolve().parent

MIN_RESULTS = 5
MAX_RESULTS = 50
EXPECTED_UNIVERSE = 92


# DATA LOADING


def load_latest_universe():
    """
    Load the Day 16 universe.

    The universe is defined by the companies present in the sectors table.
    Only the latest financial-ratio row is retained for each company.
    """

    df = load_data()

    connection = sqlite3.connect(DB_PATH)

    universe = pd.read_sql_query(
        """
        SELECT DISTINCT company_id
        FROM sectors
        """,
        connection
    )

    connection.close()

    df = df[
        df["company_id"].isin(universe["company_id"])
    ].copy()

    df["_year_sort"] = pd.to_numeric(
        df["year"],
        errors="coerce"
    )

    df = (
        df.sort_values(
            ["company_id", "_year_sort"],
            ascending=[True, False]
        )
        .drop_duplicates(
            "company_id",
            keep="first"
        )
        .drop(columns="_year_sort")
        .reset_index(drop=True)
    )

    return df


# COLUMN VALIDATION

def check_required_columns(df):
    """
    Verify all columns required by Day 16 are available.
    """

    required = [
        "company_id",
        "year",
        "return_on_equity_pct",
        "debt_to_equity",
        "free_cash_flow_cr",
        "revenue_cagr_5yr",
        "pat_cagr_5yr",
        "operating_profit_margin_pct",
        "pe_ratio",
        "pb_ratio",
        "dividend_yield_pct",
        "dividend_payout_ratio_pct",
        "market_cap_crore",
        "net_profit",
        "eps_cagr_5yr",
        "asset_turnover",
        "sales",
    ]

    missing = [
        column
        for column in required
        if column not in df.columns
    ]

    if missing:
        print("FAIL — missing columns:")

        for column in missing:
            print(f"  {column}")

        return False

    print("PASS — all required Day 16 columns are present.")

    return True


# DATA QUALITY

def print_data_quality(df):
    """
    Validate universe size, duplicates, missing values,
    infinite values and sector distribution.
    """

    print("\n" + "=" * 100)
    print("DAY 16 — DATA QUALITY CHECK")
    print("=" * 100)

    # Universe

    print("\nUNIVERSE")

    company_count = df["company_id"].nunique()

    print("Distinct companies:", company_count)
    print("Rows used:", len(df))

    if company_count == EXPECTED_UNIVERSE:
        print(
            f"PASS — exactly {EXPECTED_UNIVERSE} companies."
        )
    else:
        print(
            f"FAIL — expected {EXPECTED_UNIVERSE} companies, "
            f"found {company_count}."
        )

    
    # Duplicates

    print("\nDUPLICATES")

    duplicate_count = df["company_id"].duplicated().sum()

    if duplicate_count == 0:
        print("PASS — one latest row per company.")
    else:
        print(
            "FAIL — duplicate company rows:",
            duplicate_count
        )

    
    # Required columns
    

    print("\nREQUIRED COLUMNS")

    columns_ok = check_required_columns(df)

    # Missing values

    print("\nMISSING VALUES")

    important = [
        "return_on_equity_pct",
        "debt_to_equity",
        "free_cash_flow_cr",
        "revenue_cagr_5yr",
        "pat_cagr_5yr",
        "pe_ratio",
        "pb_ratio",
        "dividend_yield_pct",
        "dividend_payout_ratio_pct",
        "sales",
    ]

    for column in important:

        missing = df[column].isna().sum()

        if missing == 0:
            print(
                f"{column}: PASS — 0 missing"
            )
        else:
            print(
                f"{column}: {missing} missing"
            )

    
    # Infinite values
    

    print("\nINFINITE VALUES")

    numeric = df.select_dtypes(
        include="number"
    )

    inf_count = np.isinf(numeric).sum().sum()

    if inf_count == 0:
        print("PASS — no infinite values.")
    else:
        print(
            "FAIL — infinite numeric values:",
            inf_count
        )

    # Sector distribution
    

    print("\nSECTOR DISTRIBUTION")

    connection = sqlite3.connect(DB_PATH)

    sectors = pd.read_sql_query(
        """
        SELECT
            broad_sector,
            COUNT(DISTINCT company_id) AS companies
        FROM sectors
        GROUP BY broad_sector
        ORDER BY companies DESC
        """,
        connection
    )

    connection.close()

    if not sectors.empty:
        print(
            sectors.to_string(index=False)
        )

    return (
        company_count == EXPECTED_UNIVERSE
        and duplicate_count == 0
        and columns_ok
        and inf_count == 0
    )



# PRESET RESULT CHECK


def run_preset_checks(df):
    """
    Run all six presets.

    IMPORTANT:
    The 5–50 company requirement is treated as a REAL requirement.

    We do not convert fewer-than-5 results into PASS.
    We do not loosen filters.
    We do not add companies artificially.
    """

    print("\n" + "=" * 100)
    print("DAY 16 — PRESET RESULT CHECK")
    print("=" * 100)

    print(
        f"\nRequired result range: "
        f"{MIN_RESULTS} to {MAX_RESULTS} companies."
    )

    results = {}
    count_status = {}

    for name, function in PRESETS.items():

        print("\n" + "-" * 100)
        print(name)
        print("-" * 100)

        try:

            result = function(
                df.copy()
            )

            results[name] = result

            count = result["company_id"].nunique()

            print(
                "Result count:",
                count
            )

            # Count validation
            

            if MIN_RESULTS <= count <= MAX_RESULTS:

                status = "PASS"

                print(
                    f"Status: PASS — {MIN_RESULTS}–{MAX_RESULTS} range"
                )

            elif count < MIN_RESULTS:

                status = "FAIL"

                print(
                    f"Status: FAIL — fewer than {MIN_RESULTS} companies"
                )

            else:

                status = "FAIL"

                print(
                    f"Status: FAIL — more than {MAX_RESULTS} companies"
                )

            count_status[name] = status

            # Display results

            if not result.empty:

                columns = [
                    "company_id",
                    "year",
                    "return_on_equity_pct",
                    "debt_to_equity",
                    "free_cash_flow_cr",
                    "revenue_cagr_5yr",
                    "pat_cagr_5yr",
                    "pe_ratio",
                    "pb_ratio",
                    "dividend_yield_pct",
                    "dividend_payout_ratio_pct",
                    "sales",
                ]

                available = [
                    column
                    for column in columns
                    if column in result.columns
                ]

                print(
                    "\nFirst 10 matching companies:"
                )

                print(
                    result[available]
                    .head(10)
                    .to_string(index=False)
                )

            else:

                print(
                    "No companies matched this preset."
                )

        except Exception as error:

            print(
                "ERROR while running preset:"
            )

            print(
                type(error).__name__,
                ":",
                error
            )

            results[name] = pd.DataFrame()
            count_status[name] = "ERROR"

    return results, count_status


# VALUE PICK DIAGNOSTIC


def diagnose_value_pick(df):
    """
    Show exactly how many companies survive each Value Pick filter.

    This is diagnostic only. It does not modify the preset.
    """

    print("\n" + "=" * 100)
    print("VALUE PICK — DIAGNOSTIC")
    print("=" * 100)

    result = df.copy()

    conditions = {
        "P/E < 20": (
            result["pe_ratio"].notna()
            & (result["pe_ratio"] < 20)
        ),

        "P/B < 3": (
            result["pb_ratio"].notna()
            & (result["pb_ratio"] < 3)
        ),

        "D/E < 2": (
            result["debt_to_equity"].notna()
            & (result["debt_to_equity"] < 2)
        ),

        "Dividend Yield > 1": (
            result["dividend_yield_pct"].notna()
            & (result["dividend_yield_pct"] > 1)
        ),
    }

    print("\nIndividual filter counts:")

    for name, condition in conditions.items():

        print(
            f"{name}: {int(condition.sum())}"
        )

    all_conditions = (
        conditions["P/E < 20"]
        & conditions["P/B < 3"]
        & conditions["D/E < 2"]
        & conditions["Dividend Yield > 1"]
    )

    print(
        "\nAll four conditions:",
        int(all_conditions.sum())
    )

    if all_conditions.any():

        columns = [
            "company_id",
            "pe_ratio",
            "pb_ratio",
            "debt_to_equity",
            "dividend_yield_pct",
        ]

        print(
            "\nCompanies passing all four:"
        )

        print(
            result.loc[
                all_conditions,
                columns
            ].to_string(index=False)
        )



# DEBT-FREE BLUE CHIP DIAGNOSTIC

def diagnose_debt_free(df):
    """
    Show exactly how many companies survive each
    Debt-Free Blue Chip filter.

    This is diagnostic only. It does not modify the preset.
    """

    print("\n" + "=" * 100)
    print("DEBT-FREE BLUE CHIP — DIAGNOSTIC")
    print("=" * 100)

    result = df.copy()

    conditions = {
        "D/E = 0": (
            result["debt_to_equity"].notna()
            & (result["debt_to_equity"] == 0)
        ),

        "ROE > 12": (
            result["return_on_equity_pct"].notna()
            & (result["return_on_equity_pct"] > 12)
        ),

        "Revenue > 5000": (
            result["sales"].notna()
            & (result["sales"] > 5000)
        ),
    }

    print("\nIndividual filter counts:")

    for name, condition in conditions.items():

        print(
            f"{name}: {int(condition.sum())}"
        )

    all_conditions = (
        conditions["D/E = 0"]
        & conditions["ROE > 12"]
        & conditions["Revenue > 5000"]
    )

    print(
        "\nAll three conditions:",
        int(all_conditions.sum())
    )

    if all_conditions.any():

        columns = [
            "company_id",
            "debt_to_equity",
            "return_on_equity_pct",
            "sales",
        ]

        print(
            "\nCompanies passing all three:"
        )

        print(
            result.loc[
                all_conditions,
                columns
            ].to_string(index=False)
        )


# BUSINESS-SENSE VALIDATION


def business_sense_check(results):
    """
    Basic sanity checks to ensure each preset result actually
    satisfies the intended financial conditions.

    This does NOT replace the preset implementation.
    It independently verifies returned rows.
    """

    print("\n" + "=" * 100)
    print("DAY 16 — BUSINESS-SENSE VALIDATION")
    print("=" * 100)

    checks = {}

    
    # Quality Compounder

    result = results.get(
        "Quality Compounder",
        pd.DataFrame()
    )

    checks["Quality Compounder"] = (
        not result.empty
        and result["return_on_equity_pct"].gt(15).all()
        and result["debt_to_equity"].lt(1.0).all()
        and result["free_cash_flow_cr"].gt(0).all()
        and result["revenue_cagr_5yr"].gt(10).all()
    )

    # Value Pick
    

    result = results.get(
        "Value Pick",
        pd.DataFrame()
    )

    checks["Value Pick"] = (
        not result.empty
        and result["pe_ratio"].lt(20).all()
        and result["pb_ratio"].lt(3.0).all()
        and result["debt_to_equity"].lt(2.0).all()
        and result["dividend_yield_pct"].gt(1).all()
    )

    
    # Growth Accelerator
    
    result = results.get(
        "Growth Accelerator",
        pd.DataFrame()
    )

    checks["Growth Accelerator"] = (
        not result.empty
        and result["pat_cagr_5yr"].gt(20).all()
        and result["revenue_cagr_5yr"].gt(15).all()
        and result["debt_to_equity"].lt(2.0).all()
    )

    
    # Dividend Champion
    

    result = results.get(
        "Dividend Champion",
        pd.DataFrame()
    )

    checks["Dividend Champion"] = (
        not result.empty
        and result["dividend_yield_pct"].gt(2).all()
        and result["dividend_payout_ratio_pct"].lt(80).all()
        and result["free_cash_flow_cr"].gt(0).all()
    )

    
    # Debt-Free Blue Chip

    result = results.get(
        "Debt-Free Blue Chip",
        pd.DataFrame()
    )

    checks["Debt-Free Blue Chip"] = (
        not result.empty
        and result["debt_to_equity"].eq(0).all()
        and result["return_on_equity_pct"].gt(12).all()
        and result["sales"].gt(5000).all()
    )

    # Turnaround Watch
    

    result = results.get(
        "Turnaround Watch",
        pd.DataFrame()
    )

    turnaround_ok = False

    if not result.empty:

        revenue_ok = (
            "revenue_cagr_3yr" in result.columns
            and result["revenue_cagr_3yr"].gt(10).all()
        )

        fcf_ok = (
            result["free_cash_flow_cr"].gt(0).all()
        )

        de_ok = verify_turnaround_de_decline(
            result
        )

        turnaround_ok = (
            revenue_ok
            and fcf_ok
            and de_ok
        )

    checks["Turnaround Watch"] = turnaround_ok

    # Print

    for name, passed in checks.items():

        print(
            f"{name:<25}",
            "PASS" if passed else "FAIL"
        )

    return checks


# TURNAROUND D/E VALIDATION

def verify_turnaround_de_decline(result):
    """
    Independently verify that Turnaround Watch companies have
    lower latest-year D/E than the previous year.

    Uses the database directly rather than trusting a column
    produced by the preset.
    """

    if result.empty:
        return False

    company_ids = result["company_id"].tolist()

    if not company_ids:
        return False

    placeholders = ",".join(
        ["?"] * len(company_ids)
    )

    connection = sqlite3.connect(DB_PATH)

    query = f"""
        SELECT
            company_id,
            year,
            debt_to_equity
        FROM financial_ratios
        WHERE company_id IN ({placeholders})
          AND year IN (2023, 2024)
    """

    de = pd.read_sql_query(
        query,
        connection,
        params=company_ids
    )

    connection.close()

    if de.empty:
        return False

    de["year"] = pd.to_numeric(
        de["year"],
        errors="coerce"
    )

    pivot = de.pivot_table(
        index="company_id",
        columns="year",
        values="debt_to_equity",
        aggfunc="last"
    )

    required_columns = {
        2023,
        2024
    }

    if not required_columns.issubset(
        set(pivot.columns)
    ):
        return False

    selected = pivot.reindex(
        company_ids
    )

    valid = (
        selected[2023].notna()
        & selected[2024].notna()
    )

    if not valid.all():
        return False

    return (
        selected.loc[valid, 2024]
        < selected.loc[valid, 2023]
    ).all()



# EXACT RULE SUMMARY

def print_requirement_summary():
    """
    Print the six Day 16 rules exactly as specified.
    """

    print("\n" + "=" * 100)
    print("DAY 16 — PRESCRIBED RULES")
    print("=" * 100)

    rules = [
        (
            "Quality Compounder",
            "ROE > 15%, D/E < 1.0, FCF > 0, "
            "Revenue CAGR 5yr > 10%"
        ),
        (
            "Value Pick",
            "P/E < 20, P/B < 3.0, D/E < 2.0, "
            "Dividend Yield > 1%"
        ),
        (
            "Growth Accelerator",
            "PAT CAGR 5yr > 20%, Revenue CAGR 5yr > 15%, "
            "D/E < 2.0"
        ),
        (
            "Dividend Champion",
            "Dividend Yield > 2%, Dividend Payout < 80%, "
            "FCF > 0"
        ),
        (
            "Debt-Free Blue Chip",
            "D/E = 0, ROE > 12%, Revenue > 5000 Crore"
        ),
        (
            "Turnaround Watch",
            "Revenue CAGR 3yr > 10%, FCF > 0, "
            "D/E declining year-over-year"
        ),
    ]

    for name, rule in rules:

        print(
            f"{name:<25} {rule}"
        )


# MAIN

def main():

    print(
        "\nStarting Day 16 quality check..."
    )

    print_requirement_summary()

    # Load data

    df = load_latest_universe()

    
    # Data quality

    data_quality_ok = print_data_quality(
        df
    )

    if not check_required_columns(df):

        print(
            "\nSTATUS: FAIL — required columns are missing."
        )

        return

    # Preset checks

    results, count_status = run_preset_checks(
        df
    )

    
    # Diagnostics
    

    diagnose_value_pick(df)

    diagnose_debt_free(df)

    
    # Business sense
    

    business_checks = business_sense_check(
        results
    )

    # Final validation

    print("\n" + "=" * 100)
    print("FINAL DAY 16 CHECK")
    print("=" * 100)

    count_failures = []
    preset_errors = []

    for name, status in count_status.items():

        if status == "ERROR":
            preset_errors.append(name)

        elif status == "FAIL":
            count_failures.append(name)

    business_failures = [
        name
        for name, passed in business_checks.items()
        if not passed
    ]

    print(
        "\nPRESET COUNT SUMMARY"
    )

    for name in PRESETS:

        result = results.get(
            name,
            pd.DataFrame()
        )

        count = (
            result["company_id"].nunique()
            if not result.empty
            else 0
        )

        status = count_status.get(
            name,
            "ERROR"
        )

        print(
            f"{name:<25}"
            f"{count:>4} companies   "
            f"{status}"
        )

    print(
        "\nCount requirement:"
    )

    print(
        f"Each preset must return "
        f"{MIN_RESULTS}–{MAX_RESULTS} companies."
    )

    if count_failures:

        print(
            "\nCOUNT REQUIREMENT FAILURES:"
        )

        for name in count_failures:

            result = results.get(
                name,
                pd.DataFrame()
            )

            count = (
                result["company_id"].nunique()
                if not result.empty
                else 0
            )

            print(
                f"  - {name}: {count} companies"
            )

    if preset_errors:

        print(
            "\nPRESET EXECUTION ERRORS:"
        )

        for name in preset_errors:

            print(
                f"  - {name}"
            )

    if business_failures:

        print(
            "\nBUSINESS-SENSE FAILURES:"
        )

        for name in business_failures:

            print(
                f"  - {name}"
            )

    # Final status
    

    print(
        "\n" + "=" * 100
    )

    if (
        data_quality_ok
        and not count_failures
        and not preset_errors
        and not business_failures
    ):

        print(
            "STATUS: DAY 16 IMPLEMENTATION PASS"
        )

        print(
            "All six presets satisfy the prescribed rules."
        )

        print(
            f"All six presets return {MIN_RESULTS}–"
            f"{MAX_RESULTS} companies."
        )

        print(
            f"{EXPECTED_UNIVERSE}-company universe validated."
        )

    else:

        print(
            "STATUS: DAY 16 IMPLEMENTATION FAIL"
        )

        if count_failures:

            print(
                "Reason: one or more presets do not satisfy "
                "the required 5–50 result-count range."
            )

        if preset_errors:

            print(
                "Reason: one or more presets could not execute."
            )

        if business_failures:

            print(
                "Reason: one or more preset results failed "
                "independent business-rule validation."
            )

        if not data_quality_ok:

            print(
                "Reason: data-quality validation failed."
            )

    print(
        "=" * 100
    )


if __name__ == "__main__":
    main()
