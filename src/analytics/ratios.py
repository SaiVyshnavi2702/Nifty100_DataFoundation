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

    return abs(computed_opm - source_opm) > 1


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
