import pandas as pd
import plotly.express as px
import streamlit as st

from dashboard.utils.db import (
    get_ratios,
    get_sectors,
    get_valuation,
    get_pl,
)


st.title("📊 Sector Analysis")

st.write(
    "Compare companies within a sector using revenue, ROE, "
    "and market capitalisation."
)


sectors = get_sectors()


if sectors.empty:
    st.warning("Sector data is not available.")
    st.stop()


sector_names = sorted(
    sectors["broad_sector"]
    .dropna()
    .unique()
    .tolist()
)


selected_sector = st.selectbox(
    "Select Sector",
    sector_names
)


sector_companies = sectors[
    sectors["broad_sector"] == selected_sector
].copy()


if sector_companies.empty:
    st.warning("No companies found in this sector.")
    st.stop()


rows = []


for _, company in sector_companies.iterrows():

    company_name = company["company_name"]

    revenue = None
    roe = None
    market_cap = None

    # Get latest available ROE
    ratios = get_ratios(company_name)

    if not ratios.empty:

        ratios = ratios.copy()

        ratios["year"] = pd.to_numeric(
            ratios["year"],
            errors="coerce"
        )

        ratios = ratios.dropna(
            subset=["year"]
        )

        if not ratios.empty:

            latest_year = ratios["year"].max()

            latest_ratio = ratios[
                ratios["year"] == latest_year
            ]

            if not latest_ratio.empty:

                roe = latest_ratio.iloc[0].get(
                    "return_on_equity_pct"
                )

    # Get latest available Revenue
    profit_loss = get_pl(company_name)

    if not profit_loss.empty:

        profit_loss = profit_loss.copy()

        profit_loss["year"] = pd.to_numeric(
            profit_loss["year"],
            errors="coerce"
        )

        profit_loss = profit_loss.dropna(
            subset=["year"]
        )

        if not profit_loss.empty:

            latest_year = profit_loss["year"].max()

            latest_pl = profit_loss[
                profit_loss["year"] == latest_year
            ]

            if not latest_pl.empty:

                revenue = latest_pl.iloc[0].get(
                    "sales"
                )

    # Get latest available Market Cap
    valuation = get_valuation(company_name)

    if not valuation.empty:

        valuation = valuation.copy()

        valuation["year"] = pd.to_numeric(
            valuation["year"],
            errors="coerce"
        )

        valuation = valuation.dropna(
            subset=["year"]
        )

        if not valuation.empty:

            latest_year = valuation["year"].max()

            latest_valuation = valuation[
                valuation["year"] == latest_year
            ]

            if not latest_valuation.empty:

                market_cap = latest_valuation.iloc[0].get(
                    "market_cap_crore"
                )

    rows.append(
        {
            "Company": company_name,
            "Sub-sector": company["sub_sector"],
            "Revenue": revenue,
            "ROE": roe,
            "Market Cap": market_cap,
        }
    )


sector_df = pd.DataFrame(rows)


# Convert all numeric columns safely
sector_df["Revenue"] = pd.to_numeric(
    sector_df["Revenue"],
    errors="coerce"
)

sector_df["ROE"] = pd.to_numeric(
    sector_df["ROE"],
    errors="coerce"
)

sector_df["Market Cap"] = pd.to_numeric(
    sector_df["Market Cap"],
    errors="coerce"
)


# ---------------------------------------------------------
# Company Bubble Chart
# ---------------------------------------------------------

st.subheader(
    f"{selected_sector} Company Comparison"
)


chart_df = sector_df.dropna(
    subset=[
        "Revenue",
        "ROE",
        "Market Cap",
    ]
).copy()


if chart_df.empty:

    st.info(
        "There is not enough complete data to display "
        "the sector bubble chart."
    )

else:

    fig = px.scatter(
        chart_df,
        x="Revenue",
        y="ROE",
        size="Market Cap",
        color="Sub-sector",
        hover_name="Company",
        hover_data={
            "Revenue": ":,.2f",
            "ROE": ":.2f",
            "Market Cap": ":,.2f",
        },
        size_max=60,
    )

    fig.update_traces(
        marker=dict(
            opacity=0.75,
            line=dict(
                width=1,
                color="white",
            ),
        )
    )

    fig.update_layout(
        title=f"{selected_sector} Companies",
        template="plotly_white",
        height=600,
        xaxis_title="Revenue (Cr)",
        yaxis_title="ROE (%)",
        margin=dict(
            l=50,
            r=30,
            t=70,
            b=50,
        ),
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )


