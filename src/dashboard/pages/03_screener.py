import pandas as pd
import streamlit as st

from dashboard.utils.db import get_companies, get_ratios, get_sectors, get_valuation


st.title("Screener")

st.write(
    "Screen Nifty 100 companies using financial, growth, valuation, "
    "dividend and debt-related criteria."
)


companies = get_companies()

if companies.empty:
    st.warning("No company data is available.")
    st.stop()


ratio_rows = []

for _, company in companies.iterrows():
    company_name = company["company_name"]

    data = get_ratios(company_name, 2024)

    if not data.empty:
        row = data.iloc[0].copy()
        row["company_id"] = company["id"]
        row["company_name"] = company_name
        ratio_rows.append(row)


if not ratio_rows:
    st.warning("No financial ratio data is available for screening.")
    st.stop()


ratios_df = pd.DataFrame(ratio_rows)

sectors = get_sectors()

sector_df = (
    sectors[["company_id", "broad_sector"]]
    .drop_duplicates("company_id")
)


valuation_rows = []

for _, company in companies.iterrows():
    company_name = company["company_name"]

    valuation = get_valuation(company_name)

    if not valuation.empty:
        valuation = valuation[valuation["year"] == 2024]

        if not valuation.empty:
            row = valuation.iloc[0].copy()
            row["company_id"] = company["id"]
            row["company_name"] = company_name
            valuation_rows.append(row)


if valuation_rows:
    valuation_df = pd.DataFrame(valuation_rows)
else:
    valuation_df = pd.DataFrame(
        columns=[
            "company_id",
            "pe_ratio",
            "pb_ratio",
            "dividend_yield_pct",
        ]
    )


screen_df = ratios_df.merge(
    sector_df,
    on="company_id",
    how="left",
)

if not valuation_df.empty:
    screen_df = screen_df.merge(
        valuation_df[
            [
                "company_id",
                "pe_ratio",
                "pb_ratio",
                "dividend_yield_pct",
            ]
        ],
        on="company_id",
        how="left",
    )
else:
    screen_df["pe_ratio"] = pd.NA
    screen_df["pb_ratio"] = pd.NA
    screen_df["dividend_yield_pct"] = pd.NA


presets = {
    "Quality": {
        "roe_min": 15.0,
        "de_max": 1.0,
        "fcf_min": 0.0,
        "revenue_cagr_min": 10.0,
        "pat_cagr_min": 10.0,
        "opm_min": 15.0,
        "pe_max": 50.0,
        "pb_max": 8.0,
        "dividend_min": 0.0,
        "icr_min": 3.0,
    },
    "Value": {
        "roe_min": 10.0,
        "de_max": 2.0,
        "fcf_min": 0.0,
        "revenue_cagr_min": 0.0,
        "pat_cagr_min": 0.0,
        "opm_min": 0.0,
        "pe_max": 25.0,
        "pb_max": 4.0,
        "dividend_min": 1.0,
        "icr_min": 1.5,
    },
    "Growth": {
        "roe_min": 15.0,
        "de_max": 2.0,
        "fcf_min": 0.0,
        "revenue_cagr_min": 15.0,
        "pat_cagr_min": 15.0,
        "opm_min": 10.0,
        "pe_max": 80.0,
        "pb_max": 12.0,
        "dividend_min": 0.0,
        "icr_min": 1.5,
    },
    "Dividend": {
        "roe_min": 8.0,
        "de_max": 2.0,
        "fcf_min": 0.0,
        "revenue_cagr_min": 0.0,
        "pat_cagr_min": 0.0,
        "opm_min": 0.0,
        "pe_max": 60.0,
        "pb_max": 10.0,
        "dividend_min": 3.0,
        "icr_min": 1.5,
    },
    "Debt-Free": {
        "roe_min": 10.0,
        "de_max": 0.1,
        "fcf_min": 0.0,
        "revenue_cagr_min": 0.0,
        "pat_cagr_min": 0.0,
        "opm_min": 0.0,
        "pe_max": 80.0,
        "pb_max": 12.0,
        "dividend_min": 0.0,
        "icr_min": 3.0,
    },
    "Turnaround": {
        "roe_min": 5.0,
        "de_max": 3.0,
        "fcf_min": 0.0,
        "revenue_cagr_min": 5.0,
        "pat_cagr_min": 5.0,
        "opm_min": 5.0,
        "pe_max": 60.0,
        "pb_max": 8.0,
        "dividend_min": 0.0,
        "icr_min": 1.5,
    },
}


if "screener_roe_min" not in st.session_state:
    st.session_state.screener_roe_min = 0.0

if "screener_de_max" not in st.session_state:
    st.session_state.screener_de_max = 20.0

if "screener_fcf_min" not in st.session_state:
    st.session_state.screener_fcf_min = -10000.0

if "screener_revenue_cagr_min" not in st.session_state:
    st.session_state.screener_revenue_cagr_min = -50.0

if "screener_pat_cagr_min" not in st.session_state:
    st.session_state.screener_pat_cagr_min = -50.0

if "screener_opm_min" not in st.session_state:
    st.session_state.screener_opm_min = -50.0

if "screener_pe_max" not in st.session_state:
    st.session_state.screener_pe_max = 200.0

if "screener_pb_max" not in st.session_state:
    st.session_state.screener_pb_max = 50.0

if "screener_dividend_min" not in st.session_state:
    st.session_state.screener_dividend_min = 0.0

