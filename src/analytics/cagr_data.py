import sqlite3


DB_PATH = "data/nifty100.db"


def get_financial_data_by_year(company_id, db_path=DB_PATH):
    """
    Return Revenue, PAT and EPS data by year for one company.

    TTM and other non-numeric years are ignored.
    """

    connection = sqlite3.connect(db_path)

    rows = connection.execute(
        """
        SELECT year, sales, net_profit, eps
        FROM profitandloss
        WHERE company_id = ?
          AND typeof(year) = 'integer'
        ORDER BY year
        """,
        (company_id,),
    ).fetchall()

    connection.close()

    revenue_by_year = {}
    pat_by_year = {}
    eps_by_year = {}

    for year, sales, net_profit, eps in rows:
        revenue_by_year[year] = sales
        pat_by_year[year] = net_profit
        eps_by_year[year] = eps

    return {
        "revenue": revenue_by_year,
        "pat": pat_by_year,
        "eps": eps_by_year,
    }
