import pandas as pd
import streamlit as st
import plotly.graph_objects as go

from dashboard.utils.db import (
    get_companies,
    get_ratios,
    get_pl,
    get_pros_and_cons,
    get_company_sector,
)


st.set_page_config(
    page_title="Company Profile",
    layout="wide",
)


st.title("Company Profile")

st.write(
    "Search for a company to view its profile, financial performance, "
    "and key information."
)


companies = get_companies()

if companies.empty:
    st.warning("No company data is available.")
    st.stop()


search = st.text_input(
    "Search company",
    placeholder="Type company name or ticker",
)


if search:
    search_text = search.strip().lower()

    matches = companies[
        companies["company_name"].astype(str).str.lower().str.contains(
            search_text,
            na=False,
        )
        |
        companies["id"].astype(str).str.lower().str.contains(
            search_text,
            na=False,
        )
    ]

    if matches.empty:
        st.warning("Ticker not found — please try another")
        st.stop()

    selected_company = st.selectbox(
        "Select company",
        matches["company_name"].tolist(),
    )
else:
    selected_company = st.selectbox(
        "Select company",
        companies["company_name"].tolist(),
    )


company = companies[
    companies["company_name"] == selected_company
].iloc[0]

ticker = company["id"]


sector_data = get_company_sector(selected_company)

if not sector_data.empty:
    sector = sector_data.iloc[0]["broad_sector"]
    sub_sector = sector_data.iloc[0]["sub_sector"]
else:
    sector = "Not available"
    sub_sector = "Not available"


st.subheader(selected_company)

col1, col2, col3 = st.columns(3)

with col1:
    st.write("**NSE Ticker**")
    st.write(ticker)

with col2:
    st.write("**Sector**")
    st.write(sector)

with col3:
    st.write("**Sub-sector**")
    st.write(sub_sector)


about = company["about_company"]

if pd.notna(about) and str(about).strip():
    st.write(about)
else:
    st.write("Company description is not available.")


ratios = get_ratios(selected_company)

if ratios.empty:
    st.warning("Financial data is not available for this company.")
    st.stop()


ratios["year"] = pd.to_numeric(
    ratios["year"],
    errors="coerce",
)

ratios = ratios.dropna(
    subset=["year"]
)

ratios["year"] = ratios["year"].astype(int)

ratios = ratios.sort_values(
    "year",
    ascending=False,
)


# Day 27: Check whether the company has fewer than 10 years of data.
available_years = sorted(ratios["year"].unique())

if len(available_years) < 10:
    st.info(
        f"Financial data is available for {len(available_years)} years "
        f"({min(available_years)}–{max(available_years)}). "
        "Metrics and charts are displayed using the available data."
    )


latest = ratios.iloc[0]


# Safely read latest financial metrics.
roe = latest.get("return_on_equity_pct")
net_margin = latest.get("net_profit_margin_pct")
debt_equity = latest.get("debt_to_equity")
revenue_cagr = latest.get("revenue_cagr_5yr")
fcf = latest.get("free_cash_flow_cr")
roce = company.get("roce_percentage")


st.subheader("Key Financial Metrics")


col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "ROE",
        f"{roe:.2f}%" if pd.notna(roe) else "N/A",
    )

with col2:
    st.metric(
        "ROCE",
        f"{roce:.2f}%" if pd.notna(roce) else "N/A",
    )

with col3:
    st.metric(
        "Net Profit Margin",
        f"{net_margin:.2f}%"
        if pd.notna(net_margin)
        else "N/A",
    )


col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "D/E",
        f"{debt_equity:.2f}"
        if pd.notna(debt_equity)
        else "N/A",
    )

with col2:
    st.metric(
        "Revenue CAGR 5yr",
        f"{revenue_cagr:.2f}%"
        if pd.notna(revenue_cagr)
        else "N/A",
    )

with col3:
    st.metric(
        "FCF",
        f"{fcf:,.2f} Cr"
        if pd.notna(fcf)
        else "N/A",
    )


st.subheader("Revenue and Net Profit")


pl_data = get_pl(selected_company)

