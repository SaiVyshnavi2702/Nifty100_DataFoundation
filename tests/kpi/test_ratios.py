# Day 08 - Profitability Ratios

from src.analytics.ratios import (
    net_profit_margin,
    operating_profit_margin,
    opm_mismatch,
    return_on_equity,
    return_on_capital_employed,
    return_on_assets,
    roce_benchmark_flag,
)

# Day 09 - Leverage & Efficiency Ratios

from src.analytics.ratios import (
    debt_to_equity,
    is_financials_sector,
    high_leverage_flag,
    interest_coverage_ratio,
    interest_coverage_label,
    icr_warning_flag,
    asset_turnover_ratio,
    net_debt,
)


# ============================================================
# Day 08 - Profitability Ratios
# ============================================================

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


def test_opm_mismatch_logs_warning(caplog):
    with caplog.at_level("WARNING"):
        result = opm_mismatch(15, 12)

    assert result is True
    assert "OPM mismatch" in caplog.text



def test_roce_financials_benchmark():
    result = roce_benchmark_flag(8.0, "Financials", 10.0)

    assert result is True


def test_roce_financials_above_benchmark():
    result = roce_benchmark_flag(12.0, "Financials", 10.0)

    assert result is False


# ============================================================
# Day 09 - Leverage & Efficiency Ratios
# ============================================================

def test_debt_to_equity_normal():
    result = debt_to_equity(200, 300, 700)

    assert result == 0.2


def test_debt_to_equity_debt_free():
    result = debt_to_equity(0, 300, 700)

    assert result == 0.0


def test_high_leverage_flag_non_financials():
    result = high_leverage_flag(6.0, "Information Technology")

    assert result is True


def test_high_leverage_flag_financials():
    result = high_leverage_flag(6.0, "Financials")

    assert result is False


def test_interest_coverage_ratio():
    result = interest_coverage_ratio(500, 100, 100)

    assert result == 6.0


def test_interest_coverage_ratio_zero_interest():
    result = interest_coverage_ratio(500, 100, 0)

    assert result is None


def test_interest_coverage_label():
    result = interest_coverage_label(None)

    assert result == "Debt Free"


def test_icr_warning_flag_no_warning():
    result = icr_warning_flag(3.0)

    assert result is False


def test_asset_turnover_ratio():
    result = asset_turnover_ratio(500, 250)

    assert result == 2.0

def test_net_debt():
    result = net_debt(500, 100)

    assert result == 400
