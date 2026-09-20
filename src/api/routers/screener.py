
import sqlite3
from pathlib import Path

from fastapi import APIRouter, Query, HTTPException

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parents[3]
DB_PATH = BASE_DIR / "data" / "nifty100.db"


@router.get("/screener")
def screen_companies(
    min_roe: str | None = Query(default=None),
    max_de: str | None = Query(default=None),
    min_fcf: str | None = Query(default=None),
    sector: str | None = Query(default=None),
    min_rev_cagr_5yr: str | None = Query(default=None),
    min_pat_cagr_5yr: str | None = Query(default=None),
    max_pe: str | None = Query(default=None),
):
    # Convert filter values to numbers and validate them
    def parse_number(value, parameter_name):
        if value is None:
            return None

        try:
            number = float(value)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"{parameter_name} must be a valid number",
            )

        if number < 0:
            raise HTTPException(
                status_code=400,
                detail=f"{parameter_name} cannot be negative",
            )

        return number

    min_roe = parse_number(min_roe, "min_roe")
    max_de = parse_number(max_de, "max_de")
    min_fcf = parse_number(min_fcf, "min_fcf")
    min_rev_cagr_5yr = parse_number(
        min_rev_cagr_5yr,
        "min_rev_cagr_5yr",
    )
    min_pat_cagr_5yr = parse_number(
        min_pat_cagr_5yr,
        "min_pat_cagr_5yr",
    )
    max_pe = parse_number(max_pe, "max_pe")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    query = """
        SELECT
            c.id AS ticker,
            c.company_name,
            s.broad_sector,
            s.sub_sector,
            r.year,
            r.return_on_equity_pct AS roe_pct,
            r.debt_to_equity AS de,
            r.free_cash_flow_cr AS fcf_cr,
            r.revenue_cagr_5yr AS rev_cagr_5yr,
            r.pat_cagr_5yr AS pat_cagr_5yr,
            m.pe_ratio AS pe,
            r.net_profit_margin_pct,
            r.operating_profit_margin_pct,
            r.interest_coverage,
            r.asset_turnover,
            r.eps_cagr_5yr,
            r.composite_quality_score
        FROM companies c
        INNER JOIN sectors s
            ON s.company_id = c.id
        INNER JOIN financial_ratios r
            ON r.company_id = c.id
        LEFT JOIN market_cap m
            ON m.company_id = c.id
            AND m.year = r.year
        WHERE r.year = (
            SELECT MAX(r2.year)
            FROM financial_ratios r2
            WHERE r2.company_id = c.id
        )
    """

    params = []

    if min_roe is not None:
        query += " AND r.return_on_equity_pct >= ?"
        params.append(min_roe)

    if max_de is not None:
        query += " AND r.debt_to_equity <= ?"
        params.append(max_de)

    if min_fcf is not None:
        query += " AND r.free_cash_flow_cr >= ?"
        params.append(min_fcf)

    if sector:
        query += " AND s.broad_sector = ?"
        params.append(sector)

    if min_rev_cagr_5yr is not None:
        query += " AND r.revenue_cagr_5yr >= ?"
        params.append(min_rev_cagr_5yr)

    if min_pat_cagr_5yr is not None:
        query += " AND r.pat_cagr_5yr >= ?"
        params.append(min_pat_cagr_5yr)

    if max_pe is not None:
        query += " AND m.pe_ratio <= ?"
        params.append(max_pe)

    # Rank companies by quality score, then ROE
    query += """
        ORDER BY
            r.composite_quality_score DESC,
            r.return_on_equity_pct DESC,
            c.id
    """

    rows = conn.execute(query, params).fetchall()

    conn.close()

    return [dict(row) for row in rows]