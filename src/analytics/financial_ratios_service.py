import sqlite3

from src.analytics.ratios_service import calculate_company_ratios
from src.analytics.cagr_service import calculate_company_cagrs
from src.analytics.quality_score import calculate_composite_quality_score
from src.analytics.cashflow_kpis import calculate_free_cash_flow


DB_PATH = "data/nifty100.db"


def is_annual_march_period(period):
    """Check whether the period is a valid annual March period."""

    if not isinstance(period, str):
        return False

    parts = period.strip().split()

    return (
        len(parts) == 2
        and parts[0] == "Mar"
        and parts[1].isdigit()
        and len(parts[1]) == 4
    )


def calculate_book_value_per_share(
    equity_capital,
    reserves,
    face_value,
):
    """
    Calculate book value per share.

    Number of shares is estimated from:
        equity capital / face value

    Then:
        BVPS = total equity / number of shares
    """

    if equity_capital is None:
        return None

    if reserves is None:
        return None

    if face_value is None or face_value == 0:
        return None

    if equity_capital == 0:
        return None

    shares = equity_capital / face_value

    if shares == 0:
        return None

    total_equity = equity_capital + reserves

    return total_equity / shares


def get_annual_financial_rows(connection):
    """
    Get annual March financial data required for Day 12.

    Only exact annual March periods are accepted.
    TTM, quarterly and partial-year periods are ignored.
    """

    rows = connection.execute(
        """
        SELECT
            p.company_id,
            p.year,
            p.period,

            p.sales,
            p.net_profit,
            p.eps,
            p.dividend_payout,
            p.operating_profit,
            p.other_income,
            p.interest,

            b.equity_capital,
            b.reserves,
            b.borrowings,
            b.investments,
            b.total_assets,

            c.face_value,

            cf.operating_activity,
            cf.investing_activity

        FROM profitandloss AS p

        LEFT JOIN balancesheet AS b
            ON p.company_id = b.company_id
            AND p.period = b.period

        LEFT JOIN companies AS c
            ON p.company_id = c.id

        LEFT JOIN cashflow AS cf
            ON p.company_id = cf.company_id
            AND p.period = cf.period

        WHERE p.period LIKE 'Mar %'

        ORDER BY
            p.company_id,
            p.year
        """
    ).fetchall()

    return [
        row
        for row in rows
        if is_annual_march_period(row[2])
    ]


def calculate_day12_kpis(
    company_id,
    year,
    sales,
    net_profit,
    eps,
    dividend_payout,
    equity_capital,
    reserves,
    borrowings,
    investments,
    face_value,
    operating_activity,
    investing_activity,
):
    """Calculate all Day 12 KPI values for one company/year."""

    ratios = calculate_company_ratios(
        company_id,
        year,
    )

    free_cash_flow = calculate_free_cash_flow(
        operating_activity,
        investing_activity,
    )

    book_value_per_share = calculate_book_value_per_share(
        equity_capital,
        reserves,
        face_value,
    )

    cagrs = calculate_company_cagrs(
        company_id,
        year,
        db_path=DB_PATH,
    )

    revenue_cagr = cagrs["revenue"].get("cagr_5yr")
    pat_cagr = cagrs["pat"].get("cagr_5yr")
    eps_cagr = cagrs["eps"].get("cagr_5yr")

    quality_score = calculate_composite_quality_score(
        revenue_cagr,
        pat_cagr,
        eps_cagr,
    )

    return {
        "net_profit_margin_pct":
            ratios.get("net_profit_margin"),

        "operating_profit_margin_pct":
            ratios.get("operating_profit_margin"),

        "return_on_equity_pct":
            ratios.get("return_on_equity"),

        "debt_to_equity":
            ratios.get("debt_to_equity"),

        "interest_coverage":
            ratios.get("interest_coverage"),

        "asset_turnover":
            ratios.get("asset_turnover"),

        "free_cash_flow_cr":
            free_cash_flow,

        "capex_cr":
            investing_activity,

        "earnings_per_share":
            eps,

        "book_value_per_share":
            book_value_per_share,

        "dividend_payout_ratio_pct":
            dividend_payout,

        "total_debt_cr":
            borrowings,

        "cash_from_operations_cr":
            operating_activity,

        "revenue_cagr_5yr":
            revenue_cagr,

        "pat_cagr_5yr":
            pat_cagr,

        "eps_cagr_5yr":
            eps_cagr,

        "composite_quality_score":
            quality_score,
    }


