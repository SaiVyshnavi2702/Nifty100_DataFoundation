import sqlite3
import os
import numpy as np
import pandas as pd

from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt


DB_PATH = "data/nifty100.db"
OUTPUT_PATH = "output/cluster_labels.csv"
ELBOW_PATH = "reports/elbow_plot.png"


FEATURES = [
    "return_on_equity_pct",
    "debt_to_equity",
    "revenue_cagr_5yr",
    "fcf_cagr_5yr",
    "operating_profit_margin_pct"
]


def load_data():

    connection = sqlite3.connect(DB_PATH)

    ratios = pd.read_sql_query(
        """
        SELECT
            company_id,
            year,
            return_on_equity_pct,
            debt_to_equity,
            revenue_cagr_5yr,
            operating_profit_margin_pct
        FROM financial_ratios
        """,
        connection
    )

    cashflow = pd.read_sql_query(
        """
        SELECT
            company_id,
            year,
            operating_activity,
            investing_activity
        FROM cashflow
        """,
        connection
    )

    connection.close()

    print("Rows loaded:", len(ratios))
    print("Companies:", ratios["company_id"].nunique())

    return ratios, cashflow


def calculate_fcf_cagr(cashflow):

    results = []

    for company_id, group in cashflow.groupby("company_id"):

        group = group.sort_values("year").copy()

        group["free_cash_flow"] = (
            group["operating_activity"].fillna(0)
            + group["investing_activity"].fillna(0)
        )

        valid = group[group["free_cash_flow"].notna()]

        if len(valid) < 6:
            continue

        latest = valid.iloc[-1]
        previous = valid.iloc[-6]

        current_fcf = latest["free_cash_flow"]
        previous_fcf = previous["free_cash_flow"]

        if previous_fcf <= 0:
            continue

        if current_fcf <= 0:
            continue

        cagr = (
            (current_fcf / previous_fcf) ** (1 / 5) - 1
        ) * 100

        results.append({
            "company_id": company_id,
            "fcf_cagr_5yr": cagr
        })

    return pd.DataFrame(results)


def prepare_latest_data(ratios, fcf_cagr):

    ratios = ratios.sort_values("year")

    latest = ratios.groupby("company_id").tail(1).copy()

    latest = latest[
        [
            "company_id",
            "return_on_equity_pct",
            "debt_to_equity",
            "revenue_cagr_5yr",
            "operating_profit_margin_pct"
        ]
    ]

    latest = latest.merge(
        fcf_cagr,
        on="company_id",
        how="left"
    )

    return latest


def sector_median_imputation(data):

    connection = sqlite3.connect(DB_PATH)

    sectors = pd.read_sql_query(
        """
        SELECT
            company_id,
            broad_sector
        FROM sectors
        """,
        connection
    )

    connection.close()

    data = data.merge(
        sectors,
        on="company_id",
        how="left"
    )

    for feature in FEATURES:

        data[feature] = pd.to_numeric(
            data[feature],
            errors="coerce"
        )

        data[feature] = data.groupby(
            "broad_sector"
        )[feature].transform(
            lambda x: x.fillna(x.median())
        )

        data[feature] = data[feature].fillna(
            data[feature].median()
        )

    return data


def create_elbow_plot(scaled_data):

    inertias = []

    for k in range(2, 11):

        model = KMeans(
            n_clusters=k,
            random_state=42,
            n_init=10
        )

        model.fit(scaled_data)

        inertias.append(model.inertia_)

    os.makedirs("reports", exist_ok=True)

    plt.figure(figsize=(8, 5))

    plt.plot(
        range(2, 11),
        inertias,
        marker="o"
    )

    plt.xlabel("Number of Clusters")
    plt.ylabel("Inertia")
    plt.title("KMeans Elbow Plot")

    plt.grid(True)

    plt.savefig(
        ELBOW_PATH,
        dpi=150,
        bbox_inches="tight"
    )

    plt.close()

    print("Created:", ELBOW_PATH)


def main():

    print("Day 36 - KMeans Clustering")

    ratios, cashflow = load_data()

    print("Calculating FCF CAGR...")

    fcf_cagr = calculate_fcf_cagr(cashflow)

    print(
        "Companies with FCF CAGR:",
        len(fcf_cagr)
    )

    data = prepare_latest_data(
        ratios,
        fcf_cagr
    )

    print(
        "Companies for clustering:",
        len(data)
    )

    print("Applying sector median imputation...")

    data = sector_median_imputation(data)

    feature_data = data[FEATURES].copy()

    imputer = SimpleImputer(
        strategy="median"
    )

    feature_data = imputer.fit_transform(
        feature_data
    )

    scaler = StandardScaler()

    scaled_data = scaler.fit_transform(
        feature_data
    )

    print("Creating elbow plot...")

    create_elbow_plot(
        scaled_data
    )

    print("Running KMeans with 5 clusters...")

    model = KMeans(
        n_clusters=5,
        random_state=42,
        n_init=10
    )

    cluster_ids = model.fit_predict(
        scaled_data
    )

    distances = model.transform(
        scaled_data
    )

    minimum_distances = distances.min(
        axis=1
    )

    data["cluster_id"] = cluster_ids

    data["distance_from_centroid"] = (
        minimum_distances
    )

    cluster_names = {
        0: "Balanced",
        1: "Growth",
        2: "High Leverage",
        3: "High Quality",
        4: "Defensive"
    }

    data["cluster_name"] = data[
        "cluster_id"
    ].map(cluster_names)

    output = data[
        [
            "company_id",
            "cluster_id",
            "cluster_name",
            "distance_from_centroid"
        ]
    ].copy()

    os.makedirs(
        "output",
        exist_ok=True
    )

    output.to_csv(
        OUTPUT_PATH,
        index=False
    )

    print(
        "Created:",
        OUTPUT_PATH
    )

    print(
        "Rows:",
        len(output)
    )

    print(
        "Companies:",
        output["company_id"].nunique()
    )

    print(
        "Clusters:",
        sorted(output["cluster_id"].unique())
    )

    print()
    print(
        output.to_string(index=False)
    )

    print()
    print(
        "Day 36 KMeans Clustering completed successfully."
    )


if __name__ == "__main__":
    main()
