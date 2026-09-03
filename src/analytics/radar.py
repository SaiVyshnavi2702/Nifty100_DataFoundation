from pathlib import Path
import shutil
import sqlite3

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DB_PATH = PROJECT_ROOT / "data" / "nifty100.db"
OUTPUT_DIR = PROJECT_ROOT / "reports" / "radar_charts"

RADAR_METRICS = [
    "ROE",
    "ROCE",
    "NPM",
    "D/E",
    "FCF Score",
    "PAT CAGR 5yr",
    "Revenue CAGR 5yr",
    "Composite Score",
]

DAY18_METRIC_MAPPING = {
    "ROE": "ROE",
    "ROCE": "ROCE",
    "Net Profit Margin": "NPM",
    "D/E": "D/E",
    "FCF": "FCF Score",
    "PAT CAGR 5yr": "PAT CAGR 5yr",
    "Revenue CAGR 5yr": "Revenue CAGR 5yr",
    
    
}


def load_peer_percentiles(conn):
    query = """
        SELECT
            company_id,
            peer_group_name,
            metric,
            percentile_rank,
            year
        FROM peer_percentiles
    """

    df = pd.read_sql_query(query, conn)

    if df.empty:
        raise ValueError(
            "No data found in peer_percentiles. Run Day 18 before Day 19."
        )

    df["company_id"] = df["company_id"].astype(str).str.strip()
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df["percentile_rank"] = pd.to_numeric(
        df["percentile_rank"],
        errors="coerce",
    )

    return df


def load_composite_scores(conn):
    query = """
        SELECT
            company_id,
            year,
            composite_quality_score
        FROM financial_ratios
        WHERE composite_quality_score IS NOT NULL
    """

    df = pd.read_sql_query(query, conn)

    if df.empty:
        raise ValueError(
            "No composite_quality_score values found in financial_ratios."
        )

    df["company_id"] = df["company_id"].astype(str).str.strip()
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df["composite_quality_score"] = pd.to_numeric(
        df["composite_quality_score"],
        errors="coerce",
    )

    df = df.dropna(
        subset=[
            "company_id",
            "year",
            "composite_quality_score",
        ]
    )

    latest = (
        df.sort_values(
            ["company_id", "year"]
        )
        .groupby(
            "company_id",
            as_index=False,
        )
        .tail(1)
    )

    return latest[
        [
            "company_id",
            "year",
            "composite_quality_score",
        ]
    ].reset_index(drop=True)


def load_companies(conn):
    query = """
        SELECT
            id AS company_id,
            company_name
        FROM companies
    """

    companies = pd.read_sql_query(query, conn)

    companies["company_id"] = (
        companies["company_id"]
        .astype(str)
        .str.strip()
    )

    return companies


