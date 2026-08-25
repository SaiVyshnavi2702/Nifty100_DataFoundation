from src.analytics.ratios import (
    net_profit_margin,
    operating_profit_margin,
    return_on_equity,
    return_on_capital_employed,
    return_on_assets,
    debt_to_equity,
    interest_coverage_ratio,
    asset_turnover_ratio,
    net_debt,
)

from src.analytics.ratios_data import get_ratio_data_by_year


def calculate_company_ratios(company_id, year):
    data = get_ratio_data_by_year(company_id)

    if year not in data["sales"]:
        return {
            "company_id": company_id,
            "year": year,
            "status": "INSUFFICIENT",
        }

    sales = data["sales"].get(year)
    operating_profit = data["operating_profit"].get(year)
    other_income = data["other_income"].get(year)
    interest = data["interest"].get(year)
    net_profit = data["net_profit"].get(year)

    equity_capital = data["equity_capital"].get(year)
    reserves = data["reserves"].get(year)
    borrowings = data["borrowings"].get(year)
    investments = data["investments"].get(year)
    total_assets = data["total_assets"].get(year)

    return {
        "company_id": company_id,
        "year": year,
        "status": "OK",

        "net_profit_margin": net_profit_margin(
            net_profit,
            sales,
        ),

        "operating_profit_margin": operating_profit_margin(
            operating_profit,
            sales,
        ),

        "return_on_equity": return_on_equity(
            net_profit,
            equity_capital,
            reserves,
        ),

        "return_on_capital_employed": return_on_capital_employed(
            operating_profit,
            other_income,
            equity_capital,
            reserves,
            borrowings,
        ),

        "return_on_assets": return_on_assets(
            net_profit,
            total_assets,
        ),

        "debt_to_equity": debt_to_equity(
            borrowings,
            equity_capital,
            reserves,
        ),

        "interest_coverage": interest_coverage_ratio(
            operating_profit,
            other_income,
            interest,
        ),

        "asset_turnover": asset_turnover_ratio(
            sales,
            total_assets,
        ),

        "net_debt": net_debt(
            borrowings,
            investments,
        ),
    }
