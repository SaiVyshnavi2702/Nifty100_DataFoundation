"""
Day 33 - Company PDF Tearsheet

Creates a two-page company tearsheet using ReportLab.

Page 1:
- Navy company header
- Six KPI cards in 2 rows x 3 columns
- 10-year Revenue bar chart
- 10-year Net Profit bar chart
- ROE and ROCE dual-axis line chart

Page 2:
- Balance Sheet composition stacked bar chart
- Latest-year Cash Flow chart
- Pros with green bullets
- Cons with red bullets
- Capital Allocation badge

The layout is designed to fit on exactly two A4 pages.
"""

import sqlite3
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph

# Paths

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DB_PATH = PROJECT_ROOT / "data" / "nifty100.db"
OUTPUT_DIR = PROJECT_ROOT / "reports" / "tearsheets"
CAPITAL_ALLOCATION_FILE = PROJECT_ROOT / "output" / "capital_allocation.csv"


# Page settings

PAGE_WIDTH, PAGE_HEIGHT = A4


# Colours

NAVY = HexColor("#0B1F3A")
BLUE = HexColor("#1F5A94")
LIGHT_BLUE = HexColor("#EAF2F8")

GREEN = HexColor("#198754")
LIGHT_GREEN = HexColor("#EAF6EE")

RED = HexColor("#C0392B")
LIGHT_RED = HexColor("#FBEDEC")

ORANGE = HexColor("#F0A202")
GRAY_BLUE = HexColor("#8E9AAF")

DARK_GRAY = HexColor("#333333")
MEDIUM_GRAY = HexColor("#666666")
LIGHT_GRAY = HexColor("#E9ECEF")

WHITE = colors.white


# Database helpers


def query_database(sql, params=()):
    """Run a SQL query against the company database."""

    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found: {DB_PATH}")

    with sqlite3.connect(DB_PATH) as connection:
        return pd.read_sql_query(
            sql,
            connection,
            params=params,
        )


def load_company_data(ticker):
    """Load all financial data required for the tearsheet."""

    ticker = ticker.strip().upper()

    company = query_database(
        """
        SELECT
            id,
            company_name,
            company_logo,
            website,
            face_value,
            book_value,
            roce_percentage,
            roe_percentage
        FROM companies
        WHERE id = ?
        """,
        (ticker,),
    )

    if company.empty:
        raise ValueError(f"Company not found: {ticker}")

    profit_and_loss = query_database(
        """
        SELECT
            year,
            period,
            sales,
            net_profit
        FROM profitandloss
        WHERE company_id = ?
          AND year IS NOT NULL
          AND year != 'TTM'
        ORDER BY CAST(year AS INTEGER)
        """,
        (ticker,),
    )

    ratios = query_database(
        """
        SELECT
            year,
            period,
            return_on_equity_pct,
            debt_to_equity
        FROM financial_ratios
        WHERE company_id = ?
          AND year IS NOT NULL
        ORDER BY CAST(year AS INTEGER)
        """,
        (ticker,),
    )

    balance_sheet = query_database(
        """
        SELECT
            year,
            period,
            equity_capital,
            reserves,
            borrowings,
            other_liabilities,
            total_liabilities
        FROM balancesheet
        WHERE company_id = ?
          AND year IS NOT NULL
        ORDER BY CAST(year AS INTEGER)
        """,
        (ticker,),
    )

    cash_flow = query_database(
        """
        SELECT
            year,
            period,
            operating_activity,
            investing_activity,
            financing_activity,
            net_cash_flow
        FROM cashflow
        WHERE company_id = ?
          AND year IS NOT NULL
        ORDER BY CAST(year AS INTEGER)
        """,
        (ticker,),
    )

    market_data = query_database(
        """
        SELECT
            year,
            period,
            pe_ratio,
            pb_ratio,
            ev_ebitda,
            dividend_yield_pct
        FROM market_cap
        WHERE company_id = ?
          AND year IS NOT NULL
        ORDER BY CAST(year AS INTEGER)
        """,
        (ticker,),
    )

    pros_and_cons = query_database(
        """
        SELECT
            pros,
            cons
        FROM prosandcons
        WHERE company_id = ?
        """,
        (ticker,),
    )

    capital_allocation = pd.DataFrame()

    if CAPITAL_ALLOCATION_FILE.exists():

        capital_allocation = pd.read_csv(CAPITAL_ALLOCATION_FILE)

        if "company_id" in capital_allocation.columns:

            capital_allocation = capital_allocation[
                capital_allocation["company_id"].astype(str).str.upper() == ticker
            ].copy()

    return {
        "ticker": ticker,
        "company": company.iloc[0].to_dict(),
        "pl": profit_and_loss,
        "ratios": ratios,
        "balance_sheet": balance_sheet,
        "cash_flow": cash_flow,
        "market": market_data,
        "pros_cons": pros_and_cons,
        "capital_allocation": capital_allocation,
    }