def load_raw_financial_data(conn):
    query = """
        SELECT
            fr.company_id,
            fr.year,
            fr.return_on_equity_pct,
            fr.net_profit_margin_pct,
            fr.debt_to_equity,
            fr.free_cash_flow_cr,
            fr.pat_cagr_5yr,
            fr.revenue_cagr_5yr,
            fr.composite_quality_score,
            pl.operating_profit,
            pl.other_income,
            bs.equity_capital,
            bs.reserves,
            bs.borrowings
        FROM financial_ratios AS fr
        LEFT JOIN profitandloss AS pl
            ON pl.company_id = fr.company_id
            AND pl.year = fr.year
        LEFT JOIN balancesheet AS bs
            ON bs.company_id = fr.company_id
            AND bs.year = fr.year
    """

    df = pd.read_sql_query(query, conn)

    if df.empty:
        raise ValueError("No financial data found for Day 19.")

    df["company_id"] = df["company_id"].astype(str).str.strip()
    df["year"] = pd.to_numeric(df["year"], errors="coerce")

    numeric_columns = [
        "return_on_equity_pct",
        "net_profit_margin_pct",
        "debt_to_equity",
        "free_cash_flow_cr",
        "pat_cagr_5yr",
        "revenue_cagr_5yr",
        "composite_quality_score",
        "operating_profit",
        "other_income",
        "equity_capital",
        "reserves",
        "borrowings",
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    df["roce_percentage"] = calculate_roce(df)

    return df


def calculate_roce(df):
    ebit = (
        df["operating_profit"]
        + df["other_income"]
    )

    capital_employed = (
        df["equity_capital"]
        + df["reserves"]
        + df["borrowings"]
    )

    roce = (
        ebit
        / capital_employed
        * 100
    )

    return roce.replace(
        [np.inf, -np.inf],
        np.nan,
    )


def prepare_peer_radar_data(
    peer_percentiles,
    composite_scores,
):
    data = peer_percentiles.copy()

    data["radar_metric"] = data["metric"].map(
        DAY18_METRIC_MAPPING
    )

    data = data.dropna(
        subset=["radar_metric"]
    )

    data = data[
        [
            "company_id",
            "peer_group_name",
            "radar_metric",
            "percentile_rank",
            "year",
        ]
    ]

    composite = composite_scores.copy()

    composite["radar_metric"] = "Composite Score"

    composite["percentile_rank"] = (
        composite["composite_quality_score"]
        / 100.0
    )

    composite = composite[
        [
            "company_id",
            "year",
            "radar_metric",
            "percentile_rank",
        ]
    ]

    peer_lookup = (
        data[
            [
                "company_id",
                "peer_group_name",
            ]
        ]
        .drop_duplicates(
            subset=["company_id"]
        )
    )

    composite = composite.merge(
        peer_lookup,
        on="company_id",
        how="left",
    )

    composite = composite[
        [
            "company_id",
            "peer_group_name",
            "radar_metric",
            "percentile_rank",
            "year",
        ]
    ]

    result = pd.concat(
        [
            data,
            composite,
        ],
        ignore_index=True,
    )

    result["percentile_rank"] = pd.to_numeric(
        result["percentile_rank"],
        errors="coerce",
    )

    result["percentile_rank"] = (
        result["percentile_rank"]
        .clip(0, 1)
    )

    return result


def calculate_peer_averages(data):
    averages = (
        data.dropna(
            subset=["peer_group_name"]
        )
        .groupby(
            [
                "peer_group_name",
                "year",
                "radar_metric",
            ],
            as_index=False,
        )["percentile_rank"]
        .mean()
    )

    return averages


def get_company_values(
    data,
    company_id,
    year,
    metrics=None,
):
    if metrics is None:
        metrics = RADAR_METRICS

    company_data = data[
        (data["company_id"] == company_id)
        & (data["year"] == year)
    ]

    values = {}

    for metric in metrics:
        rows = company_data[
            company_data["radar_metric"] == metric
        ]

        if rows.empty:
            values[metric] = np.nan
        else:
            values[metric] = float(
                rows["percentile_rank"].iloc[0]
            )

    return values


def get_peer_average_values(
    peer_averages,
    peer_group_name,
    year,
):
    group_data = peer_averages[
        (peer_averages["peer_group_name"] == peer_group_name)
        & (peer_averages["year"] == year)
    ]

    values = {}

    for metric in RADAR_METRICS:
        rows = group_data[
            group_data["radar_metric"] == metric
        ]

        if rows.empty:
            values[metric] = np.nan
        else:
            values[metric] = float(
                rows["percentile_rank"].iloc[0]
            )

    return values


def select_latest_company_years(data):
    latest = (
        data.dropna(
            subset=["year"]
        )
        .sort_values(
            [
                "company_id",
                "year",
            ]
        )
        .groupby(
            "company_id",
            as_index=False,
        )
        .tail(1)
    )

    return latest[
        [
            "company_id",
            "year",
        ]
    ].drop_duplicates()


def calculate_cross_sectional_percentiles(raw_data):
    data = raw_data.copy()

    metric_columns = {
        "ROE": "return_on_equity_pct",
        "ROCE": "roce_percentage",
        "NPM": "net_profit_margin_pct",
        "D/E": "debt_to_equity",
        "FCF Score": "free_cash_flow_cr",
        "PAT CAGR 5yr": "pat_cagr_5yr",
        "Revenue CAGR 5yr": "revenue_cagr_5yr",
        "Composite Score": "composite_quality_score",
    }

    rows = []

    for year, year_data in data.groupby(
        "year",
        dropna=True,
    ):
        for metric, column in metric_columns.items():

            values = pd.to_numeric(
                year_data[column],
                errors="coerce",
            )

            valid = values.notna()
            count = int(valid.sum())

            if count == 0:
                continue

            percentile = pd.Series(
                np.nan,
                index=values.index,
                dtype=float,
            )

            if count == 1:
                percentile.loc[valid] = 0.0
            else:
                ranks = values.loc[valid].rank(
                    method="min",
                    ascending=True,
                )

                percentile.loc[valid] = (
                    (ranks - 1)
                    / (count - 1)
                )

            if metric == "D/E":
                percentile.loc[valid] = (
                    1.0
                    - percentile.loc[valid]
                )

            current = pd.DataFrame(
                {
                    "company_id": year_data["company_id"],
                    "year": year,
                    "radar_metric": metric,
                    "percentile_rank": percentile,
                }
            )

            rows.append(current)

    if not rows:
        return pd.DataFrame(
            columns=[
                "company_id",
                "year",
                "radar_metric",
                "percentile_rank",
            ]
        )

    result = pd.concat(
        rows,
        ignore_index=True,
    )

    result["percentile_rank"] = (
        result["percentile_rank"]
        .clip(0, 1)
    )

    return result


def calculate_nifty_average_values(
    nifty_percentiles,
    year,
    metrics=None,
):
    if metrics is None:
        metrics = RADAR_METRICS

    year_data = nifty_percentiles[
        nifty_percentiles["year"] == year
    ]

    averages = (
        year_data.groupby(
            "radar_metric"
        )["percentile_rank"]
        .mean()
        .to_dict()
    )

    return {
        metric: averages.get(
            metric,
            np.nan,
        )
        for metric in metrics
    }


def calculate_composite_reference(
    composite_scores,
    year,
):
    year_data = composite_scores[
        composite_scores["year"] == year
    ]

    if year_data.empty:
        return np.nan

    return float(
        (
            year_data["composite_quality_score"]
            / 100.0
        ).mean()
    )


def get_standalone_composite_value(
    composite_scores,
    company_id,
):
    company_data = composite_scores[
        composite_scores["company_id"] == company_id
    ]

    if company_data.empty:
        return np.nan

    row = (
        company_data
        .sort_values("year")
        .tail(1)
        .iloc[0]
    )

    value = pd.to_numeric(
        row["composite_quality_score"],
        errors="coerce",
    )

    if pd.isna(value):
        return np.nan

    return float(
        np.clip(value / 100.0, 0.0, 1.0)
    )


def create_radar_chart(
    company_name,
    company_id,
    year,
    company_values,
    reference_values,
    reference_label,
    output_path,
    metrics,
    standalone=False,
):
    company_array = np.array(
        [
            company_values.get(
                metric,
                np.nan,
            )
            for metric in metrics
        ],
        dtype=float,
    )

    reference_array = np.array(
        [
            reference_values.get(
                metric,
                np.nan,
            )
            for metric in metrics
        ],
        dtype=float,
    )

    if not np.isfinite(company_array).any():
        return False

    company_array = np.nan_to_num(
        company_array,
        nan=0.0,
    )

    reference_array = np.nan_to_num(
        reference_array,
        nan=0.0,
    )

    angles = np.linspace(
        0,
        2 * np.pi,
        len(metrics),
        endpoint=False,
    )

    company_closed = np.concatenate(
        [
            company_array,
            [company_array[0]],
        ]
    )

    reference_closed = np.concatenate(
        [
            reference_array,
            [reference_array[0]],
        ]
    )

    angles_closed = np.concatenate(
        [
            angles,
            [angles[0]],
        ]
    )

    if standalone:
        figure_size = (8, 8)
    else:
        figure_size = (10, 10)

    fig, ax = plt.subplots(
        figsize=figure_size,
        subplot_kw={"polar": True},
    )

    ax.plot(
        angles_closed,
        reference_closed,
        linestyle="--",
        linewidth=2.2,
        color="darkorange",
        label=reference_label,
    )

    ax.plot(
        angles_closed,
        company_closed,
        linewidth=2.7,
        color="royalblue",
        label=company_name,
    )

    ax.fill(
        angles_closed,
        company_closed,
        color="royalblue",
        alpha=0.25,
    )

    ax.set_xticks(angles)

    ax.set_xticklabels(
        metrics,
        fontsize=12 if not standalone else 13,
        fontweight="bold",
    )

    ax.set_ylim(0, 1)

    ax.set_yticks(
        [
            0.2,
            0.4,
            0.6,
            0.8,
            1.0,
        ]
    )

    ax.set_yticklabels(
        [
            "20",
            "40",
            "60",
            "80",
            "100",
        ],
        fontsize=10,
    )

    if standalone:
        title_suffix = "Nifty 100 Standalone Analysis"
    else:
        title_suffix = "Peer Radar Analysis"

    ax.set_title(
        f"{company_name} ({company_id})\n"
        f"{title_suffix} - {int(year)}",
        fontsize=17,
        fontweight="bold",
        pad=30,
    )

    ax.legend(
        loc="upper right",
        bbox_to_anchor=(1.30, 1.12),
        fontsize=10,
    )

    ax.grid(
        linewidth=0.8,
        alpha=0.5,
    )

    fig.tight_layout()

    fig.savefig(
        output_path,
        dpi=180,
        bbox_inches="tight",
    )

    plt.close(fig)

    return True


def get_company_name(
    companies,
    company_id,
):
    match = companies[
        companies["company_id"] == company_id
    ]

    if match.empty:
        return company_id

    return str(
        match["company_name"].iloc[0]
    )


def generate_peer_group_charts(
    data,
    peer_averages,
    companies,
):
    generated = 0

    assigned = data.dropna(
        subset=["peer_group_name"]
    )

    company_years = select_latest_company_years(
        assigned
    )

    for row in company_years.itertuples(
        index=False
    ):
        company_id = row.company_id
        year = row.year

        company_rows = assigned[
            (assigned["company_id"] == company_id)
            & (assigned["year"] == year)
        ]

        if company_rows.empty:
            continue

        peer_group_name = (
            company_rows[
                "peer_group_name"
            ]
            .dropna()
            .iloc[0]
        )

        company_values = get_company_values(
            assigned,
            company_id,
            year,
            RADAR_METRICS,
        )

        reference_values = get_peer_average_values(
            peer_averages,
            peer_group_name,
            year,
        )

        company_name = get_company_name(
            companies,
            company_id,
        )

        safe_company_id = (
            str(company_id)
            .replace("/", "_")
            .replace("\\", "_")
            .replace(" ", "_")
        )

        output_path = (
            OUTPUT_DIR
            / f"{safe_company_id}_radar.png"
        )

        created = create_radar_chart(
            company_name=company_name,
            company_id=company_id,
            year=year,
            company_values=company_values,
            reference_values=reference_values,
            reference_label=f"{peer_group_name} Average",
            output_path=output_path,
            metrics=RADAR_METRICS,
            standalone=False,
        )

        if created:
            generated += 1

    return generated


def generate_standalone_charts(
    peer_data,
    nifty_percentiles,
    composite_scores,
    companies,
):
    generated = 0

    all_company_ids = set(
        companies["company_id"]
    )

    assigned_company_ids = set(
        peer_data.dropna(
            subset=["peer_group_name"]
        )["company_id"]
    )

    unassigned_company_ids = sorted(
        all_company_ids - assigned_company_ids
    )

    standalone_metrics = [
        "Composite Score"
    ]

    for company_id in unassigned_company_ids:

        company_data = nifty_percentiles[
            nifty_percentiles["company_id"] == company_id
        ]

        if not company_data.empty:
            years = sorted(
                company_data["year"]
                .dropna()
                .unique()
            )
        else:
            years = []

        if years:
            year = years[-1]

            company_value = get_company_values(
                nifty_percentiles,
                company_id,
                year,
                standalone_metrics,
            ).get(
                "Composite Score",
                np.nan,
            )

            nifty_average = calculate_nifty_average_values(
                nifty_percentiles,
                year,
                standalone_metrics,
            ).get(
                "Composite Score",
                np.nan,
            )

        else:
            composite_data = composite_scores[
                composite_scores["company_id"] == company_id
            ]

            if composite_data.empty:
                print(
                    f"Warning: No data available for {company_id}. "
                    f"Using zero as standalone Composite Score."
                )

                company_years = composite_scores[
                    "year"
                ].dropna()

                if company_years.empty:
                    continue

                year = int(
                    company_years.max()
                )

                company_value = 0.0

            else:
                year = int(
                    composite_data[
                        "year"
                    ].max()
                )

                company_value = (
                    get_standalone_composite_value(
                        composite_scores,
                        company_id,
                    )
                )

                if not np.isfinite(company_value):
                    company_value = 0.0

            nifty_average = calculate_composite_reference(
                composite_scores,
                year,
            )

            if not np.isfinite(nifty_average):
                nifty_average = 0.0

        if not np.isfinite(company_value):
            company_value = (
                get_standalone_composite_value(
                    composite_scores,
                    company_id,
                )
            )

        if not np.isfinite(company_value):
            company_value = 0.0

        if not np.isfinite(nifty_average):
            nifty_average = calculate_composite_reference(
                composite_scores,
                year,
            )

        if not np.isfinite(nifty_average):
            nifty_average = 0.0

        company_values = {
            "Composite Score": company_value
        }

        reference_values = {
            "Composite Score": nifty_average
        }

        company_name = get_company_name(
            companies,
            company_id,
        )

        safe_company_id = (
            str(company_id)
            .replace("/", "_")
            .replace("\\", "_")
            .replace(" ", "_")
        )

        output_path = (
            OUTPUT_DIR
            / f"{safe_company_id}_radar.png"
        )

        created = create_radar_chart(
            company_name=company_name,
            company_id=company_id,
            year=year,
            company_values=company_values,
            reference_values=reference_values,
            reference_label="Nifty 100 Average",
            output_path=output_path,
            metrics=standalone_metrics,
            standalone=True,
        )

        if created:
            generated += 1

    return generated


def clear_output_directory():
    if OUTPUT_DIR.exists():
        for item in OUTPUT_DIR.iterdir():

            if item.is_file():
                item.unlink()

            elif item.is_dir():
                shutil.rmtree(item)

    else:
        OUTPUT_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )


