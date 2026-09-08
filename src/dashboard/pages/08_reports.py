import pandas as pd
import requests
import streamlit as st

from dashboard.utils.db import get_companies, _query


st.title("📄 Annual Reports")

st.write(
    "Find and access annual reports for Nifty 100 companies."
)


companies = get_companies()


if companies.empty:
    st.warning("Company data is not available.")
    st.stop()


company_names = (
    companies["company_name"]
    .dropna()
    .sort_values()
    .tolist()
)


selected_company = st.selectbox(
    "Search Company",
    company_names,
)


company = companies[
    companies["company_name"] == selected_company
]


if company.empty:
    st.warning(
        "Company not found. Please try another company."
    )
    st.stop()


company_id = company.iloc[0]["id"]


reports = _query(
    """
    SELECT
        company_id,
        year,
        period,
        annual_report
    FROM documents
    WHERE company_id = ?
    ORDER BY year DESC
    """,
    (company_id,),
)


st.subheader(
    f"Annual Reports — {selected_company}"
)


if reports.empty:
    st.info(
        "No annual reports are available for this company."
    )
    st.stop()


reports["year"] = pd.to_numeric(
    reports["year"],
    errors="coerce",
)


reports = reports.dropna(
    subset=["year"]
)


reports["year"] = reports["year"].astype(int)


@st.cache_data(ttl=600)
def get_report_status(url):

    if pd.isna(url):
        return "missing"

    url = str(url).strip()

    if not url:
        return "missing"

    try:

        response = requests.get(
            url,
            timeout=15,
            allow_redirects=True,
            stream=True,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 "
                    "(Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 "
                    "(KHTML, like Gecko) "
                    "Chrome/120.0 Safari/537.36"
                )
            },
        )

        if response.status_code == 404:
            return "404"

        return "available"

    except requests.RequestException:
        return "unknown"


for _, report in reports.iterrows():

    year = report["year"]

    url = report["annual_report"]


    st.markdown(
        f"### Annual Report {year}"
    )


    if pd.isna(url) or not str(url).strip():

        st.markdown(
            """
            <span style="
                color: #dc3545;
                font-weight: 600;
            ">
                🔴 Report unavailable
            </span>
            """,
            unsafe_allow_html=True,
        )

        continue


    url = str(url).strip()


    with st.spinner(
        f"Checking {year} report..."
    ):

        status = get_report_status(url)


    if status == "404":

        st.markdown(
            """
            <span style="
                color: #dc3545;
                font-weight: 600;
            ">
                🔴 Report unavailable
            </span>
            """,
            unsafe_allow_html=True,
        )

    else:

        st.link_button(
            f"📄 Open {year} Annual Report",
            url,
        )