if "screener_icr_min" not in st.session_state:
    st.session_state.screener_icr_min = -20.0


st.sidebar.subheader("Presets")

preset_columns = st.sidebar.columns(2)

preset_names = list(presets.keys())

for index, preset_name in enumerate(preset_names):
    column = preset_columns[index % 2]

    if column.button(
        preset_name,
        key=f"preset_{preset_name}",
        use_container_width=True,
    ):
        values = presets[preset_name]

        for key, value in values.items():
            st.session_state[f"screener_{key}"] = value

        st.rerun()


st.sidebar.subheader("Screening Filters")

roe_min = st.sidebar.slider(
    "ROE minimum (%)",
    min_value=0.0,
    max_value=100.0,
    key="screener_roe_min",
)

de_max = st.sidebar.slider(
    "D/E maximum",
    min_value=0.0,
    max_value=20.0,
    key="screener_de_max",
)

fcf_min = st.sidebar.slider(
    "FCF minimum (Cr)",
    min_value=-10000.0,
    max_value=100000.0,
    step=100.0,
    key="screener_fcf_min",
)

revenue_cagr_min = st.sidebar.slider(
    "Revenue CAGR minimum (%)",
    min_value=-50.0,
    max_value=100.0,
    key="screener_revenue_cagr_min",
)

pat_cagr_min = st.sidebar.slider(
    "PAT CAGR minimum (%)",
    min_value=-50.0,
    max_value=100.0,
    key="screener_pat_cagr_min",
)

opm_min = st.sidebar.slider(
    "OPM minimum (%)",
    min_value=-50.0,
    max_value=100.0,
    key="screener_opm_min",
)

pe_max = st.sidebar.slider(
    "P/E maximum",
    min_value=0.0,
    max_value=200.0,
    key="screener_pe_max",
)

pb_max = st.sidebar.slider(
    "P/B maximum",
    min_value=0.0,
    max_value=50.0,
    key="screener_pb_max",
)

dividend_min = st.sidebar.slider(
    "Dividend Yield minimum (%)",
    min_value=0.0,
    max_value=20.0,
    key="screener_dividend_min",
)

icr_min = st.sidebar.slider(
    "ICR minimum",
    min_value=-20.0,
    max_value=50.0,
    key="screener_icr_min",
)


filtered = screen_df.copy()


def apply_min_filter(data, column, minimum):
    if column not in data.columns:
        return data

    values = pd.to_numeric(
        data[column],
        errors="coerce",
    )

    return data[
        values.fillna(float("-inf")) >= minimum
    ]


def apply_max_filter(data, column, maximum):
    if column not in data.columns:
        return data

    values = pd.to_numeric(
        data[column],
        errors="coerce",
    )

    return data[
        values.fillna(float("inf")) <= maximum
    ]


filtered = apply_min_filter(
    filtered,
    "return_on_equity_pct",
    roe_min,
)

filtered = apply_max_filter(
    filtered,
    "debt_to_equity",
    de_max,
)

filtered = apply_min_filter(
    filtered,
    "free_cash_flow_cr",
    fcf_min,
)

filtered = apply_min_filter(
    filtered,
    "revenue_cagr_5yr",
    revenue_cagr_min,
)

filtered = apply_min_filter(
    filtered,
    "pat_cagr_5yr",
    pat_cagr_min,
)

filtered = apply_min_filter(
    filtered,
    "operating_profit_margin_pct",
    opm_min,
)

filtered = apply_max_filter(
    filtered,
    "pe_ratio",
    pe_max,
)

filtered = apply_max_filter(
    filtered,
    "pb_ratio",
    pb_max,
)

filtered = apply_min_filter(
    filtered,
    "dividend_yield_pct",
    dividend_min,
)

filtered = apply_min_filter(
    filtered,
    "interest_coverage",
    icr_min,
)


st.subheader("Screening Results")

st.write(
    f"**{len(filtered)} companies match your filters**"
)


visible_columns = [
    "company_id",
    "company_name",
    "broad_sector",
    "composite_quality_score",
    "return_on_equity_pct",
    "debt_to_equity",
    "free_cash_flow_cr",
    "revenue_cagr_5yr",
    "pat_cagr_5yr",
    "operating_profit_margin_pct",
    "pe_ratio",
    "pb_ratio",
    "dividend_yield_pct",
    "interest_coverage",
]

visible_columns = [
    column
    for column in visible_columns
    if column in filtered.columns
]


display_df = filtered[visible_columns].copy()

display_df = display_df.rename(
    columns={
        "company_id": "Company ID",
        "company_name": "Company",
        "broad_sector": "Sector",
        "composite_quality_score": "Composite Score",
        "return_on_equity_pct": "ROE %",
        "debt_to_equity": "D/E",
        "free_cash_flow_cr": "FCF (Cr)",
        "revenue_cagr_5yr": "Revenue CAGR 5yr %",
        "pat_cagr_5yr": "PAT CAGR 5yr %",
        "operating_profit_margin_pct": "OPM %",
        "pe_ratio": "P/E",
        "pb_ratio": "P/B",
        "dividend_yield_pct": "Dividend Yield %",
        "interest_coverage": "ICR",
    }
)

st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True,
)


csv_data = display_df.to_csv(
    index=False
).encode("utf-8")


st.download_button(
    label="Download Results as CSV",
    data=csv_data,
    file_name="nifty100_screening_results.csv",
    mime="text/csv",
)
