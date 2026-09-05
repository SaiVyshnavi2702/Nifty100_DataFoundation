import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from dashboard.utils.db import get_companies, get_sectors


st.title("Nifty 100 Analytics")

st.write(
    "Welcome to the Nifty 100 Analytics dashboard. "
    "Use the pages in the sidebar to explore companies, "
    "financial ratios, screeners and peer comparisons."
)


companies = get_companies()
sectors = get_sectors()


col1, col2 = st.columns(2)

with col1:
    st.metric("Companies", companies["id"].nunique())

with col2:
    st.metric("Sectors", sectors["broad_sector"].nunique())


st.subheader("Company Overview")

st.dataframe(
    companies[["id", "company_name", "roe_percentage", "roce_percentage"]],
    use_container_width=True,
    hide_index=True,
)
