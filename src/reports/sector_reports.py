
"""
Day 34 - Sector Report Generation

Generates one PDF report for each broad sector.

Each sector report contains:
1. Sector summary with median KPIs
2. List of all companies in the sector
3. Eight company-level metrics
"""

from pathlib import Path
import sqlite3

import pandas as pd

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DB_PATH = PROJECT_ROOT / "data" / "nifty100.db"

OUTPUT_DIR = PROJECT_ROOT / "reports" / "sector"


def calculate_cagr(start_value, end_value, years):
    """Calculate CAGR percentage safely."""

    if pd.isna(start_value) or pd.isna(end_value):
        return None

    if pd.isna(years) or years <= 0:
        return None

    if start_value <= 0 or end_value <= 0:
        return None

    return (
        (end_value / start_value) ** (1 / years) - 1
    ) * 100


def calculate_financial_cagr(pnl_df):
    """
    Calculate Sales Growth and Profit Growth CAGR
    using the earliest and latest available yearly data.

    TTM rows are excluded.
    """

    sales_growth = {}
    profit_growth = {}

    for ticker, group in pnl_df.groupby("company_id"):

        group = group.copy()

        group["year"] = pd.to_numeric(
            group["year"],
            errors="coerce",
        )

        group["sales"] = pd.to_numeric(
            group["sales"],
            errors="coerce",
        )

        group["net_profit"] = pd.to_numeric(
            group["net_profit"],
            errors="coerce",
        )

        group = group.dropna(
            subset=["year"]
        ).sort_values("year")

        # -------------------------
        # Sales CAGR
        # -------------------------

        sales_data = group.dropna(
            subset=["sales"]
        )

        if len(sales_data) >= 2:

            first = sales_data.iloc[0]
            last = sales_data.iloc[-1]

            sales_growth[ticker] = calculate_cagr(
                first["sales"],
                last["sales"],
                last["year"] - first["year"],
            )

        else:
            sales_growth[ticker] = None

        
        # Profit CAGR
        

        profit_data = group.dropna(
            subset=["net_profit"]
        )

        if len(profit_data) >= 2:

            first = profit_data.iloc[0]
            last = profit_data.iloc[-1]

            profit_growth[ticker] = calculate_cagr(
                first["net_profit"],
                last["net_profit"],
                last["year"] - first["year"],
            )

        else:
            profit_growth[ticker] = None

    return sales_growth, profit_growth


def calculate_stock_cagr(stock_df):
    """
    Calculate Stock CAGR using adjusted close prices.

    Uses the earliest and latest available price records
    for each company.
    """

    stock_cagr = {}

    stock_df["date"] = pd.to_datetime(
        stock_df["date"],
        errors="coerce",
    )

    stock_df["adjusted_close"] = pd.to_numeric(
        stock_df["adjusted_close"],
        errors="coerce",
    )

    for ticker, group in stock_df.groupby("company_id"):

        group = group.dropna(
            subset=[
                "date",
                "adjusted_close",
            ]
        ).sort_values("date")

        if len(group) < 2:
            stock_cagr[ticker] = None
            continue

        first = group.iloc[0]
        last = group.iloc[-1]

        days = (
            last["date"] - first["date"]
        ).days

        years = days / 365.25

        stock_cagr[ticker] = calculate_cagr(
            first["adjusted_close"],
            last["adjusted_close"],
            years,
        )

    return stock_cagr


