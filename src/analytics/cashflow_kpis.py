import os
import sqlite3
import math
import pandas as pd


DB_PATH = "data/nifty100.db"

CAPITAL_ALLOCATION_OUTPUT = "output/capital_allocation.csv"
INTELLIGENCE_OUTPUT = "output/cashflow_intelligence.xlsx"
DISTRESS_OUTPUT = "output/distress_alerts.csv"


def safe_float(value):
    if value is None:
        return None

    try:
        value = float(value)
    except (TypeError, ValueError):
        return None

    if math.isnan(value):
        return None

    return value


def get_cashflow_sign(value):
    value = safe_float(value)

    if value is None:
        return "0"

    if value > 0:
        return "+"

    if value < 0:
        return "-"

    return "0"


def calculate_free_cash_flow(
    operating_activity,
    investing_activity
):
    operating_activity = safe_float(
        operating_activity
    )

    investing_activity = safe_float(
        investing_activity
    )

    if operating_activity is None:
        return None

    if investing_activity is None:
        return None

    return (
        operating_activity
        + investing_activity
    )


def calculate_cfo_pat_ratio(
    cfo,
    pat
):
    cfo = safe_float(cfo)
    pat = safe_float(pat)

    if cfo is None:
        return None

    if pat is None:
        return None

    if pat == 0:
        return None

    return cfo / pat