def save_financial_ratio(
    connection,
    company_id,
    year,
    period,
    kpis,
):
    """Insert or update one financial_ratios row."""

    connection.execute(
        """
        INSERT INTO financial_ratios (
            company_id,
            year,
            period,

            net_profit_margin_pct,
            operating_profit_margin_pct,
            return_on_equity_pct,
            debt_to_equity,
            interest_coverage,
            asset_turnover,

            free_cash_flow_cr,
            capex_cr,
            earnings_per_share,
            book_value_per_share,
            dividend_payout_ratio_pct,

            total_debt_cr,
            cash_from_operations_cr,

            revenue_cagr_5yr,
            pat_cagr_5yr,
            eps_cagr_5yr,
            composite_quality_score
        )

        VALUES (
            ?, ?, ?,
            ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?,
            ?, ?,
            ?, ?, ?, ?
        )

        ON CONFLICT(company_id, period)
        DO UPDATE SET
            year = excluded.year,

            net_profit_margin_pct =
                excluded.net_profit_margin_pct,

            operating_profit_margin_pct =
                excluded.operating_profit_margin_pct,

            return_on_equity_pct =
                excluded.return_on_equity_pct,

            debt_to_equity =
                excluded.debt_to_equity,

            interest_coverage =
                excluded.interest_coverage,

            asset_turnover =
                excluded.asset_turnover,

            free_cash_flow_cr =
                excluded.free_cash_flow_cr,

            capex_cr =
                excluded.capex_cr,

            earnings_per_share =
                excluded.earnings_per_share,

            book_value_per_share =
                excluded.book_value_per_share,

            dividend_payout_ratio_pct =
                excluded.dividend_payout_ratio_pct,

            total_debt_cr =
                excluded.total_debt_cr,

            cash_from_operations_cr =
                excluded.cash_from_operations_cr,

            revenue_cagr_5yr =
                excluded.revenue_cagr_5yr,

            pat_cagr_5yr =
                excluded.pat_cagr_5yr,

            eps_cagr_5yr =
                excluded.eps_cagr_5yr,

            composite_quality_score =
                excluded.composite_quality_score
        """,
        (
            company_id,
            year,
            period,

            kpis["net_profit_margin_pct"],
            kpis["operating_profit_margin_pct"],
            kpis["return_on_equity_pct"],
            kpis["debt_to_equity"],
            kpis["interest_coverage"],
            kpis["asset_turnover"],

            kpis["free_cash_flow_cr"],
            kpis["capex_cr"],
            kpis["earnings_per_share"],
            kpis["book_value_per_share"],
            kpis["dividend_payout_ratio_pct"],

            kpis["total_debt_cr"],
            kpis["cash_from_operations_cr"],

            kpis["revenue_cagr_5yr"],
            kpis["pat_cagr_5yr"],
            kpis["eps_cagr_5yr"],
            kpis["composite_quality_score"],
        ),
    )


def populate_financial_ratios(db_path=DB_PATH):
    """Populate the financial_ratios table for all annual March data."""

    connection = sqlite3.connect(db_path)

    try:
        rows = get_annual_financial_rows(connection)

        print("DAY 12 - FINANCIAL RATIOS")
        print("--------------------------------")
        print("Annual March source rows:", len(rows))

        processed = 0
        scored = 0

        for row in rows:

            (
                company_id,
                year,
                period,

                sales,
                net_profit,
                eps,
                dividend_payout,
                operating_profit,
                other_income,
                interest,

                equity_capital,
                reserves,
                borrowings,
                investments,
                total_assets,

                face_value,

                operating_activity,
                investing_activity,
            ) = row

            kpis = calculate_day12_kpis(
                company_id,
                year,
                sales,
                net_profit,
                eps,
                dividend_payout,
                equity_capital,
                reserves,
                borrowings,
                investments,
                face_value,
                operating_activity,
                investing_activity,
            )

            save_financial_ratio(
                connection,
                company_id,
                year,
                period,
                kpis,
            )

            processed += 1

            if kpis["composite_quality_score"] is not None:
                scored += 1

        connection.commit()

        final_count = connection.execute(
            """
            SELECT COUNT(*)
            FROM financial_ratios
            """
        ).fetchone()[0]

        print("Rows processed:", processed)
        print("Rows with quality score:", scored)
        print("Final financial_ratios rows:", final_count)

    finally:
        connection.close()

if __name__ == "__main__":
    populate_financial_ratios()