# Data helpers


def clean_dataframe(df):
    """Clean the year column and remove invalid rows."""

    if df.empty:
        return df.copy()

    result = df.copy()

    result["year"] = pd.to_numeric(
        result["year"],
        errors="coerce",
    )

    result = result.dropna(subset=["year"])

    result["year"] = result["year"].astype(int)

    return result


def latest_value(df, column):
    """Return the latest available value."""

    if df.empty or column not in df.columns:
        return None

    valid_rows = df.dropna(subset=[column])

    if valid_rows.empty:
        return None

    return valid_rows.iloc[-1][column]


def format_number(value):
    """Format a number with commas."""

    if value is None or pd.isna(value):
        return "N/A"

    return f"{value:,.0f}"


def format_percent(value):
    """Format a percentage."""

    if value is None or pd.isna(value):
        return "N/A"

    return f"{value:.1f}%"


def format_ratio(value):
    """Format a financial ratio."""

    if value is None or pd.isna(value):
        return "N/A"

    return f"{value:.2f}"


def format_crore(value):
    """Format a financial value as Indian rupees in crore."""

    if value is None or pd.isna(value):
        return "N/A"

    return f"₹{value:,.0f} Cr"


# ReportLab drawing helpers


def draw_text(
    pdf,
    text,
    x,
    y,
    size=10,
    color=DARK_GRAY,
    bold=False,
):
    """Draw normal text."""

    font = "Helvetica-Bold" if bold else "Helvetica"

    pdf.setFont(font, size)
    pdf.setFillColor(color)

    pdf.drawString(
        x,
        y,
        str(text),
    )


def draw_header(pdf, company_name, ticker):
    """Draw the navy header."""

    header_height = 38 * mm

    pdf.setFillColor(NAVY)

    pdf.rect(
        0,
        PAGE_HEIGHT - header_height,
        PAGE_WIDTH,
        header_height,
        stroke=0,
        fill=1,
    )

    draw_text(
        pdf,
        company_name,
        18 * mm,
        PAGE_HEIGHT - 17 * mm,
        size=19,
        color=WHITE,
        bold=True,
    )

    draw_text(
        pdf,
        ticker,
        18 * mm,
        PAGE_HEIGHT - 28 * mm,
        size=13,
        color=HexColor("#BFD7EA"),
        bold=True,
    )

    draw_text(
        pdf,
        "Company Tearsheet",
        PAGE_WIDTH - 60 * mm,
        PAGE_HEIGHT - 17 * mm,
        size=9,
        color=WHITE,
    )


def draw_kpi_card(
    pdf,
    x,
    y,
    width,
    height,
    label,
    value,
):
    """Draw one KPI card."""

    pdf.setFillColor(LIGHT_BLUE)
    pdf.setStrokeColor(HexColor("#D3E2EE"))
    pdf.setLineWidth(0.7)

    pdf.roundRect(
        x,
        y,
        width,
        height,
        4,
        stroke=1,
        fill=1,
    )

    draw_text(
        pdf,
        label,
        x + 5 * mm,
        y + height - 8 * mm,
        size=8,
        color=MEDIUM_GRAY,
        bold=True,
    )

    draw_text(
        pdf,
        value,
        x + 5 * mm,
        y + 8 * mm,
        size=12,
        color=NAVY,
        bold=True,
    )


