import sqlite3
from pathlib import Path

import pandas as pd
import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "data" / "nifty100.db"
CONFIG_PATH = PROJECT_ROOT / "config" / "screener_config.yaml"


def load_config():
    """Load screener thresholds from the YAML configuration file."""

    with open(CONFIG_PATH, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def load_data():
    """Load financial data required by the screener."""

    connection = sqlite3.connect(DB_PATH)

    query = """
        SELECT
            fr.*,
            mc.market_cap_crore,
            mc.pe_ratio,
            mc.pb_ratio,
            mc.dividend_yield_pct,
            pl.sales,
            pl.net_profit,
            s.broad_sector,
            CASE
                WHEN EXISTS (
                    SELECT 1
                    FROM prosandcons pc
                    WHERE pc.company_id = fr.company_id
                      AND LOWER(pc.pros) LIKE '%debt free%'
                )
                THEN 1
                ELSE 0
            END AS debt_free
        FROM financial_ratios fr

        LEFT JOIN market_cap mc
            ON mc.company_id = fr.company_id
            AND mc.year = (
                SELECT MAX(mc2.year)
                FROM market_cap mc2
                WHERE mc2.company_id = fr.company_id
            )

        LEFT JOIN profitandloss pl
            ON pl.company_id = fr.company_id
            AND pl.year = (
                SELECT MAX(pl2.year)
                FROM profitandloss pl2
                WHERE pl2.company_id = fr.company_id
            )

        LEFT JOIN sectors s
            ON s.company_id = fr.company_id
    """

    df = pd.read_sql_query(query, connection)

    connection.close()

    return df


def apply_min_filter(df, column, threshold):
    """Keep rows where the selected metric is greater than or equal to the threshold."""

    if threshold is None:
        return df

    return df[
        df[column].notna()
        & (df[column] >= threshold)
    ]


def apply_max_filter(df, column, threshold):
    """Keep rows where the selected metric is less than or equal to the threshold."""

    if threshold is None:
        return df

    return df[
        df[column].notna()
        & (df[column] <= threshold)
    ]


def apply_filters(df, filters):
    """Apply all configured screener filters."""

    result = df.copy()

    # 1. ROE minimum
    result = apply_min_filter(
        result,
        "return_on_equity_pct",
        filters.get("roe_min")
    )

    # 2. D/E maximum
    # Financials companies are exempt from the D/E filter.
    de_max = filters.get("debt_to_equity_max")

    if de_max is not None:
        financials = (
            result["broad_sector"]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.lower()
            .eq("financials")
        )

        result = result[
            financials
            | (
                result["debt_to_equity"].notna()
                & (result["debt_to_equity"] <= de_max)
            )
        ]

    # 3. Free Cash Flow minimum
    result = apply_min_filter(
        result,
        "free_cash_flow_cr",
        filters.get("free_cash_flow_min")
    )

    # 4. Revenue CAGR 5yr minimum
    result = apply_min_filter(
        result,
        "revenue_cagr_5yr",
        filters.get("revenue_cagr_5yr_min")
    )

        # 5. PAT CAGR 5yr minimum
    result = apply_min_filter(
        result,
        "pat_cagr_5yr",
        filters.get("pat_cagr_5yr_min")
    )


    # 6. Operating Profit Margin minimum
    result = apply_min_filter(
        result,
        "operating_profit_margin_pct",
        filters.get("operating_profit_margin_min")
    )

    # 7. P/E maximum
    result = apply_max_filter(
        result,
        "pe_ratio",
        filters.get("pe_ratio_max")
    )

    # 8. P/B maximum
    result = apply_max_filter(
        result,
        "pb_ratio",
        filters.get("pb_ratio_max")
    )

    # 9. Dividend Yield minimum
    result = apply_min_filter(
        result,
        "dividend_yield_pct",
        filters.get("dividend_yield_min")
    )

    # 10. ICR minimum
    # Debt Free companies are treated as having infinite ICR.
    icr_min = filters.get("interest_coverage_min")

    if icr_min is not None:
        debt_free = result["debt_free"] == 1

        result = result[
            debt_free
            | (
                result["interest_coverage"].notna()
                & (result["interest_coverage"] >= icr_min)
            )
        ]

    # 11. Market Cap minimum
    result = apply_min_filter(
        result,
        "market_cap_crore",
        filters.get("market_cap_min")
    )

    # 12. Net Profit minimum
    result = apply_min_filter(
        result,
        "net_profit",
        filters.get("net_profit_min")
    )

    # 13. EPS CAGR minimum
    result = apply_min_filter(
        result,
        "eps_cagr_5yr",
        filters.get("eps_cagr_min")
    )

    # 14. Asset Turnover minimum
    result = apply_min_filter(
        result,
        "asset_turnover",
        filters.get("asset_turnover_min")
    )

    # 15. Sales minimum
    result = apply_min_filter(
        result,
        "sales",
        filters.get("sales_min")
    )

    # Make sure the quality score is present.
    if "composite_quality_score" not in result.columns:
        raise KeyError(
            "composite_quality_score column is missing from financial_ratios."
        )

    # Return highest-quality companies first.
    result = result.sort_values(
        by="composite_quality_score",
        ascending=False,
        na_position="last"
    ).reset_index(drop=True)

    return result


def run_screener(filters=None):
    """Load the data, apply the configured filters and return the result."""

    config = load_config()
    df = load_data()

    if filters is None:
        filters = config.get("filters", {})

    return apply_filters(df, filters)


if __name__ == "__main__":
    result = run_screener()

    print("Day 15 Screener Engine")
    print("----------------------")
    print("Rows returned:", len(result))

    if not result.empty:
        print()
        print(
            result[
                [
                    "company_id",
                    "composite_quality_score"
                ]
            ].head(10).to_string(index=False)
        )
