import pandas as pd
import plotly.express as px
import streamlit as st

from dashboard.utils.db import (
    get_companies,
    get_ratios,
    get_sectors,
)


st.title("💰 Capital Allocation Map")

st.write(
    "Explore companies grouped into capital allocation patterns "
    "based on growth, profitability, cash generation, debt and dividends."
)


companies = get_companies()
sectors = get_sectors()


if companies.empty:
    st.warning("Company data is not available.")
    st.stop()


if sectors.empty:
    st.warning("Sector data is not available.")
    st.stop()


sector_data = sectors[
    [
        "company_id",
        "broad_sector",
        "sub_sector",
        "company_name",
    ]
].copy()


sector_data = sector_data.drop_duplicates(
    subset=["company_id"]
)


company_lookup = companies[
    ["id", "company_name"]
].copy()


company_lookup = company_lookup.rename(
    columns={
        "id": "company_id",
        "company_name": "company_from_companies",
    }
)


sector_data = sector_data.merge(
    company_lookup,
    on="company_id",
    how="left",
)


rows = []


for _, company in sector_data.iterrows():

    company_id = company["company_id"]
    company_name = company["company_name"]

    if pd.isna(company_name):
        company_name = company["company_from_companies"]

    if pd.isna(company_name):
        continue

    ratios = get_ratios(company_name)

    if ratios.empty:
        continue

    ratios = ratios.copy()

    ratios["year"] = pd.to_numeric(
        ratios["year"],
        errors="coerce",
    )

    ratios = ratios.dropna(
        subset=["year"]
    )

    if ratios.empty:
        continue

    ratios = ratios.sort_values(
        "year",
        ascending=False,
    )

    latest = ratios.iloc[0]

    rows.append(
        {
            "company_id": company_id,
            "Company": company_name,
            "Year": latest.get("year"),
            "Sector": company.get(
                "broad_sector",
                "Unknown",
            ),
            "Sub-sector": company.get(
                "sub_sector",
                "Unknown",
            ),
            "ROE": latest.get(
                "return_on_equity_pct"
            ),
            "D/E": latest.get(
                "debt_to_equity"
            ),
            "FCF": latest.get(
                "free_cash_flow_cr"
            ),
            "Revenue CAGR": latest.get(
                "revenue_cagr_5yr"
            ),
            "PAT CAGR": latest.get(
                "pat_cagr_5yr"
            ),
            "Dividend Payout": latest.get(
                "dividend_payout_ratio_pct"
            ),
            "Debt": latest.get(
                "total_debt_cr"
            ),
            "Cash From Operations": latest.get(
                "cash_from_operations_cr"
            ),
        }
    )


capital_df = pd.DataFrame(rows)


if capital_df.empty:
    st.warning(
        "No financial data is available for the "
        "capital allocation analysis."
    )
    st.stop()


numeric_columns = [
    "ROE",
    "D/E",
    "FCF",
    "Revenue CAGR",
    "PAT CAGR",
    "Dividend Payout",
    "Debt",
    "Cash From Operations",
]


for column in numeric_columns:

    capital_df[column] = pd.to_numeric(
        capital_df[column],
        errors="coerce",
    )


def classify_company(row):

    roe = row["ROE"]
    debt_equity = row["D/E"]
    fcf = row["FCF"]
    revenue_cagr = row["Revenue CAGR"]
    pat_cagr = row["PAT CAGR"]
    dividend = row["Dividend Payout"]
    cash_flow = row["Cash From Operations"]

    roe = 0 if pd.isna(roe) else roe
    debt_equity = 0 if pd.isna(debt_equity) else debt_equity
    fcf = 0 if pd.isna(fcf) else fcf
    revenue_cagr = 0 if pd.isna(revenue_cagr) else revenue_cagr
    pat_cagr = 0 if pd.isna(pat_cagr) else pat_cagr
    dividend = 0 if pd.isna(dividend) else dividend
    cash_flow = 0 if pd.isna(cash_flow) else cash_flow

    if (
        revenue_cagr >= 15
        and pat_cagr >= 15
        and roe >= 15
    ):
        return "High Growth"

    if (
        revenue_cagr >= 10
        and pat_cagr >= 10
        and roe >= 20
    ):
        return "Growth + High Return"

    if (
        fcf > 0
        and cash_flow > 0
        and roe >= 15
    ):
        return "Cash Generator"

    if dividend >= 30:
        return "Dividend Focus"

    if (
        debt_equity <= 0.50
        and cash_flow > 0
    ):
        return "Debt Reduction"

    if (
        debt_equity > 1.00
        and roe < 15
    ):
        return "Capital Intensive"

    if (
        revenue_cagr > 0
        and pat_cagr > 0
        and roe < 10
    ):
        return "Turnaround"

    return "Balanced Allocator"


