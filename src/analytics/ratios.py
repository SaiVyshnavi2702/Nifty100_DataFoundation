# Day 08 - Profitability Ratios

import logging

logger = logging.getLogger(__name__)


def net_profit_margin(net_profit, sales):
    if sales is None or sales == 0:
        return None

    if net_profit is None:
        return None

    return (net_profit / sales) * 100


def operating_profit_margin(operating_profit, sales):
    if sales is None or sales == 0:
        return None

    if operating_profit is None:
        return None

    return (operating_profit / sales) * 100


def opm_mismatch(computed_opm, source_opm):
    if computed_opm is None or source_opm is None:
        return False

    mismatch = abs(computed_opm - source_opm) > 1

    if mismatch:
        logger.warning(
            "OPM mismatch: computed=%.2f%%, source=%.2f%%",
            computed_opm,
            source_opm
        )

    return mismatch


def return_on_equity(net_profit, equity_capital, reserves):
    if net_profit is None:
        return None

    if equity_capital is None or reserves is None:
        return None

    equity = equity_capital + reserves

    if equity <= 0:
        return None

    return (net_profit / equity) * 100


def return_on_capital_employed(
    operating_profit,
    other_income,
    equity_capital,
    reserves,
    borrowings
):
    if operating_profit is None or other_income is None:
        return None

    if equity_capital is None or reserves is None or borrowings is None:
        return None

    ebit = operating_profit + other_income
    capital_employed = equity_capital + reserves + borrowings

    if capital_employed <= 0:
        return None

    return (ebit / capital_employed) * 100


def return_on_assets(net_profit, total_assets):
    if net_profit is None:
        return None

    if total_assets is None or total_assets == 0:
        return None

    return (net_profit / total_assets) * 100


def is_financials_sector(broad_sector):
    if broad_sector is None:
        return False

    return broad_sector.strip().lower() == "financials"


def roce_benchmark_flag(roce, broad_sector, sector_roce_benchmark):
    if roce is None or sector_roce_benchmark is None:
        return False

    if is_financials_sector(broad_sector):
        return roce < sector_roce_benchmark

    return False


# Day 09 - Leverage & Efficiency Ratios

def debt_to_equity(borrowings, equity_capital, reserves):
    if borrowings is None:
        return None

    if borrowings == 0:
        return 0.0

    if equity_capital is None or reserves is None:
        return None

    equity = equity_capital + reserves

    if equity <= 0:
        return None

    return borrowings / equity


def high_leverage_flag(debt_equity, broad_sector):
    if debt_equity is None:
        return False

    if is_financials_sector(broad_sector):
        return False

    return debt_equity > 5


def interest_coverage_ratio(operating_profit, other_income, interest):
    if operating_profit is None or other_income is None or interest is None:
        return None

    if interest == 0:
        return None

    return (operating_profit + other_income) / interest


def interest_coverage_label(icr):
    if icr is None:
        return "Debt Free"

    return None


def icr_warning_flag(icr):
    if icr is None:
        return False

    return icr < 1.5


def asset_turnover_ratio(sales, total_assets):
    if sales is None or total_assets is None:
        return None

    if total_assets <= 0:
        return None

    return sales / total_assets

def net_debt(borrowings, investments):
    if borrowings is None or investments is None:
        return None

    return borrowings - investments
