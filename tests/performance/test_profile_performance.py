import time

import streamlit as st

from src.dashboard.utils.db import (
    get_companies,
    get_company_sector,
    get_pl,
    get_pros_and_cons,
    get_ratios,
)

TICKERS = [
    "TCS",
    "HDFCBANK",
    "RELIANCE",
    "SUNPHARMA",
    "TATASTEEL",
]


def load_company_profile(ticker):
    companies = get_companies()

    company = companies[companies["id"] == ticker].iloc[0]

    company_name = company["company_name"]

    get_company_sector(company_name)
    get_ratios(company_name)
    get_pl(company_name)
    get_pros_and_cons(company_name)


def test_company_profile_performance():
    results = []

    for ticker in TICKERS:
        st.cache_data.clear()

        start_time = time.perf_counter()

        load_company_profile(ticker)

        response_time = time.perf_counter() - start_time
        results.append((ticker, response_time))

        print(f"\n{ticker}: " f"{response_time:.3f} seconds")

    print("\nCompany Profile Performance:")

    for ticker, response_time in results:
        print(f"{ticker}: " f"{response_time:.3f} seconds")

    for ticker, response_time in results:
        assert response_time < 3, (
            f"{ticker} took "
            f"{response_time:.3f} seconds, "
            "which exceeds the 3-second target."
        )