def validate_output(expected_count):
    if not OUTPUT_DIR.exists():
        raise AssertionError(
            "Radar chart output directory was not created."
        )

    charts = list(
        OUTPUT_DIR.glob("*_radar.png")
    )

    if not charts:
        raise AssertionError(
            "No radar charts were generated."
        )

    if len(charts) != expected_count:
        raise AssertionError(
            f"Expected {expected_count} radar charts, "
            f"but found {len(charts)}."
        )

    for chart in charts:
        if chart.stat().st_size == 0:
            raise AssertionError(
                f"Empty radar chart file: {chart}"
            )

    print(
        f"Radar charts found: {len(charts)}"
    )


def main():
    print("Day 19 - Radar Charts")
    print("---------------------")

    print()
    print("Preparing output directory...")
    clear_output_directory()

    print()
    print("Opening database...")

    conn = sqlite3.connect(DB_PATH)

    try:
        print()
        print("Loading peer percentile data...")

        peer_percentiles = load_peer_percentiles(conn)

        print(
            f"Peer percentile rows loaded: "
            f"{len(peer_percentiles)}"
        )

        print()
        print("Loading composite scores...")

        composite_scores = load_composite_scores(conn)

        print(
            f"Composite score rows loaded: "
            f"{len(composite_scores)}"
        )

        print()
        print("Loading companies...")

        companies = load_companies(conn)

        print(
            f"Companies loaded: "
            f"{len(companies)}"
        )

        print()
        print("Loading financial data...")

        raw_financial_data = load_raw_financial_data(conn)

        print(
            f"Financial rows loaded: "
            f"{len(raw_financial_data)}"
        )

        print()
        print("Preparing peer-group radar data...")

        peer_data = prepare_peer_radar_data(
            peer_percentiles,
            composite_scores,
        )

        print(
            f"Peer radar rows prepared: "
            f"{len(peer_data)}"
        )

        print()
        print("Calculating peer-group averages...")

        peer_averages = calculate_peer_averages(
            peer_data
        )

        print(
            f"Peer average rows: "
            f"{len(peer_averages)}"
        )

        print()
        print("Calculating Nifty 100 percentile scores...")

        nifty_percentiles = (
            calculate_cross_sectional_percentiles(
                raw_financial_data
            )
        )

        print(
            f"Nifty percentile rows: "
            f"{len(nifty_percentiles)}"
        )

        print()
        print("Generating peer-group radar charts...")

        peer_chart_count = generate_peer_group_charts(
            peer_data,
            peer_averages,
            companies,
        )

        print(
            f"Peer-group charts generated: "
            f"{peer_chart_count}"
        )

        print()
        print("Generating standalone charts...")

        standalone_chart_count = generate_standalone_charts(
            peer_data,
            nifty_percentiles,
            composite_scores,
            companies,
        )

        print(
            f"Standalone charts generated: "
            f"{standalone_chart_count}"
        )

        total_charts = (
            peer_chart_count
            + standalone_chart_count
        )

        print()
        print("Validating output...")

        validate_output(
            len(companies)
        )

        print()
        print("Day 19 completed successfully.")

        print(
            f"Total charts generated: "
            f"{total_charts}"
        )

        print(
            f"Output directory: "
            f"{OUTPUT_DIR}"
        )

    finally:
        conn.close()


if __name__ == "__main__":
    main()