def draw_kpis(pdf, data):
    """Draw six KPI cards in two rows of three."""

    pl = clean_dataframe(data["pl"])

    ratios = clean_dataframe(data["ratios"])

    market = clean_dataframe(data["market"])

    revenue = latest_value(
        pl,
        "sales",
    )

    net_profit = latest_value(
        pl,
        "net_profit",
    )

    roe = latest_value(
        ratios,
        "return_on_equity_pct",
    )

    debt_to_equity = latest_value(
        ratios,
        "debt_to_equity",
    )

    pe = latest_value(
        market,
        "pe_ratio",
    )

    company = data["company"]

    roce = company.get("roce_percentage")

    if roce is None or pd.isna(roce):
        roce = latest_value(
            ratios,
            "return_on_equity_pct",
        )

    kpis = [
        (
            "Revenue",
            format_crore(revenue),
        ),
        (
            "Net Profit",
            format_crore(net_profit),
        ),
        (
            "ROE",
            format_percent(roe),
        ),
        (
            "ROCE",
            format_percent(roce),
        ),
        (
            "Debt / Equity",
            format_ratio(debt_to_equity),
        ),
        (
            "P / E",
            format_ratio(pe),
        ),
    ]

    left = 18 * mm
    right = 18 * mm
    gap = 5 * mm

    card_width = (PAGE_WIDTH - left - right - (2 * gap)) / 3

    card_height = 24 * mm

    first_row_y = PAGE_HEIGHT - 78 * mm

    second_row_y = PAGE_HEIGHT - 107 * mm

    for index, (label, value) in enumerate(kpis):

        row = index // 3
        column = index % 3

        x = left + column * (card_width + gap)

        if row == 0:
            y = first_row_y
        else:
            y = second_row_y

        draw_kpi_card(
            pdf,
            x,
            y,
            card_width,
            card_height,
            label,
            value,
        )


# Matplotlib helpers


def save_chart(fig, filename):
    """Save a Matplotlib chart."""

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    chart_path = OUTPUT_DIR / filename

    fig.savefig(
        chart_path,
        dpi=160,
        bbox_inches="tight",
        facecolor="white",
    )

    plt.close(fig)

    return chart_path


def clean_chart_axes(ax):
    """Apply a clean chart style with no grid lines."""

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    ax.grid(False)

    ax.set_axisbelow(False)


# Page 1 charts


def create_revenue_chart(df, ticker):
    """Create the 10-year revenue bar chart."""

    df = clean_dataframe(df)

    if df.empty:
        return None

    df = df.tail(10)

    fig, ax = plt.subplots(figsize=(4.8, 2.2))

    ax.bar(
        df["year"].astype(str),
        df["sales"],
        color="#1F5A94",
        width=0.65,
    )

    ax.set_title(
        "Revenue - 10 Year Trend",
        fontsize=10,
        fontweight="bold",
        loc="left",
    )

    ax.set_ylabel(
        "₹ Cr",
        fontsize=8,
    )

    ax.tick_params(
        axis="x",
        labelsize=7,
    )

    ax.tick_params(
        axis="y",
        labelsize=7,
    )

    clean_chart_axes(ax)

    fig.tight_layout()

    return save_chart(
        fig,
        f"{ticker}_revenue.png",
    )


