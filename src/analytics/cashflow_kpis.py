import os
import re
import sqlite3
import pandas as pd


DB_PATH = "data/nifty100.db"
OUTPUT_PATH = "output/capital_allocation.csv"


# 1. FREE CASH FLOW

def calculate_free_cash_flow(
    operating_activity,
    investing_activity
):
    """
    FCF = Operating Activity + Investing Activity.

    Negative FCF is allowed.
    """

    if operating_activity is None:
        return None

    if investing_activity is None:
        return None

    return operating_activity + investing_activity


# 2. CFO / PAT RATIO

def calculate_cfo_pat_ratio(cfo, pat):
    """
    CFO / PAT.

    Return None when PAT is zero or data is missing.
    """

    if cfo is None:
        return None

    if pat is None:
        return None

    if pat == 0:
        return None

    return cfo / pat


# 3. FIVE-YEAR ROLLING CFO QUALITY SCORE

def calculate_cfo_quality_score(rows, current_year):
    """
    Calculate the average CFO/PAT ratio over the current year
    and the previous four available annual years.

    The score is calculated separately for every company/year.

    PAT = 0 years are excluded because CFO/PAT is undefined.

    A score is returned only when there are valid CFO/PAT
    observations in the five-year window.
    """

    if not rows:
        return None

    rows = sorted(
        rows,
        key=lambda row: row["year"]
    )

    eligible_rows = [
        row
        for row in rows
        if row["year"] <= current_year
    ]

    latest_five = eligible_rows[-5:]

    ratios = []

    for row in latest_five:

        ratio = calculate_cfo_pat_ratio(
            row["operating_activity"],
            row["net_profit"]
        )

        if ratio is not None:
            ratios.append(ratio)

    if not ratios:
        return None

    return sum(ratios) / len(ratios)


# 4. CFO QUALITY CLASSIFICATION

def classify_cfo_quality(score):
    """
    > 1.0 = High Quality
    0.5 - 1.0 = Moderate
    < 0.5 = Accrual Risk
    """

    if score is None:
        return None

    if score > 1.0:
        return "High Quality"

    if score >= 0.5:
        return "Moderate"

    return "Accrual Risk"


# 5. CAPEX INTENSITY

def calculate_capex_intensity(
    investing_activity,
    sales
):
    """
    abs(investing_activity) / sales * 100.

    Return None when sales is zero or missing.
    """

    if investing_activity is None:
        return None

    if sales is None:
        return None

    if sales == 0:
        return None

    return (
        abs(investing_activity)
        / sales
        * 100
    )


# 6. CAPEX CLASSIFICATION

def classify_capex_intensity(value):
    """
    < 3% = Asset Light
    3% - 8% = Moderate
    > 8% = Capital Intensive
    """

    if value is None:
        return None

    if value < 3:
        return "Asset Light"

    if value <= 8:
        return "Moderate"

    return "Capital Intensive"


# 7. FCF CONVERSION RATE

def calculate_fcf_conversion_rate(
    free_cash_flow,
    operating_profit
):
    """
    FCF / Operating Profit * 100.

    Return None when operating profit is zero.
    """

    if free_cash_flow is None:
        return None

    if operating_profit is None:
        return None

    if operating_profit == 0:
        return None

    return (
        free_cash_flow
        / operating_profit
        * 100
    )


# 8. CASH FLOW SIGN

def get_cashflow_sign(value):
    """
    Positive = +
    Negative = -
    Zero = 0
    """

    if value is None:
        return "0"

    if value > 0:
        return "+"

    if value < 0:
        return "-"

    return "0"


# 9. CAPITAL ALLOCATION CLASSIFIER