# ---------------------------------------------------------
# Sector Median KPI Bar Charts
# ---------------------------------------------------------

st.subheader(
    f"{selected_sector} Median KPIs"
)


median_revenue = sector_df["Revenue"].median()
median_roe = sector_df["ROE"].median()
median_market_cap = sector_df["Market Cap"].median()


median_col1, median_col2, median_col3 = st.columns(3)


# Revenue median
with median_col1:

    if pd.isna(median_revenue):

        st.info("Revenue data unavailable.")

    else:

        revenue_data = pd.DataFrame(
            {
                "Metric": ["Revenue"],
                "Value": [median_revenue],
            }
        )

        revenue_fig = px.bar(
            revenue_data,
            x="Metric",
            y="Value",
            text="Value",
        )

        revenue_fig.update_traces(
            marker_color="#4C78A8",
            texttemplate="%{text:,.0f} Cr",
            textposition="outside",
        )

        revenue_fig.update_layout(
            title="Median Revenue",
            template="plotly_white",
            height=350,
            showlegend=False,
            xaxis_title="",
            yaxis_title="₹ Crore",
            margin=dict(
                l=20,
                r=20,
                t=60,
                b=30,
            ),
        )

        st.plotly_chart(
            revenue_fig,
            use_container_width=True,
        )


# ROE median
with median_col2:

    if pd.isna(median_roe):

        st.info("ROE data unavailable.")

    else:

        roe_data = pd.DataFrame(
            {
                "Metric": ["ROE"],
                "Value": [median_roe],
            }
        )

        roe_fig = px.bar(
            roe_data,
            x="Metric",
            y="Value",
            text="Value",
        )

        roe_fig.update_traces(
            marker_color="#59A14F",
            texttemplate="%{text:.2f}%",
            textposition="outside",
        )

        roe_fig.update_layout(
            title="Median ROE",
            template="plotly_white",
            height=350,
            showlegend=False,
            xaxis_title="",
            yaxis_title="Percent",
            margin=dict(
                l=20,
                r=20,
                t=60,
                b=30,
            ),
        )

        st.plotly_chart(
            roe_fig,
            use_container_width=True,
        )


# Market cap median
with median_col3:

    if pd.isna(median_market_cap):

        st.info("Market cap data unavailable.")

    else:

        market_cap_data = pd.DataFrame(
            {
                "Metric": ["Market Cap"],
                "Value": [median_market_cap],
            }
        )

        market_cap_fig = px.bar(
            market_cap_data,
            x="Metric",
            y="Value",
            text="Value",
        )

        market_cap_fig.update_traces(
            marker_color="#F28E2B",
            texttemplate="%{text:,.0f} Cr",
            textposition="outside",
        )

        market_cap_fig.update_layout(
            title="Median Market Cap",
            template="plotly_white",
            height=350,
            showlegend=False,
            xaxis_title="",
            yaxis_title="₹ Crore",
            margin=dict(
                l=20,
                r=20,
                t=60,
                b=30,
            ),
        )

        st.plotly_chart(
            market_cap_fig,
            use_container_width=True,
        )


# ---------------------------------------------------------
# Companies Table
# ---------------------------------------------------------

st.subheader(
    "Companies in Selected Sector"
)


display_df = sector_df[
    [
        "Company",
        "Sub-sector",
        "Revenue",
        "ROE",
        "Market Cap",
    ]
].copy()


display_df = display_df.rename(
    columns={
        "Revenue": "Revenue (Cr)",
        "ROE": "ROE (%)",
        "Market Cap": "Market Cap (Cr)",
    }
)


display_df["Revenue (Cr)"] = display_df[
    "Revenue (Cr)"
].round(2)


display_df["ROE (%)"] = display_df[
    "ROE (%)"
].round(2)


display_df["Market Cap (Cr)"] = display_df[
    "Market Cap (Cr)"
].round(2)


# Show N/A instead of blank/NaN values
display_df = display_df.fillna("N/A")


st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True,
)
