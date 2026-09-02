"""
Day 18 - Peer Percentile Rankings

Load peer groups from Excel, calculate percentile rankings for
the required financial metrics within each peer group and year,
and store the results in SQLite.
"""

from pathlib import Path
import sqlite3

import pandas as pd

from src.analytics.ratios import return_on_capital_employed


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DB_PATH = PROJECT_ROOT / "data" / "nifty100.db"

PEER_GROUPS_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "supporting"
    / "peer_groups.xlsx"
)


METRICS = {
    "ROE": "return_on_equity_pct",
    "ROCE": "roce_percentage",
    "Net Profit Margin": "net_profit_margin_pct",
    "D/E": "debt_to_equity",
    "FCF": "free_cash_flow_cr",
    "PAT CAGR 5yr": "pat_cagr_5yr",
    "Revenue CAGR 5yr": "revenue_cagr_5yr",
    "EPS CAGR 5yr": "eps_cagr_5yr",
    "Interest Coverage": "interest_coverage",
    "Asset Turnover": "asset_turnover",
}


def load_peer_groups():
    """
    Load company peer-group assignments from peer_groups.xlsx.
    """

    if not PEER_GROUPS_FILE.exists():
        raise FileNotFoundError(
            f"Peer group file not found: {PEER_GROUPS_FILE}"
        )

    peer_groups = pd.read_excel(PEER_GROUPS_FILE)

    required_columns = {
        "company_id",
        "peer_group_name",
    }

    missing_columns = required_columns - set(peer_groups.columns)

    if missing_columns:
        raise ValueError(
            "Missing required columns in peer_groups.xlsx: "
            + ", ".join(sorted(missing_columns))
        )

    peer_groups = peer_groups[
        ["company_id", "peer_group_name"]
    ].copy()

    peer_groups["company_id"] = (
        peer_groups["company_id"]
        .astype(str)
        .str.strip()
    )

    peer_groups["peer_group_name"] = (
        peer_groups["peer_group_name"]
        .astype(str)
        .str.strip()
    )

    peer_groups = peer_groups[
        (peer_groups["company_id"] != "")
        & (peer_groups["peer_group_name"] != "")
    ]

    duplicate_companies = (
        peer_groups[
            peer_groups.duplicated(
                subset=["company_id"],
                keep=False,
            )
        ]["company_id"]
        .unique()
        .tolist()
    )

    if duplicate_companies:
        raise ValueError(
            "Companies assigned to multiple peer groups: "
            + ", ".join(duplicate_companies)
        )

    return peer_groups


def report_companies_without_peer_group(conn, peer_groups):
    """
    Report companies that do not have a peer-group assignment.

    The companies table uses `id` as the company identifier.
    """

    companies = pd.read_sql_query(
        """
        SELECT id AS company_id
        FROM companies
        """,
        conn,
    )

    companies["company_id"] = (
        companies["company_id"]
        .astype(str)
        .str.strip()
    )

    assigned_companies = set(
        peer_groups["company_id"]
    )

    database_companies = set(
        companies["company_id"]
    )

    unassigned_companies = sorted(
        database_companies - assigned_companies
    )

    if unassigned_companies:
        print("No peer group assigned")
        print(
            "Companies without peer group:",
            ", ".join(unassigned_companies),
        )
    else:
        print("All companies have a peer group assigned.")

    return unassigned_companies


def load_financial_data(conn):
    """
    Load the financial data required for Day 18.

    ROCE is calculated from the existing project data because
    financial_ratios does not contain a stored ROCE value.

    ROCE formula:

        EBIT = Operating Profit + Other Income

        Capital Employed =
            Equity Capital + Reserves + Borrowings

        ROCE =
            EBIT / Capital Employed * 100
    """

    query = """
        SELECT
            fr.company_id,
            fr.year,
            fr.period,
            fr.net_profit_margin_pct,
            fr.return_on_equity_pct,
            fr.debt_to_equity,
            fr.interest_coverage,
            fr.asset_turnover,
            fr.free_cash_flow_cr,
            fr.revenue_cagr_5yr,
            fr.pat_cagr_5yr,
            fr.eps_cagr_5yr,
            pl.operating_profit,
            pl.other_income,
            bs.equity_capital,
            bs.reserves,
            bs.borrowings
        FROM financial_ratios AS fr
        LEFT JOIN profitandloss AS pl
            ON pl.company_id = fr.company_id
            AND pl.year = fr.year
            AND pl.period = fr.period
        LEFT JOIN balancesheet AS bs
            ON bs.company_id = fr.company_id
            AND bs.year = fr.year
            AND bs.period = fr.period
    """

    financial_data = pd.read_sql_query(
        query,
        conn,
    )

    if financial_data.empty:
        raise ValueError(
            "No financial data found in financial_ratios."
        )

    financial_data["roce_percentage"] = financial_data.apply(
        lambda row: return_on_capital_employed(
            row["operating_profit"],
            row["other_income"],
            row["equity_capital"],
            row["reserves"],
            row["borrowings"],
        ),
        axis=1,
    )

    return financial_data