def get_sector_data():
    """Load company, sector and financial metrics from the database."""

    with sqlite3.connect(DB_PATH) as connection:

        
        # Company + sector + latest financial ratio data
        

        query = """
            SELECT
                c.id AS ticker,
                c.company_name AS company_name,
                s.broad_sector AS sector,
                s.sub_sector AS sub_sector,

                fr.net_profit_margin_pct AS net_profit_margin,
                fr.operating_profit_margin_pct AS operating_margin,
                fr.debt_to_equity AS debt_to_equity,
                fr.interest_coverage AS interest_coverage,
                fr.return_on_equity_pct AS analysis_roe

            FROM companies c

            LEFT JOIN sectors s
                ON c.id = s.company_id

            LEFT JOIN financial_ratios fr
                ON c.id = fr.company_id
                AND fr.year = (
                    SELECT MAX(fr2.year)
                    FROM financial_ratios fr2
                    WHERE fr2.company_id = c.id
                      AND fr2.year IS NOT NULL
                      AND fr2.period != 'TTM'
                )

            WHERE s.broad_sector IS NOT NULL

            ORDER BY
                s.broad_sector,
                c.id
        """

        df = pd.read_sql_query(
            query,
            connection,
        )

        # Historical Profit & Loss data
        

        pnl_query = """
            SELECT
                company_id,
                year,
                sales,
                net_profit
            FROM profitandloss
            WHERE year IS NOT NULL
              AND year != 'TTM'
            ORDER BY company_id, year
        """

        pnl = pd.read_sql_query(
            pnl_query,
            connection,
        )

        # Historical stock price data
        

        stock_query = """
            SELECT
                company_id,
                date,
                adjusted_close
            FROM stock_prices
            WHERE date IS NOT NULL
              AND adjusted_close IS NOT NULL
            ORDER BY company_id, date
        """

        stock = pd.read_sql_query(
            stock_query,
            connection,
        )

    # Calculate financial growth metrics
    

    sales_growth, profit_growth = calculate_financial_cagr(
        pnl
    )

    df["sales_growth"] = df["ticker"].map(
        sales_growth
    )

    df["profit_growth"] = df["ticker"].map(
        profit_growth
    )

    # Calculate Stock CAGR

    stock_cagr = calculate_stock_cagr(
        stock
    )

    df["stock_cagr"] = df["ticker"].map(
        stock_cagr
    )

    return df


def format_number(value, suffix=""):
    """Format numeric and text-based numeric values for the PDF."""

    if pd.isna(value):
        return "N/A"

    try:
        return f"{float(value):,.2f}{suffix}"

    except (ValueError, TypeError):

        text = str(value).strip()

        if ":" in text:
            text = text.split(":")[-1].strip()

        text = text.replace("%", "").strip()

        try:
            return f"{float(text):,.2f}{suffix}"

        except (ValueError, TypeError):
            return "N/A"


def build_styles():
    """Create ReportLab styles."""

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "SectorTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#0B1F3A"),
        alignment=TA_LEFT,
        spaceAfter=8,
    )

    subtitle_style = ParagraphStyle(
        "SectorSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#555555"),
        spaceAfter=12,
    )

    heading_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        textColor=colors.HexColor("#0B1F3A"),
        spaceBefore=8,
        spaceAfter=8,
    )

    normal_style = ParagraphStyle(
        "NormalText",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#222222"),
    )

    small_style = ParagraphStyle(
        "SmallText",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7,
        leading=9,
        textColor=colors.HexColor("#333333"),
    )

    return {
        "title": title_style,
        "subtitle": subtitle_style,
        "heading": heading_style,
        "normal": normal_style,
        "small": small_style,
    }


def build_sector_summary(df, styles):
    """Build the sector median KPI summary."""

    metrics = [
        ("Sales Growth", "sales_growth", "%"),
        ("Profit Growth", "profit_growth", "%"),
        ("Stock CAGR", "stock_cagr", "%"),
        ("ROE", "analysis_roe", "%"),
        ("Net Profit Margin", "net_profit_margin", "%"),
        ("Operating Margin", "operating_margin", "%"),
        ("Debt / Equity", "debt_to_equity", ""),
        ("Interest Coverage", "interest_coverage", "x"),
    ]

    data = [
        [
            Paragraph(
                "<b>Metric</b>",
                styles["small"],
            ),
            Paragraph(
                "<b>Sector Median</b>",
                styles["small"],
            ),
        ]
    ]

    for label, column, suffix in metrics:

        numeric_values = pd.to_numeric(
            df[column],
            errors="coerce",
        )

        median_value = numeric_values.median()

        data.append(
            [
                Paragraph(
                    label,
                    styles["small"],
                ),
                Paragraph(
                    format_number(
                        median_value,
                        suffix,
                    ),
                    styles["small"],
                ),
            ]
        )

    table = Table(
        data,
        colWidths=[
            70 * mm,
            45 * mm,
        ],
        repeatRows=1,
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#E8EDF3"),
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#0B1F3A"),
                ),
                (
                    "BACKGROUND",
                    (0, 1),
                    (-1, -1),
                    colors.HexColor("#F7F9FC"),
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
            ]
        )
    )

    return table


