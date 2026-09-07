import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from dashboard.utils.db import get_peers, get_ratios


st.title("Peer Comparison")

st.write(
    "Compare a company against the average financial metrics "
    "of its peer group."
)


peer_groups = [
    "Automobiles",
    "Consumer Finance",
    "FMCG",
    "IT Services",
    "Life Insurance",
    "Oil & Gas",
    "Pharmaceuticals",
    "Power & Utilities",
    "Private Banks",
    "Public Sector Banks",
    "Steel",
]


selected_group = st.selectbox(
    "Select Peer Group",
    peer_groups,
)


peers = get_peers(selected_group)


if peers.empty:
    st.warning("No companies found in this peer group.")
    st.stop()


peer_names = peers["company_name"].dropna().tolist()


selected_company = st.selectbox(
    "Select Company",
    peer_names,
)


peer_rows = []


for _, peer in peers.iterrows():

    company_name = peer["company_name"]

    ratios = get_ratios(
        company_name,
        2024,
    )

    if not ratios.empty:

        row = ratios.iloc[0].copy()

        row["company_id"] = peer["company_id"]
        row["company_name"] = company_name
        row["is_benchmark"] = peer["is_benchmark"]

        peer_rows.append(row)


if not peer_rows:
    st.warning(
        "No financial data is available for this peer group."
    )
    st.stop()


peer_df = pd.DataFrame(peer_rows)


selected_data = peer_df[
    peer_df["company_name"] == selected_company
]


if selected_data.empty:
    st.warning(
        "Selected company data is not available."
    )
    st.stop()


selected_row = selected_data.iloc[0]


metrics = {
    "ROE": "return_on_equity_pct",
    "D/E": "debt_to_equity",
    "FCF": "free_cash_flow_cr",
    "Revenue CAGR": "revenue_cagr_5yr",
    "PAT CAGR": "pat_cagr_5yr",
    "OPM": "operating_profit_margin_pct",
    "ICR": "interest_coverage",
    "Composite Score": "composite_quality_score",
}


st.subheader(
    f"{selected_company} vs {selected_group} Average"
)


company_values = []
average_values = []


for label, column in metrics.items():

    company_value = pd.to_numeric(
        pd.Series([selected_row[column]]),
        errors="coerce",
    ).iloc[0]

    average_value = pd.to_numeric(
        peer_df[column],
        errors="coerce",
    ).mean()

    if pd.isna(company_value):
        company_value = 0

    if pd.isna(average_value):
        average_value = 0

    company_values.append(float(company_value))
    average_values.append(float(average_value))


metric_labels = list(metrics.keys())


fig = go.Figure()


fig.add_trace(
    go.Scatterpolar(
        r=company_values + [company_values[0]],
        theta=metric_labels + [metric_labels[0]],
        fill="toself",
        name=selected_company,
        line=dict(color="#1f77b4"),
    )
)


fig.add_trace(
    go.Scatterpolar(
        r=average_values + [average_values[0]],
        theta=metric_labels + [metric_labels[0]],
        fill="toself",
        name=f"{selected_group} Average",
        line=dict(color="#ff7f0e"),
    )
)


fig.update_layout(
    polar=dict(
        radialaxis=dict(
            visible=True
        )
    ),
    showlegend=True,
    margin=dict(
        t=30,
        b=30,
        l=30,
        r=30,
    ),
)


st.plotly_chart(
    fig,
    use_container_width=True,
)


st.subheader(
    f"Peer Group KPIs — {selected_group}"
)


table_columns = [
    "company_name",
    "is_benchmark",
    "return_on_equity_pct",
    "debt_to_equity",
    "free_cash_flow_cr",
    "revenue_cagr_5yr",
    "pat_cagr_5yr",
    "operating_profit_margin_pct",
    "interest_coverage",
    "composite_quality_score",
]


table_columns = [
    column
    for column in table_columns
    if column in peer_df.columns
]


table_df = peer_df[table_columns].copy()


table_df = table_df.rename(
    columns={
        "company_name": "Company",
        "is_benchmark": "Benchmark",
        "return_on_equity_pct": "ROE %",
        "debt_to_equity": "D/E",
        "free_cash_flow_cr": "FCF (Cr)",
        "revenue_cagr_5yr": "Revenue CAGR %",
        "pat_cagr_5yr": "PAT CAGR %",
        "operating_profit_margin_pct": "OPM %",
        "interest_coverage": "ICR",
        "composite_quality_score": "Composite Score",
    }
)


table_df = table_df.reset_index(drop=True)


def highlight_benchmark(row):

    if bool(row["Benchmark"]):
        return [
            "background-color: #d4edda; font-weight: bold;"
        ] * len(row)

    return [""] * len(row)


styled_table = table_df.style.apply(
    highlight_benchmark,
    axis=1,
)


st.dataframe(
    styled_table,
    use_container_width=True,
    hide_index=True,
)