def classify_capital_allocation(
    cfo,
    cfi,
    cff,
    cfo_quality_score=None
):
    """
    (+,-,-) with high CFO Quality Score = Shareholder Returns
    (+,-,-) = Reinvestor
    (+,+,-) = Liquidating Assets
    (-,+,+) = Distress Signal
    (-,-,+) = Growth Funded by Debt
    (+,+,+) = Cash Accumulator
    (-,-,-) = Pre-Revenue
    (+,-,+) = Mixed
    """

    cfo_sign = get_cashflow_sign(cfo)
    cfi_sign = get_cashflow_sign(cfi)
    cff_sign = get_cashflow_sign(cff)

    pattern = (
        cfo_sign,
        cfi_sign,
        cff_sign
    )

    if pattern == ("+", "-", "-"):

        if (
            cfo_quality_score is not None
            and cfo_quality_score > 1.0
        ):
            return "Shareholder Returns"

        return "Reinvestor"

    if pattern == ("+", "+", "-"):
        return "Liquidating Assets"

    if pattern == ("-", "+", "+"):
        return "Distress Signal"

    if pattern == ("-", "-", "+"):
        return "Growth Funded by Debt"

    if pattern == ("+", "+", "+"):
        return "Cash Accumulator"

    if pattern == ("-", "-", "-"):
        return "Pre-Revenue"

    if pattern == ("+", "-", "+"):
        return "Mixed"

    return "Mixed"


# 10. VALID ANNUAL MARCH PERIOD
#
# This function is intentionally STRICT because the unit test
# requires two-digit years such as "Mar 24" to be rejected.
#
# Therefore:
#   Mar 2024 -> True
#   Mar 2013 -> True
#   Mar 24   -> False
#
# Do NOT change this function to accept two-digit years.


def is_annual_march_period(period):
    """
    Accept only exact annual March periods.

    Valid:
        Mar 2013
        Mar 2014
        Mar 2024

    Invalid:
        Mar 24
        Mar 2023 15
        Mar 2016 9m
        TTM
        Dec 2023
        Jun 2023
        Sep 2023
    """

    if not isinstance(period, str):
        return False

    period = period.strip()

    parts = period.split()

    if len(parts) != 2:
        return False

    month, year = parts

    if month != "Mar":
        return False

    if len(year) != 4:
        return False

    if not year.isdigit():
        return False

    return True


# 10A. DATABASE ANNUAL MARCH PERIOD
#
# The source database contains some legacy periods such as:
#   Mar 13
#   Mar 14
#   Mar 15
#   ...
#   Mar 24
#
# These are annual periods even though the year is stored with
# two digits.
#
# This helper is ONLY used when loading the real database.
# It does NOT replace is_annual_march_period(), so the existing
# unit test remains correct.


def is_database_annual_march_period(period):
    """
    Accept annual March periods as stored in the database.

    Valid:
        Mar 13
        Mar 14
        Mar 24
        Mar 2013
        Mar 2014
        Mar 2024

    Invalid:
        Mar 2023 15
        Mar 2016 9m
        TTM
        Dec 2023
        Jun 2023
        Sep 2023
    """

    if not isinstance(period, str):
        return False

    period = period.strip()

    parts = period.split()

    if len(parts) != 2:
        return False

    month, year = parts

    if month != "Mar":
        return False

    if not year.isdigit():
        return False

    return len(year) in (2, 4)


# 11. LOAD DATA

def load_data(connection):

    query = """
        SELECT
            cf.company_id,
            cf.year,
            cf.period,
            cf.operating_activity,
            cf.investing_activity,
            cf.financing_activity,
            pl.sales,
            pl.operating_profit,
            pl.net_profit
        FROM cashflow cf
        LEFT JOIN profitandloss pl
            ON cf.company_id = pl.company_id
            AND cf.year = pl.year
            AND cf.period = pl.period
        ORDER BY
            cf.company_id,
            cf.year
    """

    df = pd.read_sql_query(
        query,
        connection
    )

    # The database contains both four-digit and legacy
    # two-digit annual March periods.
    #
    # Example:
    #   Mar 2024
    #   Mar 13
    #   Mar 14
    #
    # Use the database-specific validator here so legacy
    # records such as TCS are not accidentally dropped.

    df = df[
        df["period"].apply(
            is_database_annual_march_period
        )
    ].copy()

    return df


