import sqlite3


DB_PATH = "data/nifty100.db"


def get_ratio_data_by_year(company_id, db_path=DB_PATH):
    """
    Return the raw financial inputs required for ratio calculations.

    Annual financial data is taken from the March year-end period
    (for example, 'Mar 2024').

    Non-annual periods such as TTM, quarterly and partial-year
    records are ignored.
    """

    connection = sqlite3.connect(db_path)

    rows = connection.execute(
        """
        SELECT
            p.year,
            p.sales,
            p.operating_profit,
            p.other_income,
            p.interest,
            p.net_profit,

            b.equity_capital,
            b.reserves,
            b.borrowings,
            b.investments,
            b.total_assets,

            s.broad_sector

        FROM profitandloss AS p

        LEFT JOIN balancesheet AS b
            ON p.company_id = b.company_id
            AND p.period = b.period

        LEFT JOIN sectors AS s
            ON p.company_id = s.company_id

        WHERE p.company_id = ?
          AND p.period LIKE 'Mar %'

        ORDER BY CAST(p.year AS INTEGER)
        """,
        (company_id,),
    ).fetchall()

    connection.close()

    result = {
        "sales": {},
        "operating_profit": {},
        "other_income": {},
        "interest": {},
        "net_profit": {},
        "equity_capital": {},
        "reserves": {},
        "borrowings": {},
        "investments": {},
        "total_assets": {},
        "broad_sector": {},
    }

    for (
        year,
        sales,
        operating_profit,
        other_income,
        interest,
        net_profit,
        equity_capital,
        reserves,
        borrowings,
        investments,
        total_assets,
        broad_sector,
    ) in rows:

        # Database year is stored as text, so convert it to an integer.
        try:
            year = int(str(year).strip())
        except (TypeError, ValueError):
            continue

        result["sales"][year] = sales
        result["operating_profit"][year] = operating_profit
        result["other_income"][year] = other_income
        result["interest"][year] = interest
        result["net_profit"][year] = net_profit

        result["equity_capital"][year] = equity_capital
        result["reserves"][year] = reserves
        result["borrowings"][year] = borrowings
        result["investments"][year] = investments
        result["total_assets"][year] = total_assets

        result["broad_sector"][year] = broad_sector

    return result
