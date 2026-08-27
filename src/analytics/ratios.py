# Day 08 - Profitability Ratios

import logging
import math


logger = logging.getLogger(__name__)


def _is_valid_number(value):
    """
    Return True when value is a finite numeric value.
    """

    if value is None:
        return False

    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def net_profit_margin(net_profit, sales):
    """
    Net Profit Margin = Net Profit / Sales * 100
    """

    if not _is_valid_number(net_profit):
        return None

    if not _is_valid_number(sales):
        return None

    if sales == 0:
        return None

    return (net_profit / sales) * 100


def operating_profit_margin(operating_profit, sales):
    """
    Operating Profit Margin = Operating Profit / Sales * 100
    """

    if not _is_valid_number(operating_profit):
        return None

    if not _is_valid_number(sales):
        return None

    if sales == 0:
        return None

    return (operating_profit / sales) * 100


def opm_mismatch(computed_opm, source_opm):
    """
    Check whether calculated OPM differs from the source
    by more than one percentage point.
    """

    if not _is_valid_number(computed_opm):
        return False

    if not _is_valid_number(source_opm):
        return False

    mismatch = abs(computed_opm - source_opm) > 1

    if mismatch:
        logger.warning(
            "OPM mismatch: computed=%.2f%%, source=%.2f%%",
            computed_opm,
            source_opm,
        )

    return mismatch


def return_on_equity(
    net_profit,
    equity_capital,
    reserves,
):
    """
    Return on Equity = Net Profit / Total Equity * 100

    Total Equity = Equity Capital + Reserves.

    The function uses the database values as supplied.
    """

    if not _is_valid_number(net_profit):
        return None

    if not _is_valid_number(equity_capital):
        return None

    if not _is_valid_number(reserves):
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
    borrowings,
):
    """
    Return on Capital Employed = EBIT / Capital Employed * 100

    EBIT = Operating Profit + Other Income

    Capital Employed = Equity Capital + Reserves + Borrowings

    The function uses the database values as supplied.
    """

    if not _is_valid_number(operating_profit):
        return None

    if not _is_valid_number(other_income):
        return None

    if not _is_valid_number(equity_capital):
        return None

    if not _is_valid_number(reserves):
        return None

    if not _is_valid_number(borrowings):
        return None

    ebit = operating_profit + other_income

    capital_employed = (
        equity_capital
        + reserves
        + borrowings
    )

    if capital_employed <= 0:
        return None

    return (ebit / capital_employed) * 100


def return_on_assets(net_profit, total_assets):
    """
    Return on Assets = Net Profit / Total Assets * 100
    """

    if not _is_valid_number(net_profit):
        return None

    if not _is_valid_number(total_assets):
        return None

    if total_assets <= 0:
        return None

    return (net_profit / total_assets) * 100


def is_financials_sector(broad_sector):
    """
    Return True when the company belongs to Financials.
    """

    if broad_sector is None:
        return False

    return broad_sector.strip().lower() == "financials"


def roce_benchmark_flag(
    roce,
    broad_sector,
    sector_roce_benchmark,
):
    """
    Flag Financials companies whose ROCE is below the
    configured benchmark.
    """

    if not _is_valid_number(roce):
        return False

    if not _is_valid_number(sector_roce_benchmark):
        return False

    if is_financials_sector(broad_sector):
        return roce < sector_roce_benchmark

    return False


# Day 09 - Leverage and Efficiency Ratios


def debt_to_equity(
    borrowings,
    equity_capital,
    reserves,
):
    """
    Debt-to-Equity = Borrowings / Total Equity

    Total Equity = Equity Capital + Reserves.
    """

    if not _is_valid_number(borrowings):
        return None

    if borrowings == 0:
        return 0.0

    if not _is_valid_number(equity_capital):
        return None

    if not _is_valid_number(reserves):
        return None

    equity = equity_capital + reserves

    if equity <= 0:
        return None

    return borrowings / equity


def high_leverage_flag(
    debt_equity,
    broad_sector,
):
    """
    Flag non-financial companies with D/E above 5.

    Financial companies are excluded because a high D/E ratio
    is structurally normal for banks and financial institutions.
    """

    if not _is_valid_number(debt_equity):
        return False

    if is_financials_sector(broad_sector):
        return False

    return debt_equity > 5


def interest_coverage_ratio(
    operating_profit,
    other_income,
    interest,
):
    """
    Interest Coverage Ratio =
        (Operating Profit + Other Income) / Interest
    """

    if not _is_valid_number(operating_profit):
        return None

    if not _is_valid_number(other_income):
        return None

    if not _is_valid_number(interest):
        return None

    if interest == 0:
        return None

    return (operating_profit + other_income) / interest


def interest_coverage_label(icr):
    """
    Return a label when interest coverage is unavailable.
    """

    if icr is None:
        return "Debt Free"

    return None


def icr_warning_flag(icr):
    """
    Flag companies with interest coverage below 1.5x.
    """

    if not _is_valid_number(icr):
        return False

    return icr < 1.5


def asset_turnover_ratio(
    sales,
    total_assets,
):
    """
    Asset Turnover = Sales / Total Assets
    """

    if not _is_valid_number(sales):
        return None

    if not _is_valid_number(total_assets):
        return None

    if total_assets <= 0:
        return None

    return sales / total_assets


def net_debt(
    borrowings,
    investments,
):
    """
    Net Debt = Borrowings - Investments
    """

    if not _is_valid_number(borrowings):
        return None

    if not _is_valid_number(investments):
        return None

    return borrowings - investments