def create_profit_chart(df, ticker):
    """Create the 10-year net profit bar chart."""

    df = clean_dataframe(df)

    if df.empty:
        return None

    df = df.tail(10)

    fig, ax = plt.subplots(figsize=(4.8, 2.2))

    ax.bar(
        df["year"].astype(str),
        df["net_profit"],
        color="#198754",
        width=0.65,
    )

    ax.set_title(
        "Net Profit - 10 Year Trend",
        fontsize=10,
        fontweight="bold",
        loc="left",
    )

    ax.set_ylabel(
        "₹ Cr",
        fontsize=8,
    )

    ax.tick_params(
        axis="x",
        labelsize=7,
    )

    ax.tick_params(
        axis="y",
        labelsize=7,
    )

    clean_chart_axes(ax)

    fig.tight_layout()

    return save_chart(
        fig,
        f"{ticker}_profit.png",
    )


def create_roe_roce_chart(data, ticker):
    """
    Create a dual-axis ROE and ROCE line chart.

    Both lines are solid.
    No dotted or dashed lines.
    No chart grid lines.
    """

    ratios = clean_dataframe(data["ratios"])

    if ratios.empty:
        return None

    ratios = ratios.tail(10)

    years = ratios["year"].astype(str)

    roe = pd.to_numeric(
        ratios["return_on_equity_pct"],
        errors="coerce",
    )

    if "return_on_capital_employed_pct" in ratios.columns:

        roce = pd.to_numeric(
            ratios["return_on_capital_employed_pct"],
            errors="coerce",
        )

    else:

        company_roce = data["company"].get("roce_percentage")

        if company_roce is None or pd.isna(company_roce):

            roce = roe.copy()

        else:

            roce = pd.Series(
                [company_roce] * len(ratios),
                index=ratios.index,
            )

    fig, ax1 = plt.subplots(figsize=(9.7, 2.25))

    ax2 = ax1.twinx()

    ax1.plot(
        years,
        roe,
        marker="o",
        color="#1F5A94",
        linewidth=2,
        linestyle="-",
        label="ROE",
    )

    ax2.plot(
        years,
        roce,
        marker="o",
        color="#C0392B",
        linewidth=2,
        linestyle="-",
        label="ROCE",
    )

    ax1.set_ylabel(
        "ROE (%)",
        color="#1F5A94",
        fontsize=8,
    )

    ax2.set_ylabel(
        "ROCE (%)",
        color="#C0392B",
        fontsize=8,
    )

    ax1.tick_params(
        axis="both",
        labelsize=7,
        colors="#1F5A94",
    )

    ax2.tick_params(
        axis="y",
        labelsize=7,
        colors="#C0392B",
    )

    ax1.set_title(
        "ROE & ROCE Trend",
        fontsize=10,
        fontweight="bold",
        loc="left",
    )

    ax1.grid(False)
    ax2.grid(False)

    ax1.spines["top"].set_visible(False)
    ax2.spines["top"].set_visible(False)

    ax1.legend(
        loc="upper left",
        fontsize=7,
        frameon=False,
    )

    ax2.legend(
        loc="upper right",
        fontsize=7,
        frameon=False,
    )

    fig.tight_layout()

    return save_chart(
        fig,
        f"{ticker}_roe_roce.png",
    )


# Page 1


def draw_page_one(pdf, data):
    """Draw page one."""

    company_name = data["company"]["company_name"]

    ticker = data["ticker"]

    draw_header(
        pdf,
        company_name,
        ticker,
    )

    draw_kpis(
        pdf,
        data,
    )

    revenue_chart = create_revenue_chart(
        data["pl"],
        ticker,
    )

    profit_chart = create_profit_chart(
        data["pl"],
        ticker,
    )

    chart_y = 79 * mm
    chart_height = 43 * mm
    chart_width = 82 * mm

    if revenue_chart and revenue_chart.exists():

        pdf.drawImage(
            str(revenue_chart),
            18 * mm,
            chart_y,
            width=chart_width,
            height=chart_height,
            preserveAspectRatio=False,
            anchor="sw",
            mask="auto",
        )

    if profit_chart and profit_chart.exists():

        pdf.drawImage(
            str(profit_chart),
            110 * mm,
            chart_y,
            width=chart_width,
            height=chart_height,
            preserveAspectRatio=False,
            anchor="sw",
            mask="auto",
        )

    roe_roce_chart = create_roe_roce_chart(
        data,
        ticker,
    )

    if roe_roce_chart and roe_roce_chart.exists():

        pdf.drawImage(
            str(roe_roce_chart),
            18 * mm,
            25 * mm,
            width=174 * mm,
            height=45 * mm,
            preserveAspectRatio=False,
            anchor="sw",
            mask="auto",
        )

    draw_text(
        pdf,
        "Day 33 Financial Overview",
        18 * mm,
        12 * mm,
        size=7,
        color=MEDIUM_GRAY,
    )


