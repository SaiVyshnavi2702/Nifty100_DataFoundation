import sqlite3
from pathlib import Path
from statistics import median

from fastapi import APIRouter

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parents[3]
DB_PATH = BASE_DIR / "data" / "nifty100.db"

@router.get("/sectors")
def get_sectors():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    query = """
        SELECT
            s.broad_sector,
            s.company_id,
            r.return_on_equity_pct AS roe,
            m.pe_ratio AS pe,
            r.debt_to_equity AS de
        FROM sectors s
        LEFT JOIN financial_ratios r
            ON r.company_id = s.company_id
            AND r.year = (
                SELECT MAX(r2.year)
                FROM financial_ratios r2
                WHERE r2.company_id = s.company_id
            )
        LEFT JOIN market_cap m
            ON m.company_id = s.company_id
            AND m.year = (
                SELECT MAX(m2.year)
                FROM market_cap m2
                WHERE m2.company_id = s.company_id
            )
        ORDER BY s.broad_sector, s.company_id
    """

    rows = conn.execute(query).fetchall()

    conn.close()

    sector_data = {}

    for row in rows:
        sector = row["broad_sector"]

        if sector not in sector_data:
            sector_data[sector] = {
                "companies": 0,
                "roe": [],
                "pe": [],
                "de": [],
            }

        sector_data[sector]["companies"] += 1

        if row["roe"] is not None:
            sector_data[sector]["roe"].append(row["roe"])

        if row["pe"] is not None:
            sector_data[sector]["pe"].append(row["pe"])

        if row["de"] is not None:
            sector_data[sector]["de"].append(row["de"])

    result = []

    for sector, data in sector_data.items():
        result.append(
            {
                "sector": sector,
                "company_count": data["companies"],
                "median_roe": (
                    round(median(data["roe"]), 2)
                    if data["roe"]
                    else None
                ),
                "median_pe": (
                    round(median(data["pe"]), 2)
                    if data["pe"]
                    else None
                ),
                "median_de": (
                    round(median(data["de"]), 2)
                    if data["de"]
                    else None
                ),
            }
        )

    return result


@router.get("/sectors/{sector}/companies")
def get_sector_companies(sector: str):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    query = """
        SELECT
            c.id AS ticker,
            c.company_name,
            s.broad_sector,
            s.sub_sector,
            r.year AS latest_year,
            r.net_profit_margin_pct,
            r.operating_profit_margin_pct,
            r.return_on_equity_pct,
            r.debt_to_equity,
            r.interest_coverage,
            r.asset_turnover,
            r.free_cash_flow_cr,
            r.capex_cr,
            r.earnings_per_share,
            r.book_value_per_share,
            r.dividend_payout_ratio_pct,
            r.total_debt_cr,
            r.cash_from_operations_cr,
            r.revenue_cagr_5yr,
            r.pat_cagr_5yr,
            r.eps_cagr_5yr,
            r.composite_quality_score
        FROM companies c
        INNER JOIN sectors s
            ON s.company_id = c.id
        LEFT JOIN financial_ratios r
            ON r.company_id = c.id
            AND r.year = (
                SELECT MAX(r2.year)
                FROM financial_ratios r2
                WHERE r2.company_id = c.id
            )
        WHERE s.broad_sector = ?
        ORDER BY c.id
    """

    rows = conn.execute(query, (sector,)).fetchall()

    conn.close()

    if not rows:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=404,
            detail="Sector not found",
        )

    return [dict(row) for row in rows]