def build_peer_metric_data(financial_data, peer_groups):
    """
    Match companies to their peer groups and convert the ten
    required metrics into long-format data.
    """

    financial_data = financial_data.copy()

    financial_data["company_id"] = (
        financial_data["company_id"]
        .astype(str)
        .str.strip()
    )

    peer_groups = peer_groups.copy()

    peer_groups["company_id"] = (
        peer_groups["company_id"]
        .astype(str)
        .str.strip()
    )

    merged = financial_data.merge(
        peer_groups,
        on="company_id",
        how="inner",
    )

    if merged.empty:
        raise ValueError(
            "No financial records could be matched to peer groups."
        )

    metric_rows = []

    for metric_name, column_name in METRICS.items():

        if column_name not in merged.columns:
            raise ValueError(
                f"Required metric column is missing: {column_name}"
            )

        current = merged[
            [
                "company_id",
                "peer_group_name",
                "year",
                column_name,
            ]
        ].copy()

        current = current.rename(
            columns={
                column_name: "value"
            }
        )

        current["metric"] = metric_name

        metric_rows.append(
            current[
                [
                    "company_id",
                    "peer_group_name",
                    "metric",
                    "value",
                    "year",
                ]
            ]
        )

    result = pd.concat(
        metric_rows,
        ignore_index=True,
    )

    result["value"] = pd.to_numeric(
        result["value"],
        errors="coerce",
    )

    return result


def calculate_percent_rank(values):
    """
    Calculate SQL-style PERCENT_RANK.

    Formula:

        (RANK - 1) / (COUNT - 1)

    Tied values receive the same minimum rank.

    If there is only one valid company in a
    peer-group/year/metric combination, its percentile
    rank is 0.0.

    Missing values remain NULL.
    """

    result = pd.Series(
        pd.NA,
        index=values.index,
        dtype="Float64",
    )

    valid = values.notna()

    valid_count = int(valid.sum())

    if valid_count == 0:
        return result

    if valid_count == 1:
        result.loc[valid] = 0.0
        return result

    ranks = (
        values.loc[valid]
        .rank(
            method="min",
            ascending=True,
        )
    )

    result.loc[valid] = (
        (ranks - 1)
        / (valid_count - 1)
    )

    return result


def calculate_peer_percentiles(metric_data):
    """
    Calculate percentile ranks independently for each:

        peer_group_name
        year
        metric

    D/E is inverted after the normal percentile calculation
    so that lower debt-to-equity receives a higher percentile.
    """

    metric_data = metric_data.copy()

    metric_data["percentile_rank"] = pd.NA

    grouped = metric_data.groupby(
        [
            "peer_group_name",
            "year",
            "metric",
        ],
        sort=False,
        dropna=False,
    )

    for group_key, group in grouped:

        percentiles = calculate_percent_rank(
            group["value"]
        )

        metric_name = group["metric"].iloc[0]

        if metric_name == "D/E":
            valid = percentiles.notna()

            percentiles.loc[valid] = (
                1.0
                - percentiles.loc[valid].astype(float)
            )

        metric_data.loc[
            group.index,
            "percentile_rank",
        ] = percentiles

    metric_data["percentile_rank"] = pd.to_numeric(
        metric_data["percentile_rank"],
        errors="coerce",
    )

    return metric_data[
        [
            "company_id",
            "peer_group_name",
            "metric",
            "value",
            "percentile_rank",
            "year",
        ]
    ]


def create_peer_percentiles_table(conn):
    """
    Create the SQLite table required by Day 18.
    """

    conn.execute(
        "DROP TABLE IF EXISTS peer_percentiles"
    )

    conn.execute(
        """
        CREATE TABLE peer_percentiles (
            company_id TEXT NOT NULL,
            peer_group_name TEXT NOT NULL,
            metric TEXT NOT NULL,
            value REAL,
            percentile_rank REAL,
            year INTEGER NOT NULL
        )
        """
    )

    conn.commit()


def save_peer_percentiles(conn, results):
    """
    Save percentile results to SQLite.
    """

    results.to_sql(
        "peer_percentiles",
        conn,
        if_exists="append",
        index=False,
    )

    conn.commit()