# Page 2 charts


def create_balance_sheet_chart(df, ticker):
    """Create the balance sheet composition stacked bar."""

    df = clean_dataframe(df)

    if df.empty:
        return None

    df = df.tail(5)

    equity_capital = pd.to_numeric(
        df["equity_capital"],
        errors="coerce",
    ).fillna(0)

    reserves = pd.to_numeric(
        df["reserves"],
        errors="coerce",
    ).fillna(0)

    equity = equity_capital + reserves

    borrowings = pd.to_numeric(
        df["borrowings"],
        errors="coerce",
    ).fillna(0)

    other_liabilities = pd.to_numeric(
        df["other_liabilities"],
        errors="coerce",
    ).fillna(0)

    years = df["year"].astype(str)

    fig, ax = plt.subplots(figsize=(9.8, 2.8))

    ax.bar(
        years,
        equity,
        label="Equity",
        color="#1F5A94",
    )

    ax.bar(
        years,
        borrowings,
        bottom=equity,
        label="Borrowings",
        color="#F0A202",
    )

    ax.bar(
        years,
        other_liabilities,
        bottom=equity + borrowings,
        label="Other Liabilities",
        color="#8E9AAF",
    )

    ax.set_title(
        "Balance Sheet Composition",
        fontsize=10,
        fontweight="bold",
        loc="left",
    )

    ax.set_ylabel(
        "₹ Cr",
        fontsize=8,
    )

    ax.tick_params(
        axis="x",
        labelsize=8,
    )

    ax.tick_params(
        axis="y",
        labelsize=7,
    )

    ax.legend(
        fontsize=7,
        frameon=False,
        ncol=3,
        loc="upper left",
    )

    clean_chart_axes(ax)

    fig.tight_layout()

    return save_chart(
        fig,
        f"{ticker}_balance_sheet.png",
    )


def create_cash_flow_chart(df, ticker):
    """Create the latest-year cash flow chart."""

    df = clean_dataframe(df)

    if df.empty:
        return None

    row = df.iloc[-1]

    cfo = pd.to_numeric(
        row["operating_activity"],
        errors="coerce",
    )

    cfi = pd.to_numeric(
        row["investing_activity"],
        errors="coerce",
    )

    cff = pd.to_numeric(
        row["financing_activity"],
        errors="coerce",
    )

    net_cash = pd.to_numeric(
        row["net_cash_flow"],
        errors="coerce",
    )

    labels = [
        "CFO",
        "CFI",
        "CFF",
        "Net Cash Flow",
    ]

    values = [
        cfo,
        cfi,
        cff,
        net_cash,
    ]

    colors_for_bars = [
        "#198754",
        "#C0392B",
        "#C0392B",
        "#1F5A94",
    ]

    fig, ax = plt.subplots(figsize=(9.8, 2.7))

    ax.bar(
        labels,
        values,
        color=colors_for_bars,
        width=0.55,
    )

    ax.axhline(
        0,
        color="#333333",
        linewidth=0.8,
        linestyle="-",
    )

    ax.set_title(
        f"Cash Flow - Latest Year ({int(row['year'])})",
        fontsize=10,
        fontweight="bold",
        loc="left",
    )

    ax.set_ylabel(
        "₹ Cr",
        fontsize=8,
    )

    ax.tick_params(
        axis="x",
        labelsize=8,
    )

    ax.tick_params(
        axis="y",
        labelsize=7,
    )

    clean_chart_axes(ax)

    valid_values = [value for value in values if not pd.isna(value)]

    if valid_values:

        maximum_value = max(abs(value) for value in valid_values)

        offset = 0.03 * max(
            maximum_value,
            1,
        )

        for index, value in enumerate(values):

            if pd.isna(value):
                continue

            if value >= 0:

                label_y = value + offset

                vertical_alignment = "bottom"

            else:

                label_y = value - offset

                vertical_alignment = "top"

            ax.text(
                index,
                label_y,
                f"{value:,.0f}",
                ha="center",
                va=vertical_alignment,
                fontsize=7,
            )

    fig.tight_layout()

    return save_chart(
        fig,
        f"{ticker}_cash_flow.png",
    )


