import sqlite3
from pathlib import Path

from fastapi import APIRouter, HTTPException

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parents[3]
DB_PATH = BASE_DIR / "data" / "nifty100.db"

@router.get("/peers/{group_name}")
def get_peer_group(group_name: str):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    group_query = """
        SELECT
            pg.peer_group_name,
            pg.company_id,
            pg.is_benchmark
        FROM peer_groups pg
        WHERE pg.peer_group_name = ?
        ORDER BY pg.is_benchmark DESC, pg.company_id
    """

    group_rows = conn.execute(
        group_query,
        (group_name,),
    ).fetchall()

    if not group_rows:
        conn.close()
        raise HTTPException(
            status_code=404,
            detail="Peer group not found",
        )

    companies = []

    for group_row in group_rows:
        company_id = group_row["company_id"]

        percentile_query = """
            SELECT
                metric,
                value,
                percentile_rank,
                year
            FROM peer_percentiles
            WHERE company_id = ?
              AND peer_group_name = ?
              AND year = (
                  SELECT MAX(p2.year)
                  FROM peer_percentiles p2
                  WHERE p2.company_id = peer_percentiles.company_id
                    AND p2.peer_group_name = peer_percentiles.peer_group_name
                    AND p2.metric = peer_percentiles.metric
              )
            ORDER BY metric
        """

        percentile_rows = conn.execute(
            percentile_query,
            (company_id, group_name),
        ).fetchall()

        metrics = {}

        for row in percentile_rows:
            metrics[row["metric"]] = {
                "value": row["value"],
                "percentile_rank": row["percentile_rank"],
                "year": row["year"],
            }

        companies.append(
            {
                "company_id": company_id,
                "is_benchmark": bool(group_row["is_benchmark"]),
                "metrics": metrics,
            }
        )

    conn.close()

    return {
        "peer_group": group_name,
        "company_count": len(companies),
        "companies": companies,
    }

@router.get("/companies/{ticker}/peers/compare")
def compare_company_with_peers(ticker: str):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # Find the company's peer group
    company_query = """
        SELECT
            pg.peer_group_name,
            pg.company_id,
            pg.is_benchmark
        FROM peer_groups pg
        WHERE UPPER(pg.company_id) = UPPER(?)
    """

    company_row = conn.execute(
        company_query,
        (ticker,),
    ).fetchone()

    if not company_row:
        conn.close()
        raise HTTPException(
            status_code=404,
            detail="Company peer group not found",
        )

    peer_group = company_row["peer_group_name"]

    # Get all companies in the same peer group
    peers_query = """
        SELECT
            company_id,
            is_benchmark
        FROM peer_groups
        WHERE peer_group_name = ?
    """

    peer_rows = conn.execute(
        peers_query,
        (peer_group,),
    ).fetchall()

    # Eight radar metrics
    radar_metrics = [
        "ROE",
        "ROCE",
        "Revenue CAGR 5yr",
        "PAT CAGR 5yr",
        "EPS CAGR 5yr",
        "Net Profit Margin",
        "FCF",
        "Asset Turnover",
    ]

    # Get latest value for each metric for every peer
    values_query = """
        SELECT
            company_id,
            metric,
            value,
            year
        FROM peer_percentiles
        WHERE peer_group_name = ?
          AND metric IN (
              'ROE',
              'ROCE',
              'Revenue CAGR 5yr',
              'PAT CAGR 5yr',
              'EPS CAGR 5yr',
              'Net Profit Margin',
              'FCF',
              'Asset Turnover'
          )
          AND year = (
              SELECT MAX(p2.year)
              FROM peer_percentiles p2
              WHERE p2.company_id = peer_percentiles.company_id
                AND p2.peer_group_name = peer_percentiles.peer_group_name
                AND p2.metric = peer_percentiles.metric
          )
    """

    value_rows = conn.execute(
        values_query,
        (peer_group,),
    ).fetchall()

    conn.close()

    # Organize values by company
    company_values = {}

    for row in value_rows:
        company_id = row["company_id"]

        if company_id not in company_values:
            company_values[company_id] = {}

        company_values[company_id][row["metric"]] = row["value"]

    # Find benchmark company
    benchmark_company = None

    for peer in peer_rows:
        if peer["is_benchmark"]:
            benchmark_company = peer["company_id"]
            break

    # Build radar data
    radar_data = []

    for metric in radar_metrics:
        peer_values = []

        for peer in peer_rows:
            value = company_values.get(peer["company_id"], {}).get(metric)

            if value is not None:
                peer_values.append(value)

        company_value = company_values.get(
            company_row["company_id"],
            {},
        ).get(metric)

        benchmark_value = None

        if benchmark_company:
            benchmark_value = company_values.get(
                benchmark_company,
                {},
            ).get(metric)

        peer_average = (
            sum(peer_values) / len(peer_values)
            if peer_values
            else None
        )

        radar_data.append(
            {
                "metric": metric,
                "company_value": company_value,
                "peer_average": peer_average,
                "benchmark_value": benchmark_value,
            }
        )

    return {
        "company_id": company_row["company_id"],
        "peer_group": peer_group,
        "benchmark_company": benchmark_company,
        "radar_data": radar_data,
    }