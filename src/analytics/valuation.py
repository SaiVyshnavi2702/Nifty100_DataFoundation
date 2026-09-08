"""
Day 26 - Valuation Module

This module calculates:
- FCF Yield
- Sector median P/E
- Valuation flags

It creates:
- output/valuation_summary.xlsx
- output/valuation_flags.csv
"""

from pathlib import Path
import sqlite3

import numpy as np
import pandas as pd


# Project paths

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DB_PATH = PROJECT_ROOT / "data" / "nifty100.db"

MARKET_CAP_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "supporting"
    / "market_cap.xlsx"
)

OUTPUT_DIR = PROJECT_ROOT / "output"

SUMMARY_OUTPUT = OUTPUT_DIR / "valuation_summary.xlsx"

FLAGS_OUTPUT = OUTPUT_DIR / "valuation_flags.csv"


# Columns required in the final valuation file

OUTPUT_COLUMNS = [
    "company_id",
    "company_name",
    "sector",
    "P/E",
    "P/B",
    "EV/EBITDA",
    "FCF_yield_pct",
    "5yr_median_PE",
    "PE_vs_sector_median_pct",
    "flag",
]


def load_market_cap():
    """
    Load market cap and valuation data from market_cap.xlsx.

    The Excel file contains yearly data, so we keep the
    latest year available for each company.
    """

    if not MARKET_CAP_PATH.exists():
        raise FileNotFoundError(
            f"Market cap file not found: {MARKET_CAP_PATH}"
        )

    df = pd.read_excel(MARKET_CAP_PATH)

    required_columns = [
        "company_id",
        "year",
        "market_cap_crore",
        "pe_ratio",
        "pb_ratio",
        "ev_ebitda",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing columns in market_cap.xlsx: {missing_columns}"
        )

    df["year"] = pd.to_numeric(
        df["year"],
        errors="coerce"
    )

    df["market_cap_crore"] = pd.to_numeric(
        df["market_cap_crore"],
        errors="coerce"
    )

    df["pe_ratio"] = pd.to_numeric(
        df["pe_ratio"],
        errors="coerce"
    )

    df["pb_ratio"] = pd.to_numeric(
        df["pb_ratio"],
        errors="coerce"
    )

    df["ev_ebitda"] = pd.to_numeric(
        df["ev_ebitda"],
        errors="coerce"
    )

    df = df.sort_values(
        ["company_id", "year"]
    )

    df = df.drop_duplicates(
        subset=["company_id"],
        keep="last"
    )

    df = df.rename(
        columns={
            "pe_ratio": "P/E",
            "pb_ratio": "P/B",
            "ev_ebitda": "EV/EBITDA",
        }
    )

    return df[
        [
            "company_id",
            "year",
            "market_cap_crore",
            "P/E",
            "P/B",
            "EV/EBITDA",
        ]
    ]


def load_fcf():
    """
    Load free cash flow data from the financial_ratios table.

    We use the latest available year for each company.
    """

    connection = sqlite3.connect(DB_PATH)

    try:
        query = """
            SELECT
                company_id,
                year,
                free_cash_flow_cr
            FROM financial_ratios
        """

        df = pd.read_sql_query(
            query,
            connection
        )

    finally:
        connection.close()

    df["year"] = pd.to_numeric(
        df["year"],
        errors="coerce"
    )

    df["free_cash_flow_cr"] = pd.to_numeric(
        df["free_cash_flow_cr"],
        errors="coerce"
    )

    df = df.sort_values(
        ["company_id", "year"]
    )

    df = df.drop_duplicates(
        subset=["company_id"],
        keep="last"
    )

    return df[
        [
            "company_id",
            "year",
            "free_cash_flow_cr",
        ]
    ]

def load_sectors():
    """
    Load broad sector information from the sectors table.
    """

    connection = sqlite3.connect(DB_PATH)

    try:
        query = """
            SELECT
                company_id,
                broad_sector
            FROM sectors
        """

        df = pd.read_sql_query(
            query,
            connection
        )

    finally:
        connection.close()

    df["company_id"] = (
        df["company_id"]
        .astype(str)
        .str.strip()
    )

    df["broad_sector"] = (
        df["broad_sector"]
        .astype(str)
        .str.strip()
    )

    df = df.drop_duplicates(
        subset=["company_id"],
        keep="last"
    )

    return df[
        [
            "company_id",
            "broad_sector",
        ]
    ]