# Pros / Cons


def get_pros_and_cons(data):
    """Return company pros and cons."""

    pros = []
    cons = []

    df = data["pros_cons"]

    if df.empty:
        return pros, cons

    for _, row in df.iterrows():

        pro = row.get("pros")
        con = row.get("cons")

        if pro is not None and not pd.isna(pro):

            text = str(pro).strip()

            if text and text.lower() != "nan":
                pros.append(text)

        if con is not None and not pd.isna(con):

            text = str(con).strip()

            if text and text.lower() != "nan":
                cons.append(text)

    return pros, cons


def draw_wrapped_bullet(
    pdf,
    text,
    x,
    y,
    width,
    bullet_color,
):
    """Draw a word-wrapped bullet point."""

    style = ParagraphStyle(
        "bullet_style",
        fontName="Helvetica",
        fontSize=8.5,
        leading=11,
        textColor=DARK_GRAY,
        alignment=TA_LEFT,
    )

    pdf.setFillColor(bullet_color)

    pdf.setFont(
        "Helvetica-Bold",
        11,
    )

    pdf.drawString(
        x,
        y,
        "•",
    )

    paragraph = Paragraph(
        str(text),
        style,
    )

    paragraph_width = width - 7 * mm

    paragraph_height = paragraph.wrap(
        paragraph_width,
        30 * mm,
    )[1]

    paragraph.drawOn(
        pdf,
        x + 6 * mm,
        y - paragraph_height + 3,
    )

    return y - paragraph_height - 3 * mm


def draw_pros_and_cons(pdf, data):
    """Draw the Pros and Cons sections."""

    pros, cons = get_pros_and_cons(data)

    left = 18 * mm
    width = 174 * mm

    pros_y = 92 * mm

    draw_text(
        pdf,
        "PROS",
        left,
        pros_y,
        size=11,
        color=GREEN,
        bold=True,
    )

    y = pros_y - 7 * mm

    if not pros:

        draw_text(
            pdf,
            "No pros available.",
            left,
            y,
            size=8,
            color=MEDIUM_GRAY,
        )

    else:

        for pro in pros[:3]:

            y = draw_wrapped_bullet(
                pdf,
                pro,
                left,
                y,
                width,
                GREEN,
            )

    cons_y = 59 * mm

    draw_text(
        pdf,
        "CONS",
        left,
        cons_y,
        size=11,
        color=RED,
        bold=True,
    )

    y = cons_y - 7 * mm

    if not cons:

        draw_text(
            pdf,
            "No cons available.",
            left,
            y,
            size=8,
            color=MEDIUM_GRAY,
        )

    else:

        for con in cons[:3]:

            y = draw_wrapped_bullet(
                pdf,
                con,
                left,
                y,
                width,
                RED,
            )


# Capital allocation


def get_capital_allocation(data):
    """Get the latest capital allocation pattern."""

    df = data["capital_allocation"]

    if df.empty:
        return "Not available"

    df = df.copy()

    if "year" not in df.columns:
        return "Not available"

    df["year"] = pd.to_numeric(
        df["year"],
        errors="coerce",
    )

    df = df.dropna(subset=["year"])

    if df.empty:
        return "Not available"

    df = df.sort_values("year")

    latest_row = df.iloc[-1]

    label = latest_row.get("pattern_label")

    if label is None or pd.isna(label):
        return "Not available"

    return str(label)