if not pl_data.empty:

    pl_data["year"] = pd.to_numeric(
        pl_data["year"],
        errors="coerce",
    )

    pl_data = pl_data.dropna(
        subset=["year"]
    )

    pl_data["year"] = pl_data["year"].astype(int)

    # Safely convert chart values to numeric.
    if "sales" in pl_data.columns:
        pl_data["sales"] = pd.to_numeric(
            pl_data["sales"],
            errors="coerce",
        )

    if "net_profit" in pl_data.columns:
        pl_data["net_profit"] = pd.to_numeric(
            pl_data["net_profit"],
            errors="coerce",
        )

    pl_data = pl_data.sort_values(
        "year"
    ).tail(10)

    revenue_profit_chart = go.Figure()

    # Add Revenue only when the column exists and has valid data.
    if (
        "sales" in pl_data.columns
        and pl_data["sales"].notna().any()
    ):
        revenue_profit_chart.add_trace(
            go.Bar(
                x=pl_data["year"],
                y=pl_data["sales"],
                name="Revenue",
            )
        )

    # Add Net Profit only when the column exists and has valid data.
    if (
        "net_profit" in pl_data.columns
        and pl_data["net_profit"].notna().any()
    ):
        revenue_profit_chart.add_trace(
            go.Bar(
                x=pl_data["year"],
                y=pl_data["net_profit"],
                name="Net Profit",
            )
        )

    if len(revenue_profit_chart.data) > 0:

        revenue_profit_chart.update_layout(
            barmode="group",
            xaxis_title="Year",
            yaxis_title="Amount",
            height=450,
        )

        st.plotly_chart(
            revenue_profit_chart,
            use_container_width=True,
        )

    else:
        st.info(
            "Revenue and Net Profit data is not available."
        )

else:
    st.info(
        "Profit and loss data is not available."
    )


st.subheader("ROE and ROCE Trend")


trend_data = ratios.sort_values(
    "year"
).tail(10).copy()


trend_data["return_on_equity_pct"] = pd.to_numeric(
    trend_data["return_on_equity_pct"],
    errors="coerce",
)


# Check whether ROE data is available
roe_available = trend_data["return_on_equity_pct"].notna().any()

# Check whether ROCE data is available
roce_available = pd.notna(roce)


if roe_available and roce_available:

    roe_roce_chart = go.Figure()

    roe_roce_chart.add_trace(
        go.Scatter(
            x=trend_data["year"],
            y=trend_data["return_on_equity_pct"],
            mode="lines+markers",
            name="ROE",
            line=dict(
                color="#1f77b4",
                width=2,
            ),
            marker=dict(
                size=7,
            ),
        )
    )

    roe_roce_chart.add_trace(
        go.Scatter(
            x=trend_data["year"],
            y=[roce] * len(trend_data),
            mode="lines+markers",
            name="ROCE",
            yaxis="y2",
            line=dict(
                color="#ff7f0e",
                width=2,
            ),
            marker=dict(
                size=7,
            ),
        )
    )

    roe_roce_chart.update_layout(
        height=450,
        xaxis=dict(
            title="Year",
        ),
        yaxis=dict(
            title="ROE (%)",
            side="left",
            showgrid=True,
        ),
        yaxis2=dict(
            title="ROCE (%)",
            side="right",
            overlaying="y",
            showgrid=False,
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
    )

    st.plotly_chart(
        roe_roce_chart,
        use_container_width=True,
    )

else:

    st.info(
        "ROE and ROCE trend data is not available."
    )



st.subheader("Pros and Cons")


pros_cons = get_pros_and_cons(
    selected_company
)


if not pros_cons.empty:

    col1, col2 = st.columns(2)

    with col1:

        st.markdown("### Pros")

        pros_found = False

        for value in pros_cons["pros"]:

            if pd.notna(value) and str(value).strip():

                pros_found = True

                st.success(
                    "✓ " + str(value).strip()
                )

        if not pros_found:
            st.write(
                "No pros available."
            )


    with col2:

        st.markdown("### Cons")

        cons_found = False

        for value in pros_cons["cons"]:

            if pd.notna(value) and str(value).strip():

                cons_found = True

                st.error(
                    "✗ " + str(value).strip()
                )

        if not cons_found:
            st.write(
                "No cons available."
            )

else:

    st.info(
        "Pros and cons are not available for this company."
    )