def validate_peer_percentiles(conn):
    """
    Validate the Day 18 output against the task requirements.
    """

    print()
    print("Running Day 18 validation...")

    table_exists = conn.execute(
        """
        SELECT COUNT(*)
        FROM sqlite_master
        WHERE type = 'table'
          AND name = 'peer_percentiles'
        """
    ).fetchone()[0]

    if table_exists != 1:
        raise AssertionError(
            "peer_percentiles table was not created."
        )

    actual_columns = [
        row[1]
        for row in conn.execute(
            "PRAGMA table_info(peer_percentiles)"
        ).fetchall()
    ]

    required_columns = [
        "company_id",
        "peer_group_name",
        "metric",
        "value",
        "percentile_rank",
        "year",
    ]

    if actual_columns != required_columns:
        raise AssertionError(
            "peer_percentiles columns are incorrect.\n"
            f"Expected: {required_columns}\n"
            f"Actual:   {actual_columns}"
        )

    metric_count = conn.execute(
        """
        SELECT COUNT(DISTINCT metric)
        FROM peer_percentiles
        """
    ).fetchone()[0]

    if metric_count != 10:
        raise AssertionError(
            f"Expected 10 metrics, found {metric_count}."
        )

    database_metrics = {
        row[0]
        for row in conn.execute(
            """
            SELECT DISTINCT metric
            FROM peer_percentiles
            """
        ).fetchall()
    }

    expected_metrics = set(METRICS.keys())

    if database_metrics != expected_metrics:
        raise AssertionError(
            "Metric list does not match Day 18 requirements.\n"
            f"Expected: {sorted(expected_metrics)}\n"
            f"Actual:   {sorted(database_metrics)}"
        )

    peer_group_count = conn.execute(
        """
        SELECT COUNT(DISTINCT peer_group_name)
        FROM peer_percentiles
        """
    ).fetchone()[0]

    if peer_group_count != 11:
        raise AssertionError(
            f"Expected 11 peer groups, found {peer_group_count}."
        )

    invalid_percentiles = conn.execute(
        """
        SELECT COUNT(*)
        FROM peer_percentiles
        WHERE percentile_rank IS NOT NULL
          AND (
              percentile_rank < 0
              OR percentile_rank > 1
          )
        """
    ).fetchone()[0]

    if invalid_percentiles:
        raise AssertionError(
            f"Found {invalid_percentiles} percentile values "
            "outside the 0 to 1 range."
        )

    duplicate_count = conn.execute(
        """
        SELECT COUNT(*)
        FROM (
            SELECT
                company_id,
                peer_group_name,
                metric,
                year
            FROM peer_percentiles
            GROUP BY
                company_id,
                peer_group_name,
                metric,
                year
            HAVING COUNT(*) > 1
        )
        """
    ).fetchone()[0]

    if duplicate_count:
        raise AssertionError(
            f"Found {duplicate_count} duplicate "
            "company/group/metric/year combinations."
        )

    total_rows = conn.execute(
        """
        SELECT COUNT(*)
        FROM peer_percentiles
        """
    ).fetchone()[0]

    if total_rows == 0:
        raise AssertionError(
            "peer_percentiles contains no rows."
        )

    percentile_range = conn.execute(
        """
        SELECT
            MIN(percentile_rank),
            MAX(percentile_rank)
        FROM peer_percentiles
        """
    ).fetchone()

    print("Validation passed.")
    print(f"Total rows: {total_rows}")
    print(f"Metrics: {metric_count}")
    print(f"Peer groups: {peer_group_count}")
    print(
        "Percentile range: "
        f"{percentile_range[0]} to {percentile_range[1]}"
    )


def main():
    """
    Run the complete Day 18 peer percentile process.
    """

    print("Day 18 - Peer Percentile Rankings")
    print("----------------------------------")

    print()
    print("Loading peer groups...")

    peer_groups = load_peer_groups()

    print(
        f"Peer-group assignments loaded: "
        f"{len(peer_groups)}"
    )

    peer_group_count = (
        peer_groups["peer_group_name"]
        .nunique()
    )

    print(
        f"Peer groups found: "
        f"{peer_group_count}"
    )

    if peer_group_count != 11:
        raise ValueError(
            "Expected 11 peer groups in peer_groups.xlsx."
        )

    print()
    print("Opening database...")

    conn = sqlite3.connect(DB_PATH)

    try:
        print()
        print("Checking peer-group assignments...")

        report_companies_without_peer_group(
            conn,
            peer_groups,
        )

        print()
        print("Loading financial data...")

        financial_data = load_financial_data(
            conn
        )

        print(
            f"Financial rows loaded: "
            f"{len(financial_data)}"
        )

        print()
        print("Preparing Day 18 metrics...")

        metric_data = build_peer_metric_data(
            financial_data,
            peer_groups,
        )

        print(
            f"Metric rows prepared: "
            f"{len(metric_data)}"
        )

        print()
        print("Calculating peer percentile rankings...")

        results = calculate_peer_percentiles(
            metric_data
        )

        print(
            f"Percentile rows calculated: "
            f"{len(results)}"
        )

        print()
        print("Creating peer_percentiles table...")

        create_peer_percentiles_table(
            conn
        )

        print("Saving percentile rankings...")

        save_peer_percentiles(
            conn,
            results,
        )

        validate_peer_percentiles(
            conn
        )

        print()
        print("Day 18 completed successfully.")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