capital_df["Pattern"] = capital_df.apply(
    classify_company,
    axis=1,
)


patterns = [
    "High Growth",
    "Growth + High Return",
    "Cash Generator",
    "Dividend Focus",
    "Debt Reduction",
    "Capital Intensive",
    "Turnaround",
    "Balanced Allocator",
]


company_count = capital_df["Company"].nunique()


if company_count == 92:

    st.success(
        "All 92 companies are classified across "
        "8 capital allocation patterns."
    )

else:

    st.warning(
        f"{company_count} companies are currently classified. "
        "The expected universe contains 92 companies."
    )


pattern_summary = (
    capital_df.groupby("Pattern")
    .size()
    .reset_index(name="Companies")
)


pattern_summary = pd.DataFrame(
    {
        "Pattern": patterns,
    }
).merge(
    pattern_summary,
    on="Pattern",
    how="left",
)


pattern_summary["Companies"] = (
    pattern_summary["Companies"]
    .fillna(0)
    .astype(int)
)


st.subheader("Capital Allocation Patterns")

st.caption(
    f"{company_count} companies classified across "
    f"{len(patterns)} capital allocation patterns."
)


treemap_df = pattern_summary[
    pattern_summary["Companies"] > 0
].copy()


if treemap_df.empty:

    st.info(
        "No capital allocation patterns are available."
    )

else:

    fig = px.treemap(
        treemap_df,
        path=["Pattern"],
        values="Companies",
        color="Companies",
        color_continuous_scale="Blues",
    )

    fig.update_traces(
        textinfo="label+value",
        hovertemplate=(
            "<b>%{label}</b><br>"
            "Companies: %{value}"
            "<extra></extra>"
        ),
    )

    fig.update_layout(
        title="Companies by Capital Allocation Pattern",
        template="plotly_white",
        height=600,
        margin=dict(
            l=20,
            r=20,
            t=70,
            b=20,
        ),
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )


st.subheader(
    "Companies in Capital Allocation Pattern"
)


selected_pattern = st.selectbox(
    "Select a Pattern",
    patterns,
)


selected_companies = capital_df[
    capital_df["Pattern"] == selected_pattern
].copy()


if selected_companies.empty:

    st.info(
        f"No companies are currently classified under "
        f"'{selected_pattern}'."
    )

else:

    st.success(
        f"{len(selected_companies)} companies "
        f"are classified as {selected_pattern}."
    )

    display_df = selected_companies[
        [
            "Company",
            "Sector",
            "Sub-sector",
            "ROE",
            "D/E",
            "FCF",
            "Revenue CAGR",
            "PAT CAGR",
            "Dividend Payout",
        ]
    ].copy()

    display_df = display_df.rename(
        columns={
            "ROE": "ROE (%)",
            "D/E": "D/E",
            "FCF": "FCF (Cr)",
            "Revenue CAGR": "Revenue CAGR (%)",
            "PAT CAGR": "PAT CAGR (%)",
            "Dividend Payout": "Dividend Payout (%)",
        }
    )

    display_df = display_df.round(2)

    display_df = display_df.fillna("N/A")

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
    )


st.subheader("Pattern Summary")

st.dataframe(
    pattern_summary,
    use_container_width=True,
    hide_index=True,
)
