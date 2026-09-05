import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DB_PATH = PROJECT_ROOT / "data" / "nifty100.db"


def _query(sql, params=()):
    with sqlite3.connect(DB_PATH) as connection:
        return pd.read_sql_query(sql, connection, params=params)


@st.cache_data(ttl=600)
def get_companies():
    return _query(
        """
        SELECT
            id,
            company_logo,
            company_name,
            chart_link,
            about_company,
            website,
            nse_profile,
            bse_profile,
            face_value,
            book_value,
            roce_percentage,
            roe_percentage
        FROM companies
        ORDER BY company_name
        """
    )


@st.cache_data(ttl=600)
def get_ratios(ticker, year=None):
    if year is None:
        return _query(
            """
            SELECT
                fr.*,
                c.company_name
            FROM financial_ratios fr
            JOIN companies c
                ON c.id = fr.company_id
            WHERE c.company_name = ?
            ORDER BY fr.year DESC
            """,
            (ticker,),
        )

    return _query(
        """
        SELECT
            fr.*,
            c.company_name
        FROM financial_ratios fr
        JOIN companies c
            ON c.id = fr.company_id
        WHERE c.company_name = ?
          AND fr.year = ?
        ORDER BY fr.year DESC
        """,
        (ticker, year),
    )


@st.cache_data(ttl=600)
def get_pl(ticker):
    return _query(
        """
        SELECT
            pl.*,
            c.company_name
        FROM profitandloss pl
        JOIN companies c
            ON c.id = pl.company_id
        WHERE c.company_name = ?
        ORDER BY pl.year DESC
        """,
        (ticker,),
    )


@st.cache_data(ttl=600)
def get_bs(ticker):
    return _query(
        """
        SELECT
            bs.*,
            c.company_name
        FROM balancesheet bs
        JOIN companies c
            ON c.id = bs.company_id
        WHERE c.company_name = ?
        ORDER BY bs.year DESC
        """,
        (ticker,),
    )


@st.cache_data(ttl=600)
def get_cf(ticker):
    return _query(
        """
        SELECT
            cf.*,
            c.company_name
        FROM cashflow cf
        JOIN companies c
            ON c.id = cf.company_id
        WHERE c.company_name = ?
        ORDER BY cf.year DESC
        """,
        (ticker,),
    )


@st.cache_data(ttl=600)
def get_sectors():
    return _query(
        """
        SELECT
            s.*,
            c.company_name
        FROM sectors s
        JOIN companies c
            ON c.id = s.company_id
        ORDER BY s.broad_sector, c.company_name
        """
    )


@st.cache_data(ttl=600)
def get_peers(group_name):
    return _query(
        """
        SELECT
            pg.id,
            pg.peer_group_name,
            pg.company_id,
            pg.is_benchmark,
            c.company_name
        FROM peer_groups pg
        JOIN companies c
            ON c.id = pg.company_id
        WHERE pg.peer_group_name = ?
        ORDER BY pg.is_benchmark DESC, c.company_name
        """,
        (group_name,),
    )


@st.cache_data(ttl=600)
def get_valuation(ticker):
    return _query(
        """
        SELECT
            mc.*,
            c.company_name
        FROM market_cap mc
        JOIN companies c
            ON c.id = mc.company_id
        WHERE c.company_name = ?
        ORDER BY mc.year DESC
        """,
        (ticker,),
    )


