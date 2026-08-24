from src.analytics.ratios import (
    net_profit_margin,
    operating_profit_margin,
    opm_mismatch,
    return_on_equity,
    return_on_capital_employed,
    return_on_assets,
)


def test_net_profit_margin():
    assert round(net_profit_margin(20, 100), 2) == 20.00


def test_net_profit_margin_zero_sales():
    assert net_profit_margin(20, 0) is None


def test_operating_profit_margin():
    assert round(operating_profit_margin(30, 100), 2) == 30.00


def test_opm_mismatch():
    assert opm_mismatch(15, 12) is True


def test_return_on_equity():
    assert round(return_on_equity(20, 50, 50), 2) == 20.00


def test_return_on_equity_negative_equity():
    assert return_on_equity(20, -100, 20) is None


def test_return_on_capital_employed():
    result = return_on_capital_employed(
        30,
        10,
        50,
        25,
        25
    )

    assert round(result, 2) == 40.00




def test_return_on_assets_zero_assets():
    assert return_on_assets(20, 0) is None
