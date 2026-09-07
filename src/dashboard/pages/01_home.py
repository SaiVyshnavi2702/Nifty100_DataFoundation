import pandas as pd
import plotly.express as px
import streamlit as st

from dashboard.utils.db import get_companies, get_ratios, get_sectors, get_valuation



st.set_page_config(
    page_title="Nifty 100 Analytics",
    layout="wide",
    initial_sidebar_state="expanded",
)


st.title("Nifty 100 Analytics")
st.write(
    "Overview of company quality, valuation and financial performance "
    "across the Nifty 100."
)


# Year selection
year = st.sidebar.selectbox(
    "Select Year",
    list(range(2019, 2025)),
    index=5,
)


companies = get_companies()
sectors = get_sectors()


# Get ratio data for all companies for the selected year.
ratio_rows = []

for company_id in companies["id"]:
    company_name = companies.loc[
        companies["id"] == company_id, "company_name"
    ].iloc[0]

    ratios = get_ratios(company_name, year)

    if not ratios.empty:
        row = ratios.iloc[0].copy()
        row["company_name"] = company_name
        ratio_rows.append(row)


if ratio_rows:
    ratios_df = pd.DataFrame(ratio_rows)
else:
    ratios_df = pd.DataFrame()


# Get valuation data for the selected year.
valuation_rows = []

for company_id in companies["id"]:
    company_name = companies.loc[
        companies["id"] == company_id, "company_name"
    ].iloc[0]

    valuation = get_valuation(company_name)

    if not valuation.empty:
        valuation = valuation[valuation["year"] == year]

        if not valuation.empty:
            row = valuation.iloc[0].copy()
            row["company_name"] = company_name
            valuation_rows.append(row)


if valuation_rows:
    valuation_df = pd.DataFrame(valuation_rows)
else:
    valuation_df = pd.DataFrame()


# Create the six KPI values.
if not ratios_df.empty:
    average_roe = ratios_df["return_on_equity_pct"].mean()
    median_de = ratios_df["debt_to_equity"].median()
    median_revenue_cagr = ratios_df["revenue_cagr_5yr"].median()

    debt_free_count = (
        ratios_df["debt_to_equity"]
        .dropna()
        .eq(0)
        .sum()
    )

    top_companies = (
        ratios_df[
            [
                "company_name",
                "composite_quality_score",
            ]
        ]
        .dropna(subset=["composite_quality_score"])
        .sort_values(
            "composite_quality_score",
            ascending=False,
        )
        .head(5)
    )
else:
    average_roe = None
    median_de = None
    median_revenue_cagr = None
    debt_free_count = 0
    top_companies = pd.DataFrame()


if not valuation_df.empty:
    median_pe = valuation_df["pe_ratio"].median()
else:
    median_pe = None


# KPI tiles
col1, col2, col3, col4, col5, col6 = st.columns(6)

with col1:
    st.metric(
        "Average ROE",
        f"{average_roe:.2f}%" if pd.notna(average_roe) else "N/A",
    )

with col2:
    st.metric(
        "Median P/E",
        f"{median_pe:.2f}" if pd.notna(median_pe) else "N/A",
    )

with col3:
    st.metric(
        "Median D/E",
        f"{median_de:.2f}" if pd.notna(median_de) else "N/A",
    )

with col4:
    st.metric(
        "Total Companies",
        companies["id"].nunique(),
    )

with col5:
    st.metric(
        "Median Revenue CAGR 5yr",
        (
            f"{median_revenue_cagr:.2f}%"
            if pd.notna(median_revenue_cagr)
            else "N/A"
        ),
    )

with col6:
    st.metric(
        "Debt-Free Companies",
        int(debt_free_count),
    )


st.divider()


# Sector breakdown
st.subheader(f"Sector Breakdown — {year}")

sector_counts = (
    sectors.groupby("broad_sector")["company_id"]
    .nunique()
    .reset_index(name="company_count")
    .sort_values("company_count", ascending=False)
)


fig = px.pie(
    sector_counts,
    names="broad_sector",
    values="company_count",
    hole=0.55,
)


fig.update_layout(
    showlegend=True,
    margin=dict(t=20, b=20, l=20, r=20),
)


st.plotly_chart(
    fig,
    use_container_width=True,
)


# Top five companies
st.subheader(f"Top 5 Companies by Composite Quality Score — {year}")


if not top_companies.empty:
    top_companies = top_companies.rename(
        columns={
            "company_name": "Company",
            "composite_quality_score": "Composite Quality Score",
        }
    )

    st.dataframe(
        top_companies,
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info(
        "No composite quality score data is available for the selected year."
    )