def calculate_cfo_quality_score(
    rows,
    current_year
):
    if not rows:
        return None

    rows = sorted(
        rows,
        key=lambda row: row["year"]
    )

    eligible_rows = [
        row
        for row in rows
        if safe_float(row["year"]) is not None
        and int(row["year"]) <= int(current_year)
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


def classify_cfo_quality(score):
    score = safe_float(score)

    if score is None:
        return None

    if score > 1.0:
        return "High Quality"

    if score >= 0.5:
        return "Moderate"

    return "Accrual Risk"


def calculate_capex_intensity(
    investing_activity,
    sales
):
    investing_activity = safe_float(
        investing_activity
    )

    sales = safe_float(sales)

    if investing_activity is None:
        return None

    if sales is None:
        return None

    if sales == 0:
        return None

    return (
        abs(investing_activity)
        / abs(sales)
        * 100
    )


def classify_capex_intensity(value):
    value = safe_float(value)

    if value is None:
        return None

    if value < 3:
        return "Asset Light"

    if value <= 8:
        return "Moderate"

    return "Capital Intensive"


def calculate_fcf_conversion_rate(
    free_cash_flow,
    operating_profit
):
    free_cash_flow = safe_float(
        free_cash_flow
    )

    operating_profit = safe_float(
        operating_profit
    )

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


def calculate_fcf_cagr_5yr(
    rows,
    current_year
):
    if not rows:
        return None

    rows = sorted(
        rows,
        key=lambda row: row["year"]
    )

    eligible_rows = [
        row
        for row in rows
        if safe_float(row["year"]) is not None
        and int(row["year"]) <= int(current_year)
    ]

    if len(eligible_rows) < 6:
        return None

    current_row = eligible_rows[-1]

    current_fcf = calculate_free_cash_flow(
        current_row["operating_activity"],
        current_row["investing_activity"]
    )

    if current_fcf is None:
        return None

    target_year = int(current_year) - 5

    previous_rows = [
        row
        for row in eligible_rows
        if int(row["year"]) <= target_year
    ]

    if not previous_rows:
        return None

    previous_row = previous_rows[-1]

    previous_fcf = calculate_free_cash_flow(
        previous_row["operating_activity"],
        previous_row["investing_activity"]
    )

    if previous_fcf is None:
        return None

    if previous_fcf <= 0:
        return None

    if current_fcf <= 0:
        return None

    cagr = (
        (current_fcf / previous_fcf) ** (1 / 5)
        - 1
    ) * 100

    return cagr


def classify_capital_allocation(
    cfo,
    cfi,
    cff,
    cfo_quality_score=None
):
    cfo_sign = get_cashflow_sign(cfo)
    cfi_sign = get_cashflow_sign(cfi)
    cff_sign = get_cashflow_sign(cff)

    pattern = (
        cfo_sign,
        cfi_sign,
        cff_sign
    )

    if pattern == ("+", "-", "-"):
        score = safe_float(
            cfo_quality_score
        )

        if (
            score is not None
            and score > 1.0
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


def is_annual_march_period(period):
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


def is_database_annual_march_period(period):
    if not isinstance(period, str):
        return False

    period = period.strip()

    parts = period.split()

    if len(parts) != 2:
        return False

    month, year = parts

    if month not in ("Mar", "Jun", "Sep", "Dec"):
        return False

    if not year.isdigit():
        return False

    return len(year) in (2, 4)


def normalize_year(value):
    value = safe_float(value)

    if value is None:
        return None

    year = int(value)

    if 0 <= year <= 99:
        return 2000 + year

    return year


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
            pl.net_profit,
            bs.borrowings,
            s.broad_sector AS sector
        FROM cashflow cf
        LEFT JOIN profitandloss pl
            ON cf.company_id = pl.company_id
            AND cf.year = pl.year
            
        LEFT JOIN balancesheet bs
            ON cf.company_id = bs.company_id
            AND cf.year = bs.year
            
        LEFT JOIN sectors s
            ON cf.company_id = s.company_id
        ORDER BY
            cf.company_id,
            cf.year
    """

    df = pd.read_sql_query(
        query,
        connection
    )

    df = df[
        df["period"].apply(
            is_database_annual_march_period
        )
    ].copy()

    df["year"] = df["year"].apply(
        normalize_year
    )

    df = df[
        df["year"].notna()
    ].copy()

    df["year"] = df["year"].astype(int)

    df.sort_values(
        ["company_id", "year"],
        inplace=True
    )

    df.reset_index(
        drop=True,
        inplace=True
    )

    return df


def calculate_kpis(df):
    df = df.copy()

    df["free_cash_flow"] = df.apply(
        lambda row: calculate_free_cash_flow(
            row["operating_activity"],
            row["investing_activity"]
        ),
        axis=1
    )

    df["cfo_pat_ratio"] = df.apply(
        lambda row: calculate_cfo_pat_ratio(
            row["operating_activity"],
            row["net_profit"]
        ),
        axis=1
    )

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

    df["cfo_quality_label"] = df[
        "cfo_quality_score"
    ].apply(
        classify_cfo_quality
    )

    df["capex_intensity_pct"] = df.apply(
        lambda row: calculate_capex_intensity(
            row["investing_activity"],
            row["sales"]
        ),
        axis=1
    )

    df["capex_intensity_label"] = df[
        "capex_intensity_pct"
    ].apply(
        classify_capex_intensity
    )

    df["fcf_conversion_rate_pct"] = df.apply(
        lambda row: calculate_fcf_conversion_rate(
            row["free_cash_flow"],
            row["operating_profit"]
        ),
        axis=1
    )

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


def build_cashflow_intelligence(df):
    output_rows = []

    for company_id, group in df.groupby(
        "company_id",
        sort=False
    ):
        group = group.sort_values(
            "year"
        ).copy()

        if group.empty:
            continue

        latest = group.iloc[-1]

        latest_year = int(
            latest["year"]
        )

        latest_cfo = safe_float(
            latest["operating_activity"]
        )

        latest_cff = safe_float(
            latest["financing_activity"]
        )

        company_rows = group.to_dict(
            "records"
        )

        cfo_quality_score = calculate_cfo_quality_score(
            company_rows,
            latest_year
        )

        cfo_quality_label = classify_cfo_quality(
            cfo_quality_score
        )

        capex_intensity_pct = calculate_capex_intensity(
            latest["investing_activity"],
            latest["sales"]
        )

        capex_label = classify_capex_intensity(
            capex_intensity_pct
        )

        fcf_cagr_5yr = calculate_fcf_cagr_5yr(
            company_rows,
            latest_year
        )

        latest_fcf = calculate_free_cash_flow(
            latest["operating_activity"],
            latest["investing_activity"]
        )

        fcf_conversion_pct = calculate_fcf_conversion_rate(
            latest_fcf,
            latest["operating_profit"]
        )

        distress_flag = (
            latest_cfo is not None
            and latest_cff is not None
            and latest_cfo < 0
            and latest_cff > 0
        )

        deleveraging_flag = False

        latest_borrowings = safe_float(
            latest["borrowings"]
        )

        previous_rows = group[
            group["year"] < latest_year
        ]

        if not previous_rows.empty:

            previous = previous_rows.iloc[-1]

            previous_borrowings = safe_float(
                previous["borrowings"]
            )

            if (
                latest_cff is not None
                and latest_cff < 0
                and latest_borrowings is not None
                and previous_borrowings is not None
                and latest_borrowings < previous_borrowings
            ):
                deleveraging_flag = True

        capital_allocation_label = classify_capital_allocation(
            latest["operating_activity"],
            latest["investing_activity"],
            latest["financing_activity"],
            cfo_quality_score
        )

        sector = latest["sector"]

        if pd.isna(sector):
            sector = None

        output_rows.append({
            "company_id": str(company_id),
            "sector": sector,
            "cfo_quality_score": cfo_quality_score,
            "cfo_quality_label": cfo_quality_label,
            "capex_intensity_pct": capex_intensity_pct,
            "capex_label": capex_label,
            "fcf_cagr_5yr": fcf_cagr_5yr,
            "fcf_conversion_pct": fcf_conversion_pct,
            "distress_flag": bool(distress_flag),
            "deleveraging_flag": bool(deleveraging_flag),
            "capital_allocation_label": capital_allocation_label,
        })

    return pd.DataFrame(
        output_rows,
        columns=[
            "company_id",
            "sector",
            "cfo_quality_score",
            "cfo_quality_label",
            "capex_intensity_pct",
            "capex_label",
            "fcf_cagr_5yr",
            "fcf_conversion_pct",
            "distress_flag",
            "deleveraging_flag",
            "capital_allocation_label",
        ]
    )


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
        CAPITAL_ALLOCATION_OUTPUT,
        index=False
    )

    return output_df


def generate_cashflow_intelligence_xlsx(
    intelligence_df
):
    os.makedirs(
        "output",
        exist_ok=True
    )

    intelligence_df.to_excel(
        INTELLIGENCE_OUTPUT,
        index=False
    )

    return intelligence_df


def generate_distress_alerts(df):
    os.makedirs(
        "output",
        exist_ok=True
    )

    distress_rows = []

    for company_id, group in df.groupby(
        "company_id",
        sort=False
    ):
        group = group.sort_values(
            "year"
        )

        if group.empty:
            continue

        latest = group.iloc[-1]

        cfo = safe_float(
            latest["operating_activity"]
        )

        cff = safe_float(
            latest["financing_activity"]
        )

        latest_net_profit = safe_float(
            latest["net_profit"]
        )

        if (
            cfo is not None
            and cff is not None
            and cfo < 0
            and cff > 0
        ):
            distress_rows.append({
                "company_id": str(company_id),
                "cfo": cfo,
                "cff": cff,
                "latest_net_profit": latest_net_profit,
            })

    distress_df = pd.DataFrame(
        distress_rows,
        columns=[
            "company_id",
            "cfo",
            "cff",
            "latest_net_profit",
        ]
    )

    distress_df.to_csv(
        DISTRESS_OUTPUT,
        index=False
    )

    return distress_df


def verify_outputs(
    df,
    intelligence_df,
    distress_df
):
    expected_intelligence_columns = [
        "company_id",
        "sector",
        "cfo_quality_score",
        "cfo_quality_label",
        "capex_intensity_pct",
        "capex_label",
        "fcf_cagr_5yr",
        "fcf_conversion_pct",
        "distress_flag",
        "deleveraging_flag",
        "capital_allocation_label",
    ]

    expected_distress_columns = [
        "company_id",
        "cfo",
        "cff",
        "latest_net_profit",
    ]

    intelligence_columns_valid = (
        list(intelligence_df.columns)
        == expected_intelligence_columns
    )

    distress_columns_valid = (
        list(distress_df.columns)
        == expected_distress_columns
    )

    company_count = df[
        "company_id"
    ].nunique()

    intelligence_company_count = intelligence_df[
        "company_id"
    ].nunique()

    distress_flags = intelligence_df[
        "distress_flag"
    ].fillna(False).astype(bool)

    distress_output_count = len(
        distress_df
    )

    distress_flag_count = int(
        distress_flags.sum()
    )

    distress_counts_match = (
        distress_output_count
        == distress_flag_count
    )

    capital_allocation_labels_valid = (
        intelligence_df[
            "capital_allocation_label"
        ].notna().all()
    )

    print()
    print("Day 31 verification:")
    print(
        "Companies in source:",
        company_count
    )
    print(
        "Companies in intelligence output:",
        intelligence_company_count
    )
    print(
        "Intelligence columns valid:",
        intelligence_columns_valid
    )
    print(
        "Distress columns valid:",
        distress_columns_valid
    )
    print(
        "Distress flags:",
        distress_flag_count
    )
    print(
        "Distress alert rows:",
        distress_output_count
    )
    print(
        "Distress counts match:",
        distress_counts_match
    )
    print(
        "Capital allocation labels valid:",
        capital_allocation_labels_valid
    )

    verification_passed = (
        company_count > 0
        and intelligence_company_count == company_count
        and intelligence_columns_valid
        and distress_columns_valid
        and distress_counts_match
        and capital_allocation_labels_valid
        and os.path.exists(
            INTELLIGENCE_OUTPUT
        )
        and os.path.exists(
            DISTRESS_OUTPUT
        )
        and os.path.exists(
            CAPITAL_ALLOCATION_OUTPUT
        )
    )

    if verification_passed:
        print()
        print(
            "VERIFICATION PASSED: Day 31 Cash Flow Intelligence "
            "outputs generated successfully."
        )
    else:
        print()
        print(
            "VERIFICATION FAILED: one or more Day 31 requirements "
            "were not satisfied."
        )

        raise SystemExit(1)


def main():

    print(
        "DAY 31 - CASH FLOW INTELLIGENCE MODULE"
    )

    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(
            f"Database not found: {DB_PATH}"
        )

    os.makedirs(
        "output",
        exist_ok=True
    )

    connection = sqlite3.connect(
        DB_PATH
    )

    try:

        print(
            "\nLoading annual March cash flow data..."
        )

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

        if df.empty:
            raise ValueError(
                "No annual March cash flow data was found."
            )

        print(
            "\nCalculating cash flow KPIs..."
        )

        result = calculate_kpis(
            df
        )

        print(
            "\nGenerating capital allocation CSV..."
        )

        capital_allocation_df = (
            generate_capital_allocation_csv(
                result
            )
        )

        print(
            "Created:",
            CAPITAL_ALLOCATION_OUTPUT
        )

        print(
            "Rows:",
            len(capital_allocation_df)
        )

        print(
            "\nGenerating company-level cash flow intelligence..."
        )

        intelligence_df = (
            build_cashflow_intelligence(
                result
            )
        )

        print(
            "\nGenerating cashflow intelligence Excel..."
        )

        generate_cashflow_intelligence_xlsx(
            intelligence_df
        )

        print(
            "Created:",
            INTELLIGENCE_OUTPUT
        )

        print(
            "\nGenerating distress alerts..."
        )

        distress_df = generate_distress_alerts(
            result
        )

        print(
            "Created:",
            DISTRESS_OUTPUT
        )

        print(
            "Distress companies:",
            len(distress_df)
        )

        print(
            "\nCapital allocation pattern summary:"
        )

        print(
            intelligence_df[
                "capital_allocation_label"
            ]
            .value_counts()
            .to_string()
        )

        print(
            "\nCFO Quality summary:"
        )

        print(
            intelligence_df[
                "cfo_quality_label"
            ]
            .value_counts(
                dropna=False
            )
            .to_string()
        )

        print(
            "\nCapEx intensity summary:"
        )

        print(
            intelligence_df[
                "capex_label"
            ]
            .value_counts(
                dropna=False
            )
            .to_string()
        )

        print(
            "\nDistress signal companies:",
            int(
                intelligence_df[
                    "distress_flag"
                ]
                .fillna(False)
                .astype(bool)
                .sum()
            )
        )

        print(
            "Deleveraging companies:",
            int(
                intelligence_df[
                    "deleveraging_flag"
                ]
                .fillna(False)
                .astype(bool)
                .sum()
            )
        )

        verify_outputs(
            result,
            intelligence_df,
            distress_df
        )

        print()
        print(
            "Day 31 Cash Flow Intelligence completed successfully."
        )

    finally:
        connection.close()


if __name__ == "__main__":
    main()