def build_company_table(df, styles):
    """Build the company-level eight-metric table."""

    headers = [
        "Ticker",
        "Company",
        "Sales Growth",
        "Profit Growth",
        "Stock CAGR",
        "ROE",
        "NPM",
        "D/E",
        "Interest Cover",
    ]

    data = [
        [
            Paragraph(
                f"<b>{header}</b>",
                styles["small"],
            )
            for header in headers
        ]
    ]

    for _, row in df.iterrows():

        company_name = row["company_name"]

        if pd.isna(company_name):
            company_name = row["ticker"]

        data.append(
            [
                Paragraph(
                    str(row["ticker"]),
                    styles["small"],
                ),
                Paragraph(
                    str(company_name),
                    styles["small"],
                ),
                Paragraph(
                    format_number(
                        row["sales_growth"],
                        "%",
                    ),
                    styles["small"],
                ),
                Paragraph(
                    format_number(
                        row["profit_growth"],
                        "%",
                    ),
                    styles["small"],
                ),
                Paragraph(
                    format_number(
                        row["stock_cagr"],
                        "%",
                    ),
                    styles["small"],
                ),
                Paragraph(
                    format_number(
                        row["analysis_roe"],
                        "%",
                    ),
                    styles["small"],
                ),
                Paragraph(
                    format_number(
                        row["net_profit_margin"],
                        "%",
                    ),
                    styles["small"],
                ),
                Paragraph(
                    format_number(
                        row["debt_to_equity"],
                    ),
                    styles["small"],
                ),
                Paragraph(
                    format_number(
                        row["interest_coverage"],
                        "x",
                    ),
                    styles["small"],
                ),
            ]
        )

    table = Table(
        data,
        colWidths=[
            22 * mm,
            38 * mm,
            21 * mm,
            21 * mm,
            20 * mm,
            17 * mm,
            17 * mm,
            14 * mm,
            23 * mm,
        ],
        repeatRows=1,
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#E8EDF3"),
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#0B1F3A"),
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    3,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    3,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    4,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    4,
                ),
            ]
        )
    )

    return table


def generate_sector_report(sector_name, sector_df):
    """Generate one PDF report for a sector."""

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    safe_name = (
        str(sector_name)
        .strip()
        .replace("/", "_")
        .replace("\\", "_")
        .replace(" ", "_")
    )

    output_file = (
        OUTPUT_DIR
        / f"{safe_name}_report.pdf"
    )

    styles = build_styles()

    document = SimpleDocTemplate(
        str(output_file),
        pagesize=A4,
        rightMargin=12 * mm,
        leftMargin=12 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
        title=f"{sector_name} Sector Report",
    )

    story = []

    story.append(
        Paragraph(
            f"{sector_name} Sector Report",
            styles["title"],
        )
    )

    story.append(
        Paragraph(
            f"Companies covered: {len(sector_df)}",
            styles["subtitle"],
        )
    )

    story.append(
        Paragraph(
            "Sector Median KPIs",
            styles["heading"],
        )
    )

    story.append(
        build_sector_summary(
            sector_df,
            styles,
        )
    )

    story.append(
        Spacer(
            1,
            10,
        )
    )

    story.append(
        Paragraph(
            "Companies in Sector",
            styles["heading"],
        )
    )

    story.append(
        build_company_table(
            sector_df,
            styles,
        )
    )

    document.build(story)

    return output_file


def generate_all_sector_reports():
    """Generate reports for all broad sectors."""

    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Database not found: {DB_PATH}"
        )

    df = get_sector_data()

    if df.empty:
        raise ValueError(
            "No sector data found in the database."
        )

    sectors = (
        df["sector"]
        .dropna()
        .astype(str)
        .str.strip()
        .unique()
    )

    sectors = sorted(sectors)

    print(
        f"Total sectors found: {len(sectors)}"
    )

    print()

    generated = 0

    for index, sector_name in enumerate(
        sectors,
        start=1,
    ):

        sector_df = df[
            df["sector"] == sector_name
        ].copy()

        print(
            f"[{index}/{len(sectors)}] "
            f"Generating {sector_name}..."
        )

        try:

            output_file = generate_sector_report(
                sector_name,
                sector_df,
            )

            generated += 1

            print(
                f"  CREATED - {output_file.name}"
            )

        except Exception as error:

            print(
                f"  ERROR - {error}"
            )

    print()
    print("Sector report generation completed.")
    print(
        f"Total sectors: {len(sectors)}"
    )
    print(
        f"Generated reports: {generated}"
    )
    print(
        f"Output directory: {OUTPUT_DIR}"
    )


def main():
    """Run sector report generation."""

    generate_all_sector_reports()


if __name__ == "__main__":
    main()

