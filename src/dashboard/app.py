import streamlit as st


st.set_page_config(
    page_title="Nifty 100 Analytics",
    layout="wide",
    initial_sidebar_state="expanded",
)


st.title("Nifty 100 Analytics")

st.sidebar.title("Navigation")

st.sidebar.write("Use the pages below to explore the Nifty 100 data.")

st.write("Welcome to the Nifty 100 Analytics dashboard.")
st.write(
    "Use the sidebar to view company profiles, screen companies, "
    "compare peers, analyse trends, sectors and capital allocation."
)