def draw_capital_allocation(pdf, data):
    """Draw the capital allocation badge."""

    label = get_capital_allocation(data)

    x = 18 * mm
    y = 18 * mm
    width = 174 * mm
    height = 25 * mm

    pdf.setFillColor(LIGHT_BLUE)

    pdf.setStrokeColor(HexColor("#BFD7EA"))

    pdf.roundRect(
        x,
        y,
        width,
        height,
        5,
        stroke=1,
        fill=1,
    )

    draw_text(
        pdf,
        "CAPITAL ALLOCATION",
        x + 7 * mm,
        y + 15 * mm,
        size=8,
        color=MEDIUM_GRAY,
        bold=True,
    )

    badge_font_size = 10

    max_badge_width = width - 65 * mm

    text_width = stringWidth(
        label,
        "Helvetica-Bold",
        badge_font_size,
    )

    if text_width + 14 * mm > max_badge_width:

        badge_font_size = 8

        text_width = stringWidth(
            label,
            "Helvetica-Bold",
            badge_font_size,
        )

    badge_width = min(
        text_width + 14 * mm,
        max_badge_width,
    )

    badge_x = x + width - badge_width - 7 * mm

    pdf.setFillColor(NAVY)

    pdf.roundRect(
        badge_x,
        y + 6 * mm,
        badge_width,
        11 * mm,
        5,
        stroke=0,
        fill=1,
    )

    draw_text(
        pdf,
        label,
        badge_x + 7 * mm,
        y + 10 * mm,
        size=badge_font_size,
        color=WHITE,
        bold=True,
    )


# Page 2


def draw_page_two(pdf, data):
    """Draw page two."""

    company_name = data["company"]["company_name"]

    ticker = data["ticker"]

    draw_header(
        pdf,
        company_name,
        ticker,
    )

    draw_text(
        pdf,
        "Financial Position & Investment View",
        18 * mm,
        PAGE_HEIGHT - 48 * mm,
        size=13,
        color=NAVY,
        bold=True,
    )

    balance_chart = create_balance_sheet_chart(
        data["balance_sheet"],
        ticker,
    )

    if balance_chart and balance_chart.exists():

        pdf.drawImage(
            str(balance_chart),
            18 * mm,
            123 * mm,
            width=174 * mm,
            height=52 * mm,
            preserveAspectRatio=False,
            anchor="sw",
            mask="auto",
        )

    cash_chart = create_cash_flow_chart(
        data["cash_flow"],
        ticker,
    )

    if cash_chart and cash_chart.exists():

        pdf.drawImage(
            str(cash_chart),
            18 * mm,
            99 * mm,
            width=174 * mm,
            height=42 * mm,
            preserveAspectRatio=False,
            anchor="sw",
            mask="auto",
        )

    draw_pros_and_cons(
        pdf,
        data,
    )

    draw_capital_allocation(
        pdf,
        data,
    )


# PDF generation


def generate_tearsheet(ticker):
    """Generate a two-page company tearsheet."""

    data = load_company_data(ticker)

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_file = OUTPUT_DIR / f"{data['ticker']}_tearsheet.pdf"

    pdf = canvas.Canvas(
        str(output_file),
        pagesize=A4,
    )

    pdf.setTitle(f"{data['ticker']} Company Tearsheet")

    draw_page_one(
        pdf,
        data,
    )

    pdf.showPage()

    draw_page_two(
        pdf,
        data,
    )

    pdf.showPage()

    pdf.save()

    return output_file


# Main


def main():
    """Generate the TCS tearsheet."""

    ticker = "TCS"

    output_file = generate_tearsheet(ticker)

    print(f"Created: {output_file}")


if __name__ == "__main__":
    main()