def load_companies():
    """
    Load company names from the companies table.
    """

    connection = sqlite3.connect(DB_PATH)

    try:
        query = """
            SELECT
                id AS company_id,
                company_name
            FROM companies
        """

        df = pd.read_sql_query(
            query,
            connection
        )

    finally:
        connection.close()

    df["company_id"] = (
        df["company_id"]
        .astype(str)
        .str.strip()
    )

    df["company_name"] = (
        df["company_name"]
        .astype(str)
        .str.strip()
    )

    df = df.drop_duplicates(
        subset=["company_id"],
        keep="last"
    )

    return df[
        [
            "company_id",
            "company_name",
        ]
    ]
def build_valuation_dataset():
    """
    Load and merge all data needed for the valuation analysis.

    The market_cap.xlsx dataset is the base dataset because
    it contains the 92 companies required for this task.
    """

    market_cap = load_market_cap()

    fcf = load_fcf()

    sectors = load_sectors()

    companies = load_companies()

    df = market_cap.merge(
        fcf[["company_id", "free_cash_flow_cr"]],
        on="company_id",
        how="left"
    )

    df = df.merge(
        sectors,
        on="company_id",
        how="left"
    )

    df = df.merge(
        companies,
        on="company_id",
        how="left"
    )

    df = df.rename(
        columns={
            "broad_sector": "sector",
            "free_cash_flow_cr": "FCF",
        }
    )

    return df

def calculate_fcf_yield(df):
    """
    Calculate FCF Yield as:

    FCF / Market Cap * 100
    """

    df = df.copy()

    df["FCF_yield_pct"] = (
        df["FCF"]
        / df["market_cap_crore"]
        * 100
    )

    return df
def calculate_sector_median_pe(df):
    """
    Calculate the median P/E for each broad sector
    using the latest-year valuation data.
    """

    df = df.copy()

    sector_medians = (
        df.groupby("sector")["P/E"]
        .median()
        .reset_index()
    )

    sector_medians = sector_medians.rename(
        columns={
            "P/E": "5yr_median_PE"
        }
    )

    df = df.merge(
        sector_medians,
        on="sector",
        how="left"
    )

    return df
def calculate_pe_vs_sector_median(df):
    """
    Calculate the percentage difference between
    company P/E and its sector median P/E.
    """

    df = df.copy()

    df["PE_vs_sector_median_pct"] = (
        (
            df["P/E"] - df["5yr_median_PE"]
        )
        / df["5yr_median_PE"]
        * 100
    )

    return df
def apply_valuation_flags(df):
    """
    Apply valuation flags based on P/E relative to
    the sector median P/E.

    Caution:
        P/E > sector median * 1.5

    Discount:
        P/E < sector median * 0.7

    Fair:
        Everything else
    """

    df = df.copy()

    df["flag"] = "Fair"

    df.loc[
        df["P/E"] > df["5yr_median_PE"] * 1.5,
        "flag"
    ] = "Caution"

    df.loc[
        df["P/E"] < df["5yr_median_PE"] * 0.7,
        "flag"
    ] = "Discount"

    return df

def write_valuation_outputs(df):
    output_dir = PROJECT_ROOT / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_columns = [
        "company_id",
        "company_name",
        "sector",
        "P/E",
        "P/B",
        "EV/EBITDA",
        "FCF_yield_pct",
        "5yr_median_PE",
        "PE_vs_sector_median_pct",
        "flag",
    ]

    summary = df[output_columns].copy()

    summary.to_excel(
        output_dir / "valuation_summary.xlsx",
        index=False
    )

    flags = summary[
        summary["flag"].isin(["Caution", "Discount"])
    ].copy()

    flags.to_csv(
        output_dir / "valuation_flags.csv",
        index=False
    )

    print("Created:", output_dir / "valuation_summary.xlsx")
    print("Created:", output_dir / "valuation_flags.csv")
    print("Summary rows:", len(summary))
    print("Flagged rows:", len(flags))
