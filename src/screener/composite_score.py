import sqlite3

import numpy as np
import pandas as pd


def winsorised_score(series, higher_is_better=True):
    """
    Convert a financial metric into a 0-100 score.

    Values below P10 are capped at P10.
    Values above P90 are capped at P90.
    The capped values are then scaled to 0-100.
    """

    values = pd.to_numeric(series, errors="coerce")
    valid_values = values.dropna()

    if valid_values.empty:
        return pd.Series(
            np.nan,
            index=series.index,
            dtype=float
        )

    p10 = valid_values.quantile(0.10)
    p90 = valid_values.quantile(0.90)

    if p10 == p90:
        return pd.Series(
            50.0,
            index=series.index,
            dtype=float
        )

    capped = values.clip(
        lower=p10,
        upper=p90
    )

    if higher_is_better:
        return (
            (capped - p10)
            / (p90 - p10)
            * 100
        )

    return (
        (p90 - capped)
        / (p90 - p10)
        * 100
    )


def calculate_cfo_pat_ratio(cfo, pat):
    """
    Calculate CFO/PAT.

    Returns NaN when CFO or PAT is missing,
    or when PAT is zero.
    """

    cfo = pd.to_numeric(cfo, errors="coerce")
    pat = pd.to_numeric(pat, errors="coerce")

    if pd.isna(cfo) or pd.isna(pat):
        return np.nan

    if pat == 0:
        return np.nan

    return cfo / pat


def calculate_fcf_cagr(current_fcf, previous_fcf, years=5):
    """
    Calculate five-year FCF CAGR.

    CAGR is calculated only when both endpoint
    FCF values are positive.
    """

    if pd.isna(current_fcf) or pd.isna(previous_fcf):
        return np.nan

    if current_fcf <= 0 or previous_fcf <= 0:
        return np.nan

    return (
        (
            current_fcf / previous_fcf
        ) ** (1 / years)
        - 1
    ) * 100


def add_historical_fcf_cagr(df, db_path):
    """
    Calculate five-year FCF CAGR from historical
    financial_ratios data.

    For each company, the latest available FCF is
    compared with the FCF from five years earlier.
    """

    result = df.copy()

    connection = sqlite3.connect(db_path)

    history = pd.read_sql_query(
        """
        SELECT
            company_id,
            year,
            free_cash_flow_cr
        FROM financial_ratios
        """,
        connection
    )

    connection.close()

    history["year"] = pd.to_numeric(
        history["year"],
        errors="coerce"
    )

    history["free_cash_flow_cr"] = pd.to_numeric(
        history["free_cash_flow_cr"],
        errors="coerce"
    )

    history = history.dropna(
        subset=[
            "company_id",
            "year"
        ]
    ).copy()

    history["year"] = history["year"].astype(int)

    history = (
        history
        .sort_values(
            ["company_id", "year"]
        )
        .drop_duplicates(
            ["company_id", "year"],
            keep="last"
        )
    )

    latest = (
        history
        .sort_values(
            ["company_id", "year"]
        )
        .drop_duplicates(
            "company_id",
            keep="last"
        )
        .copy()
    )

    latest["previous_year"] = latest["year"] - 5

    previous = history.rename(
        columns={
            "year": "previous_year",
            "free_cash_flow_cr": "previous_fcf"
        }
    )

    merged = latest.merge(
        previous[
            [
                "company_id",
                "previous_year",
                "previous_fcf"
            ]
        ],
        on=[
            "company_id",
            "previous_year"
        ],
        how="left"
    )

    merged["fcf_cagr_5yr"] = merged.apply(
        lambda row: calculate_fcf_cagr(
            row["free_cash_flow_cr"],
            row["previous_fcf"]
        ),
        axis=1
    )

    fcf_cagr = (
        merged
        .set_index("company_id")["fcf_cagr_5yr"]
    )

    result["fcf_cagr_5yr"] = result["company_id"].map(
        fcf_cagr
    )

    return result


