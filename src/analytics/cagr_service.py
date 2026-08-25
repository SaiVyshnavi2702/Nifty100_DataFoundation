from src.analytics.cagr import calculate_all_cagrs
from src.analytics.cagr_data import get_financial_data_by_year


def calculate_company_cagrs(company_id, end_year, db_path="data/nifty100.db"):
    """
    Calculate 3-year, 5-year and 10-year CAGR for
    Revenue, PAT and EPS for one company.
    """

    financial_data = get_financial_data_by_year(
        company_id,
        db_path=db_path,
    )

    result = {}

    for metric in ("revenue", "pat", "eps"):
        values_by_year = financial_data[metric]

        cagrs = calculate_all_cagrs(
            values_by_year,
            end_year,
        )

        result[metric] = cagrs

    return result
