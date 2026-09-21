import sqlite3
from pathlib import Path
from statistics import quantiles

from fastapi import APIRouter

router = APIRouter()


BASE_DIR = Path(__file__).resolve().parents[3]

DB_PATH = BASE_DIR / "data" / "nifty100.db"


@router.get("/portfolio/stats")
def get_portfolio_stats():
    """Retrieve portfolio stats."""
    conn = sqlite3.connect(DB_PATH)

    conn.row_factory = sqlite3.Row

    query = """
        SELECT
            r.company_id,
            r.net_profit_margin_pct,
            r.operating_profit_margin_pct,
            r.return_on_equity_pct,
            r.debt_to_equity,
            r.interest_coverage,
            r.asset_turnover,
            r.free_cash_flow_cr,
            r.capex_cr,
            r.earnings_per_share,
            r.book_value_per_share
        FROM financial_ratios r
        INNER JOIN sectors s
            ON s.company_id = r.company_id
        WHERE r.year = (
            SELECT MAX(r2.year)
            FROM financial_ratios r2
            WHERE r2.company_id = r.company_id
        )
        ORDER BY r.company_id
    """

    rows = conn.execute(query).fetchall()

    conn.close()

    kpis = {
        "net_profit_margin_pct": [],
        "operating_profit_margin_pct": [],
        "return_on_equity_pct": [],
        "debt_to_equity": [],
        "interest_coverage": [],
        "asset_turnover": [],
        "free_cash_flow_cr": [],
        "capex_cr": [],
        "earnings_per_share": [],
        "book_value_per_share": [],
    }

    for row in rows:
        for kpi, values in kpis.items():
            value = row[kpi]

            if value is not None:
                values.append(value)

    result = []

    for kpi, values in kpis.items():
        if not values:
            continue

        if len(values) == 1:
            p10 = p25 = p50 = p75 = p90 = values[0]

        else:
            q = quantiles(values, n=100, method="inclusive")

            p10 = q[9]
            p25 = q[24]
            p50 = q[49]
            p75 = q[74]
            p90 = q[89]

        result.append(
            {
                "kpi": kpi,
                "p10": round(p10, 2),
                "p25": round(p25, 2),
                "p50": round(p50, 2),
                "p75": round(p75, 2),
                "p90": round(p90, 2),
            }
        )

    return {
        "company_count": len(rows),
        "kpi_count": len(result),
        "statistics": result,
    }