def calculate_sector_relative_score(df, db_path=None):
    """
    Calculate the Day 17 sector-relative composite quality score.

    Profitability = 35%
        ROE  = 15%
        ROCE = 10%
        NPM  = 10%

    Cash Quality = 30%
        FCF CAGR     = 15%
        CFO/PAT      = 10%
        FCF positive = 5%

    Growth = 20%
        Revenue CAGR = 10%
        PAT CAGR     = 10%

    Leverage = 15%
        D/E = 10%
        ICR = 5%

    Each continuous metric is normalised within its
    broad sector using P10/P90 winsorisation.
    """

    result = df.copy()

    required_columns = [
        "company_id",
        "broad_sector",
        "return_on_equity_pct",
        "roce_percentage",
        "net_profit_margin_pct",
        "free_cash_flow_cr",
        "cash_from_operations_cr",
        "net_profit",
        "revenue_cagr_5yr",
        "pat_cagr_5yr",
        "debt_to_equity",
        "interest_coverage"
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in result.columns
    ]

    if missing_columns:
        raise KeyError(
            "Missing columns required for Day 17 composite score: "
            + ", ".join(missing_columns)
        )

    if db_path is not None:
        result = add_historical_fcf_cagr(
            result,
            db_path
        )
    elif "fcf_cagr_5yr" not in result.columns:
        result["fcf_cagr_5yr"] = np.nan

    result["cfo_pat_ratio"] = result.apply(
        lambda row: calculate_cfo_pat_ratio(
            row["cash_from_operations_cr"],
            row["net_profit"]
        ),
        axis=1
    )

    result["fcf_positive_flag"] = np.where(
        result["free_cash_flow_cr"].notna()
        & (result["free_cash_flow_cr"] > 0),
        1,
        0
    )

    metrics = {
        "return_on_equity_pct": True,
        "roce_percentage": True,
        "net_profit_margin_pct": True,
        "fcf_cagr_5yr": True,
        "cfo_pat_ratio": True,
        "revenue_cagr_5yr": True,
        "pat_cagr_5yr": True,
        "debt_to_equity": False,
        "interest_coverage": True
    }

    for metric, higher_is_better in metrics.items():
        score_column = f"sector_score_{metric}"

        result[score_column] = np.nan

        for sector, indexes in result.groupby(
            "broad_sector",
            dropna=False
        ).groups.items():

            sector_values = result.loc[
                indexes,
                metric
            ]

            result.loc[
                indexes,
                score_column
            ] = winsorised_score(
                sector_values,
                higher_is_better
            )

    result["sector_score_fcf_positive"] = (
        result["fcf_positive_flag"] * 100
    )

    result["profitability_score"] = (
        result["sector_score_return_on_equity_pct"] * 0.15
        + result["sector_score_roce_percentage"] * 0.10
        + result["sector_score_net_profit_margin_pct"] * 0.10
    )

    result["cash_quality_score"] = (
        result["sector_score_fcf_cagr_5yr"] * 0.15
        + result["sector_score_cfo_pat_ratio"] * 0.10
        + result["sector_score_fcf_positive"] * 0.05
    )

    result["growth_score"] = (
        result["sector_score_revenue_cagr_5yr"] * 0.10
        + result["sector_score_pat_cagr_5yr"] * 0.10
    )

    result["leverage_score"] = (
        result["sector_score_debt_to_equity"] * 0.10
        + result["sector_score_interest_coverage"] * 0.05
    )

    result["composite_quality_score"] = (
        result["profitability_score"]
        + result["cash_quality_score"]
        + result["growth_score"]
        + result["leverage_score"]
    )

    result["composite_quality_score"] = (
        result["composite_quality_score"]
        .clip(0, 100)
        .round(2)
    )

    result = result.sort_values(
        by="composite_quality_score",
        ascending=False,
        na_position="last"
    ).reset_index(drop=True)

    return result
