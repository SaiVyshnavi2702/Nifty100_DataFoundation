import sqlite3

import pandas as pd

from src.screener.engine import DB_PATH, load_data


def _get_92_company_universe():
    """Return the 92 companies present in the sectors table."""
    connection = sqlite3.connect(DB_PATH)

    rows = connection.execute("SELECT DISTINCT company_id FROM sectors").fetchall()

    connection.close()

    return {row[0] for row in rows}


def _latest_per_company(df):
    """Keep only the latest financial-ratio row for each company."""
    result = df.copy()

    universe = _get_92_company_universe()

    result = result[result["company_id"].isin(universe)].copy()

    result["_year_sort"] = pd.to_numeric(result["year"], errors="coerce")

    result = (
        result.sort_values(["company_id", "_year_sort"], ascending=[True, False])
        .drop_duplicates("company_id", keep="first")
        .drop(columns="_year_sort")
    )

    return result


def _strict_min(df, column, threshold):
    """Keep values strictly greater than the threshold."""
    return df[df[column].notna() & (df[column] > threshold)]


def _strict_max(df, column, threshold):
    """Keep values strictly less than the threshold."""
    return df[df[column].notna() & (df[column] < threshold)]


def _de_max(df, threshold):
    """Apply strict D/E maximum."""
    return df[df["debt_to_equity"].notna() & (df["debt_to_equity"] < threshold)]


def _sort(df):
    """Sort by Day 15 composite quality score."""
    return df.sort_values(
        by="composite_quality_score", ascending=False, na_position="last"
    ).reset_index(drop=True)


def quality_compounder(df):
    """
    Quality Compounder:
    ROE > 15%
    D/E < 1.0
    FCF > 0
    Revenue CAGR 5yr > 10%
    """
    result = _latest_per_company(df)

    result = _strict_min(result, "return_on_equity_pct", 15)

    result = _de_max(result, 1.0)

    result = _strict_min(result, "free_cash_flow_cr", 0)

    result = _strict_min(result, "revenue_cagr_5yr", 10)

    return _sort(result)


def value_pick(df):
    """
    Value Pick:
    P/E < 20
    P/B < 3.0
    D/E < 2.0
    Dividend Yield > 1%
    """
    result = _latest_per_company(df)

    result = _strict_max(result, "pe_ratio", 20)

    result = _strict_max(result, "pb_ratio", 3.0)

    result = _de_max(result, 2.0)

    result = _strict_min(result, "dividend_yield_pct", 1)

    return _sort(result)


def growth_accelerator(df):
    """
    Growth Accelerator:
    PAT CAGR 5yr > 20%
    Revenue CAGR 5yr > 15%
    D/E < 2.0
    """
    result = _latest_per_company(df)

    result = _strict_min(result, "pat_cagr_5yr", 20)

    result = _strict_min(result, "revenue_cagr_5yr", 15)

    result = _de_max(result, 2.0)

    return _sort(result)


def dividend_champion(df):
    """
    Dividend Champion:
    Dividend Yield > 2%
    Dividend Payout < 80%
    FCF > 0
    """
    result = _latest_per_company(df)

    result = _strict_min(result, "dividend_yield_pct", 2)

    result = _strict_max(result, "dividend_payout_ratio_pct", 80)

    result = _strict_min(result, "free_cash_flow_cr", 0)

    return _sort(result)


def debt_free_blue_chip(df):
    """
    Debt-Free Blue Chip:
    D/E = 0
    ROE > 12%
    Revenue > 5000 Crore
    """
    result = _latest_per_company(df)

    result = result[result["debt_to_equity"].notna() & (result["debt_to_equity"] == 0)]

    result = _strict_min(result, "return_on_equity_pct", 12)

    result = _strict_min(result, "sales", 5000)

    return _sort(result)


def _calculate_revenue_cagr_3yr():
    """
    Calculate 3-year revenue CAGR using 2021 -> 2024 sales.
    """
    connection = sqlite3.connect(DB_PATH)

    query = """
        SELECT company_id, year, sales
        FROM profitandloss
        WHERE year IN (2021, 2024)
    """

    sales = pd.read_sql_query(query, connection)

    connection.close()

    sales = sales.dropna(subset=["sales"])

    sales["year"] = sales["year"].astype(int)

    pivot = sales.pivot_table(
        index="company_id", columns="year", values="sales", aggfunc="last"
    )

    if 2021 not in pivot.columns or 2024 not in pivot.columns:
        return pd.Series(dtype=float)

    valid = (
        pivot[2021].notna()
        & pivot[2024].notna()
        & (pivot[2021] > 0)
        & (pivot[2024] > 0)
    )

    cagr = pd.Series(index=pivot.index, dtype=float)

    cagr.loc[valid] = (
        (pivot.loc[valid, 2024] / pivot.loc[valid, 2021]) ** (1 / 3) - 1
    ) * 100

    return cagr


def _calculate_de_declining():
    """
    Identify companies whose 2024 D/E is lower than 2023 D/E.
    """
    connection = sqlite3.connect(DB_PATH)

    query = """
        SELECT company_id, year, debt_to_equity
        FROM financial_ratios
        WHERE year IN (2023, 2024)
    """

    de = pd.read_sql_query(query, connection)

    connection.close()

    de["year"] = de["year"].astype(int)

    pivot = de.pivot_table(
        index="company_id", columns="year", values="debt_to_equity", aggfunc="last"
    )

    if 2023 not in pivot.columns or 2024 not in pivot.columns:
        return pd.Series(dtype=bool)

    return pivot[2023].notna() & pivot[2024].notna() & (pivot[2024] < pivot[2023])


def turnaround_watch(df):
    """
    Turnaround Watch:
    Revenue CAGR 3yr > 10%
    Latest-year FCF > 0
    D/E declining year-over-year
    """
    result = _latest_per_company(df)

    revenue_cagr_3yr = _calculate_revenue_cagr_3yr()

    result["revenue_cagr_3yr"] = result["company_id"].map(revenue_cagr_3yr)

    result = result[
        result["revenue_cagr_3yr"].notna() & (result["revenue_cagr_3yr"] > 10)
    ]

    result = result[
        result["free_cash_flow_cr"].notna() & (result["free_cash_flow_cr"] > 0)
    ]

    de_declining = _calculate_de_declining()

    result = result[result["company_id"].map(de_declining).fillna(False)]

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
    """Run one Day 16 preset on the 92-company universe."""
    if name not in PRESETS:
        raise ValueError(
            f"Unknown preset: {name}. " f"Available presets: {', '.join(PRESETS)}"
        )

    df = load_data()

    return PRESETS[name](df)


def run_all_presets():
    """Run all six Day 16 presets on the 92-company universe."""
    df = load_data()

    return {name: function(df) for name, function in PRESETS.items()}