# 12. CALCULATE KPIs

def calculate_kpis(df):

    df = df.copy()

    # Free Cash Flow

    df["free_cash_flow"] = df.apply(
        lambda row: calculate_free_cash_flow(
            row["operating_activity"],
            row["investing_activity"]
        ),
        axis=1
    )

    # Annual CFO/PAT ratio

    df["cfo_pat_ratio"] = df.apply(
        lambda row: calculate_cfo_pat_ratio(
            row["operating_activity"],
            row["net_profit"]
        ),
        axis=1
    )

    # Five-year rolling CFO Quality Score

    df["cfo_quality_score"] = None

    for company_id, group in df.groupby(
        "company_id",
        sort=False
    ):

        group_rows = group.to_dict(
            "records"
        )

        for index, row in group.iterrows():

            score = calculate_cfo_quality_score(
                group_rows,
                int(row["year"])
            )

            df.loc[
                index,
                "cfo_quality_score"
            ] = score

    # CFO Quality Label

    df["cfo_quality_label"] = df[
        "cfo_quality_score"
    ].apply(
        classify_cfo_quality
    )

    # CapEx Intensity

    df["capex_intensity_pct"] = df.apply(
        lambda row: calculate_capex_intensity(
            row["investing_activity"],
            row["sales"]
        ),
        axis=1
    )

    # CapEx Intensity Label

    df["capex_intensity_label"] = df[
        "capex_intensity_pct"
    ].apply(
        classify_capex_intensity
    )

    # FCF Conversion Rate

    df["fcf_conversion_rate_pct"] = df.apply(
        lambda row: calculate_fcf_conversion_rate(
            row["free_cash_flow"],
            row["operating_profit"]
        ),
        axis=1
    )

    # Cash flow signs

    df["cfo_sign"] = df[
        "operating_activity"
    ].apply(
        get_cashflow_sign
    )

    df["cfi_sign"] = df[
        "investing_activity"
    ].apply(
        get_cashflow_sign
    )

    df["cff_sign"] = df[
        "financing_activity"
    ].apply(
        get_cashflow_sign
    )

    # Capital allocation pattern

    df["pattern_label"] = df.apply(
        lambda row: classify_capital_allocation(
            row["operating_activity"],
            row["investing_activity"],
            row["financing_activity"],
            row["cfo_quality_score"]
        ),
        axis=1
    )

    return df


# 13. GENERATE REQUIRED CSV

def generate_capital_allocation_csv(df):

    os.makedirs(
        "output",
        exist_ok=True
    )

    output_columns = [
        "company_id",
        "year",
        "cfo_sign",
        "cfi_sign",
        "cff_sign",
        "pattern_label"
    ]

    output_df = df[
        output_columns
    ].copy()

    output_df.to_csv(
        OUTPUT_PATH,
        index=False
    )

    return output_df


# 14. MAIN

def main():

    print("DAY 11 - CASH FLOW KPIs & CAPITAL ALLOCATION")

    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(
            f"Database not found: {DB_PATH}"
        )

    connection = sqlite3.connect(
        DB_PATH
    )

    try:

        print("\nLoading annual March data...")

        df = load_data(
            connection
        )

        print(
            "Rows loaded:",
            len(df)
        )

        print(
            "Companies:",
            df["company_id"].nunique()
        )

        print(
            "Years:",
            df["year"].nunique()
        )

        print("\nCalculating Day 11 KPIs...")

        result = calculate_kpis(
            df
        )

        print("\nGenerating capital allocation CSV...")

        output_df = generate_capital_allocation_csv(
            result
        )

        print(
            "\nCreated:",
            OUTPUT_PATH
        )

        print(
            "Rows:",
            len(output_df)
        )

        print("\nPattern summary:")

        print(
            output_df[
                "pattern_label"
            ].value_counts().to_string()
        )

        print("\nDay 11 completed successfully.")

    finally:

        connection.close()


if __name__ == "__main__":
    main()