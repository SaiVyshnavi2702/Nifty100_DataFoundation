import sqlite3
import pandas as pd

from src.screener.engine import load_data, DB_PATH


def _get_92_company_universe():
    """
    Return the companies present in the sectors table.
    The Day 16 validation expects this universe to contain 92 companies.
    """
    connection = sqlite3.connect(DB_PATH)

    rows = connection.execute(
        "SELECT DISTINCT company_id FROM sectors"
    ).fetchall()

    connection.close()

    return {row[0] for row in rows}


def _latest_per_company(df):
    """
    Restrict the input to the Day 16 universe and keep the latest
    available financial-ratio row for each company.
    """

    result = df.copy()

    universe = _get_92_company_universe()

    result = result[
        result["company_id"].isin(universe)
    ].copy()

    result["_year_sort"] = pd.to_numeric(
        result["year"],
        errors="coerce"
    )

    result = (
        result
        .sort_values(
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

    return result


def _strict_min(df, column, threshold):
    """
    Keep non-null values strictly greater than threshold.
    """
    return df[
        df[column].notna()
        & (df[column] > threshold)
    ].copy()


def _strict_max(df, column, threshold):
    """
    Keep non-null values strictly less than threshold.
    """
    return df[
        df[column].notna()
        & (df[column] < threshold)
    ].copy()


def _sort(df):
    """
    Sort by the existing Day 15 composite quality score when available.
    """
    if "composite_quality_score" not in df.columns:
        return df.reset_index(drop=True)

    return (
        df.sort_values(
            by="composite_quality_score",
            ascending=False,
            na_position="last"
        )
        .reset_index(drop=True)
    )


def quality_compounder(df):
    """
    Quality Compounder

    Requirements:
    - ROE > 15%
    - D/E < 1.0
    - FCF > 0
    - Revenue CAGR 5yr > 10%
    """

    result = _latest_per_company(df)

    result = _strict_min(
        result,
        "return_on_equity_pct",
        15
    )

    result = _strict_max(
        result,
        "debt_to_equity",
        1.0
    )

    result = _strict_min(
        result,
        "free_cash_flow_cr",
        0
    )

    result = _strict_min(
        result,
        "revenue_cagr_5yr",
        10
    )

    return _sort(result)


def value_pick(df):
    """
    Value Pick

    Requirements:
    - P/E < 20
    - P/B < 3.0
    - D/E < 2.0
    - Dividend Yield > 1%
    """

    result = _latest_per_company(df)

    result = _strict_max(
        result,
        "pe_ratio",
        20
    )

    result = _strict_max(
        result,
        "pb_ratio",
        3.0
    )

    result = _strict_max(
        result,
        "debt_to_equity",
        2.0
    )

    result = _strict_min(
        result,
        "dividend_yield_pct",
        1
    )

    return _sort(result)


def growth_accelerator(df):
    """
    Growth Accelerator

    Requirements:
    - PAT CAGR 5yr > 20%
    - Revenue CAGR 5yr > 15%
    - D/E < 2.0
    """

    result = _latest_per_company(df)

    result = _strict_min(
        result,
        "pat_cagr_5yr",
        20
    )

    result = _strict_min(
        result,
        "revenue_cagr_5yr",
        15
    )

    result = _strict_max(
        result,
        "debt_to_equity",
        2.0
    )

    return _sort(result)


def dividend_champion(df):
    """
    Dividend Champion

    Requirements:
    - Dividend Yield > 2%
    - Dividend Payout < 80%
    - FCF > 0
    """

    result = _latest_per_company(df)

    result = _strict_min(
        result,
        "dividend_yield_pct",
        2
    )

    result = _strict_max(
        result,
        "dividend_payout_ratio_pct",
        80
    )

    result = _strict_min(
        result,
        "free_cash_flow_cr",
        0
    )

    return _sort(result)


def debt_free_blue_chip(df):
    """
    Debt-Free Blue Chip

    Requirements:
    - D/E = 0
    - ROE > 12%
    - Revenue > 5000 Crore
    """

    result = _latest_per_company(df)

    result = result[
        result["debt_to_equity"].notna()
        & (result["debt_to_equity"] == 0)
    ].copy()

    result = _strict_min(
        result,
        "return_on_equity_pct",
        12
    )

    result = _strict_min(
        result,
        "sales",
        5000
    )

    return _sort(result)


def _calculate_revenue_cagr_3yr():
    """
    Calculate 3-year revenue CAGR using the latest available year
    and the year three years before it.

    CAGR = ((latest / prior) ** (1 / 3) - 1) * 100
    """

    connection = sqlite3.connect(DB_PATH)

    sales = pd.read_sql_query(
        """
        SELECT company_id, year, sales
        FROM profitandloss
        """,
        connection
    )

    connection.close()

    sales["year"] = pd.to_numeric(
        sales["year"],
        errors="coerce"
    )

    sales["sales"] = pd.to_numeric(
        sales["sales"],
        errors="coerce"
    )

    sales = sales.dropna(
        subset=["company_id", "year", "sales"]
    ).copy()

    sales["year"] = sales["year"].astype(int)

    latest_year = sales["year"].max()
    prior_year = latest_year - 3

    latest = (
        sales[sales["year"] == latest_year]
        .drop_duplicates("company_id", keep="last")
        .set_index("company_id")["sales"]
    )

    prior = (
        sales[sales["year"] == prior_year]
        .drop_duplicates("company_id", keep="last")
        .set_index("company_id")["sales"]
    )

    combined = pd.concat(
        [
            latest.rename("latest_sales"),
            prior.rename("prior_sales"),
        ],
        axis=1
    )

    valid = (
        combined["latest_sales"].notna()
        & combined["prior_sales"].notna()
        & (combined["latest_sales"] > 0)
        & (combined["prior_sales"] > 0)
    )

    cagr = pd.Series(
        index=combined.index,
        dtype=float
    )

    cagr.loc[valid] = (
        (
            combined.loc[valid, "latest_sales"]
            / combined.loc[valid, "prior_sales"]
        ) ** (1 / 3)
        - 1
    ) * 100

    return cagr


def _calculate_de_declining():
    """
    Identify companies whose latest D/E is lower than the
    immediately preceding year's D/E.

    This is a strict year-over-year comparison.
    """

    connection = sqlite3.connect(DB_PATH)

    de = pd.read_sql_query(
        """
        SELECT company_id, year, debt_to_equity
        FROM financial_ratios
        """,
        connection
    )

    connection.close()

    de["year"] = pd.to_numeric(
        de["year"],
        errors="coerce"
    )

    de["debt_to_equity"] = pd.to_numeric(
        de["debt_to_equity"],
        errors="coerce"
    )

    de = de.dropna(
        subset=["company_id", "year"]
    ).copy()

    de["year"] = de["year"].astype(int)

    latest_year = de["year"].max()
    previous_year = latest_year - 1

    latest = (
        de[de["year"] == latest_year]
        .drop_duplicates("company_id", keep="last")
        .set_index("company_id")["debt_to_equity"]
    )

    previous = (
        de[de["year"] == previous_year]
        .drop_duplicates("company_id", keep="last")
        .set_index("company_id")["debt_to_equity"]
    )

    combined = pd.concat(
        [
            latest.rename("latest_de"),
            previous.rename("previous_de"),
        ],
        axis=1
    )

    return (
        combined["latest_de"].notna()
        & combined["previous_de"].notna()
        & (combined["latest_de"] < combined["previous_de"])
    )


def turnaround_watch(df):
    """
    Turnaround Watch

    Requirements:
    - Revenue CAGR 3yr > 10%
    - FCF positive in latest year
    - D/E declining year-over-year
    """

    result = _latest_per_company(df)

    revenue_cagr_3yr = _calculate_revenue_cagr_3yr()

    result["revenue_cagr_3yr"] = result["company_id"].map(
        revenue_cagr_3yr
    )

    result = result[
        result["revenue_cagr_3yr"].notna()
        & (result["revenue_cagr_3yr"] > 10)
    ].copy()

    result = result[
        result["free_cash_flow_cr"].notna()
        & (result["free_cash_flow_cr"] > 0)
    ].copy()

    de_declining = _calculate_de_declining()

    result = result[
        result["company_id"]
        .map(de_declining)
        .fillna(False)
    ].copy()

    return _sort(result)


PRESETS = {
    "Quality Compounder": quality_compounder,
    "Value Pick": value_pick,
    "Growth Accelerator": growth_accelerator,
    "Dividend Champion": dividend_champion,
    "Debt-Free Blue Chip": debt_free_blue_chip,
    "Turnaround Watch": turnaround_watch,
}


def run_preset(name):
    """
    Run one Day 16 preset on the 92-company universe.
    """

    if name not in PRESETS:
        raise ValueError(
            f"Unknown preset: {name}. "
            f"Available presets: {', '.join(PRESETS)}"
        )

    df = load_data()

    return PRESETS[name](df)


def run_all_presets():
    """
    Run all six Day 16 presets on the 92-company universe.
    """

    df = load_data()

    return {
        name: function(df)
        for name, function in PRESETS.items()
    }
