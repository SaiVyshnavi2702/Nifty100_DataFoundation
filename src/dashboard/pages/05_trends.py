import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from dashboard.utils.db import get_companies, get_ratios, get_pl

st.set_page_config(
    page_title="Trend Analysis | Nifty 100 Analytics",
    page_icon="📈",
    layout="wide"
)


st.title("📈 Trend Analysis")

st.write(
    "Compare a company's financial performance over the last 10 years."
)


companies = get_companies()

if companies.empty:
    st.warning("No company data is available.")
    st.stop()


company_names = (
    companies["company_name"]
    .dropna()
    .sort_values()
    .tolist()
)


st.subheader("Search Company")

search_text = st.text_input(
    "Search by company name or ticker",
    placeholder="Type company name or ticker..."
)


search_text = search_text.strip().lower()


if search_text:

    matching_companies = companies[
        companies["company_name"]
        .str.lower()
        .str.contains(search_text, na=False)
    ]["company_name"].tolist()

    if not matching_companies:
        st.warning(
            "Ticker not found — please try another."
        )
        st.stop()

else:
    matching_companies = company_names


selected_company = st.selectbox(
    "Select Company",
    matching_companies
)


ratios = get_ratios(selected_company)
pl = get_pl(selected_company)


if ratios.empty and pl.empty:
    st.warning(
        "No historical financial data is available for this company."
    )
    st.stop()


if not ratios.empty:
    ratios["year"] = pd.to_numeric(
        ratios["year"],
        errors="coerce"
    )


if not pl.empty:
    pl["year"] = pd.to_numeric(
        pl["year"],
        errors="coerce"
    )


metrics = {}


if "return_on_equity_pct" in ratios.columns:
    metrics["ROE"] = (
        "ratios",
        "return_on_equity_pct"
    )


if "operating_profit_margin_pct" in ratios.columns:
    metrics["Operating Profit Margin"] = (
        "ratios",
        "operating_profit_margin_pct"
    )


if "net_profit_margin_pct" in ratios.columns:
    metrics["Net Profit Margin"] = (
        "ratios",
        "net_profit_margin_pct"
    )


if "debt_to_equity" in ratios.columns:
    metrics["Debt / Equity"] = (
        "ratios",
        "debt_to_equity"
    )


if "interest_coverage" in ratios.columns:
    metrics["Interest Coverage"] = (
        "ratios",
        "interest_coverage"
    )


if "free_cash_flow_cr" in ratios.columns:
    metrics["Free Cash Flow"] = (
        "ratios",
        "free_cash_flow_cr"
    )


if "revenue_cagr_5yr" in ratios.columns:
    metrics["Revenue CAGR 5Y"] = (
        "ratios",
        "revenue_cagr_5yr"
    )


if "pat_cagr_5yr" in ratios.columns:
    metrics["PAT CAGR 5Y"] = (
        "ratios",
        "pat_cagr_5yr"
    )


if not pl.empty:

    if "sales" in pl.columns:
        metrics["Revenue"] = (
            "pl",
            "sales"
        )

    if "net_profit" in pl.columns:
        metrics["Net Profit"] = (
            "pl",
            "net_profit"
        )


if not metrics:
    st.error(
        "No historical financial metrics were found."
    )
    st.stop()


st.subheader("Select up to 3 metrics")


selected_metrics = st.multiselect(
    "Choose the metrics you want to compare",
    options=list(metrics.keys()),
    default=["ROE"],
    max_selections=3
)


if not selected_metrics:
    st.info(
        "Select at least one metric to display the graph."
    )
    st.stop()


def prepare_metric_data(source, column):

    data = source[["year", column]].copy()

    data.columns = ["year", "value"]

    data["value"] = pd.to_numeric(
        data["value"],
        errors="coerce"
    )

    data = data.dropna(
        subset=["year", "value"]
    )

    data = (
        data
        .groupby("year", as_index=False)["value"]
        .mean()
        .sort_values("year")
    )

    data = data.tail(10).copy()

    data["yoy"] = (
        data["value"]
        .pct_change()
        .mul(100)
    )

    return data


fig = go.Figure()


for metric in selected_metrics:

    source_name, column = metrics[metric]

    if source_name == "ratios":
        source = ratios
    else:
        source = pl


    data = prepare_metric_data(
        source,
        column
    )


    if data.empty:
        continue


    fig.add_trace(
        go.Scatter(
            x=data["year"],
            y=data["value"],
            mode="lines+markers",
            name=metric,
            line=dict(width=3),
            marker=dict(size=8),
            customdata=data["yoy"],
            hovertemplate=(
                "<b>%{fullData.name}</b><br>"
                "Year: %{x}<br>"
                "Value: %{y:.2f}<br>"
                "YoY Change: %{customdata:.2f}%"
                "<extra></extra>"
            )
        )
    )


    for _, row in data.iterrows():

        if pd.isna(row["yoy"]):
            yoy_text = "N/A"
        else:
            yoy_text = f"{row['yoy']:+.1f}%"


        fig.add_annotation(
            x=row["year"],
            y=row["value"],
            text=yoy_text,
            showarrow=False,
            yshift=16,
            font=dict(
                size=10,
                color="#555555"
            )
        )


fig.update_layout(
    title=f"10-Year Trend - {selected_company}",
    template="plotly_white",
    height=600,
    hovermode="x unified",
    xaxis_title="Year",
    yaxis_title="Value",
    margin=dict(
        l=50,
        r=30,
        t=80,
        b=50
    ),
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="left",
        x=0
    )
)


fig.update_xaxes(
    dtick=1,
    showgrid=False
)


fig.update_yaxes(
    showgrid=True,
    gridcolor="#eeeeee"
)


st.subheader("Financial Trend")


st.plotly_chart(
    fig,
    use_container_width=True
)


available_years = set()


for metric in selected_metrics:

    source_name, column = metrics[metric]

    if source_name == "ratios":
        source = ratios
    else:
        source = pl


    data = prepare_metric_data(
        source,
        column
    )


    if not data.empty:
        available_years.update(
            data["year"].tolist()
        )


if available_years:

    year_count = len(available_years)

    if year_count < 10:

        years = sorted(available_years)

        st.info(
            f"Historical data is available for {year_count} years "
            f"({int(min(years))} to {int(max(years))})."
        )
