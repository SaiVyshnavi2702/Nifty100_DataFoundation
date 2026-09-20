import math

from src.analytics.cagr import calculate_cagr
from src.analytics.cashflow_kpis import (
    calculate_cfo_pat_ratio,
    calculate_cfo_quality_score,
)
from src.analytics.ratios import (
    debt_to_equity,
    high_leverage_flag,
    interest_coverage_ratio,
    operating_profit_margin,
    opm_mismatch,
    return_on_equity,
)

# ROE tests


def test_roe_with_positive_equity():
    result = return_on_equity(
        net_profit=200,
        equity_capital=500,
        reserves=500,
    )

    assert result == 20.0


def test_roe_with_negative_equity_returns_none():
    result = return_on_equity(
        net_profit=200,
        equity_capital=-600,
        reserves=500,
    )

    assert result is None


def test_roe_with_zero_equity_returns_none():
    result = return_on_equity(
        net_profit=200,
        equity_capital=500,
        reserves=-500,
    )

    assert result is None


# D/E tests


def test_debt_free_company_returns_zero():
    result = debt_to_equity(
        borrowings=0,
        equity_capital=500,
        reserves=500,
    )

    assert result == 0.0


def test_debt_to_equity_normal_calculation():
    result = debt_to_equity(
        borrowings=200,
        equity_capital=500,
        reserves=500,
    )

    assert result == 0.2


def test_high_leverage_flag_for_non_financial_company():
    result = high_leverage_flag(
        debt_equity=6.0,
        broad_sector="Industrials",
    )

    assert result is True


def test_high_leverage_flag_excludes_financials():
    result = high_leverage_flag(
        debt_equity=8.0,
        broad_sector="Financials",
    )

    assert result is False


# Interest Coverage Ratio tests


def test_icr_when_interest_zero_returns_none():
    result = interest_coverage_ratio(
        operating_profit=500,
        other_income=100,
        interest=0,
    )

    assert result is None


def test_icr_normal_calculation():
    result = interest_coverage_ratio(
        operating_profit=500,
        other_income=100,
        interest=100,
    )

    assert result == 6.0


# CAGR tests


def test_cagr_turnaround_flag():
    value, flag = calculate_cagr(
        start_value=-100,
        end_value=200,
        years=5,
    )

    assert value is None
    assert flag == "TURNAROUND"


def test_cagr_decline_to_loss_flag():
    value, flag = calculate_cagr(
        start_value=200,
        end_value=-100,
        years=5,
    )

    assert value is None
    assert flag == "DECLINE_TO_LOSS"


def test_normal_cagr_calculation():
    value, flag = calculate_cagr(
        start_value=100,
        end_value=121,
        years=2,
    )

    assert math.isclose(value, 10.0, rel_tol=1e-9)
    assert flag is None


def test_cagr_zero_base_flag():
    value, flag = calculate_cagr(
        start_value=0,
        end_value=100,
        years=5,
    )

    assert value is None
    assert flag == "ZERO_BASE"


# OPM cross-check tests


def test_opm_cross_check_divergence_flag():
    computed_opm = operating_profit_margin(
        operating_profit=200,
        sales=1000,
    )

    source_opm = 15.0

    assert computed_opm == 20.0
    assert opm_mismatch(computed_opm, source_opm) is True


def test_opm_cross_check_no_divergence():
    computed_opm = operating_profit_margin(
        operating_profit=200,
        sales=1000,
    )

    source_opm = 20.5

    assert computed_opm == 20.0
    assert opm_mismatch(computed_opm, source_opm) is False


# CFO quality tests


def test_cfo_quality_score_calculation():
    rows = [
        {
            "year": 2020,
            "operating_activity": 120,
            "net_profit": 100,
        },
        {
            "year": 2021,
            "operating_activity": 150,
            "net_profit": 100,
        },
        {
            "year": 2022,
            "operating_activity": 180,
            "net_profit": 120,
        },
        {
            "year": 2023,
            "operating_activity": 160,
            "net_profit": 100,
        },
        {
            "year": 2024,
            "operating_activity": 200,
            "net_profit": 100,
        },
    ]

    result = calculate_cfo_quality_score(
        rows,
        current_year=2024,
    )

    expected = (1.2 + 1.5 + 1.5 + 1.6 + 2.0) / 5

    assert math.isclose(
        result,
        expected,
        rel_tol=1e-9,
    )


def test_cfo_quality_uses_latest_five_years():
    rows = [
        {
            "year": 2018,
            "operating_activity": 1000,
            "net_profit": 100,
        },
        {
            "year": 2019,
            "operating_activity": 120,
            "net_profit": 100,
        },
        {
            "year": 2020,
            "operating_activity": 120,
            "net_profit": 100,
        },
        {
            "year": 2021,
            "operating_activity": 120,
            "net_profit": 100,
        },
        {
            "year": 2022,
            "operating_activity": 120,
            "net_profit": 100,
        },
        {
            "year": 2023,
            "operating_activity": 120,
            "net_profit": 100,
        },
        {
            "year": 2024,
            "operating_activity": 120,
            "net_profit": 100,
        },
    ]

    result = calculate_cfo_quality_score(
        rows,
        current_year=2024,
    )

    assert result == 1.2


def test_cfo_pat_ratio_calculation():
    result = calculate_cfo_pat_ratio(
        cfo=150,
        pat=100,
    )

    assert result == 1.5


def test_cfo_pat_ratio_zero_pat_returns_none():
    result = calculate_cfo_pat_ratio(
        cfo=100,
        pat=0,
    )

    assert result is None


def test_cfo_quality_score_returns_none_when_no_valid_ratios():
    rows = [
        {
            "year": 2024,
            "operating_activity": 100,
            "net_profit": 0,
        }
    ]

    result = calculate_cfo_quality_score(
        rows,
        current_year=2024,
    )

    assert result is None
