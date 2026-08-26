import pytest

from src.analytics.cashflow_kpis import (
    calculate_free_cash_flow,
    calculate_cfo_pat_ratio,
    calculate_cfo_quality_score,
    classify_cfo_quality,
    calculate_capex_intensity,
    classify_capex_intensity,
    calculate_fcf_conversion_rate,
    get_cashflow_sign,
    classify_capital_allocation,
    is_annual_march_period
)


def test_free_cash_flow():
    assert calculate_free_cash_flow(
        100,
        -40
    ) == 60


def test_negative_free_cash_flow():
    assert calculate_free_cash_flow(
        50,
        -100
    ) == -50


def test_cfo_pat_ratio():
    assert calculate_cfo_pat_ratio(
        120,
        100
    ) == pytest.approx(1.2)


def test_pat_zero_returns_none():
    assert calculate_cfo_pat_ratio(
        100,
        0
    ) is None


def test_five_year_rolling_cfo_quality_score():

    rows = [
        {
            "year": 2020,
            "operating_activity": 60,
            "net_profit": 100
        },
        {
            "year": 2021,
            "operating_activity": 80,
            "net_profit": 100
        },
        {
            "year": 2022,
            "operating_activity": 100,
            "net_profit": 100
        },
        {
            "year": 2023,
            "operating_activity": 120,
            "net_profit": 100
        },
        {
            "year": 2024,
            "operating_activity": 140,
            "net_profit": 100
        }
    ]

    score_2022 = calculate_cfo_quality_score(
        rows,
        2022
    )

    assert score_2022 == pytest.approx(
        (0.6 + 0.8 + 1.0) / 3
    )

    score_2024 = calculate_cfo_quality_score(
        rows,
        2024
    )

    assert score_2024 == pytest.approx(
        (0.6 + 0.8 + 1.0 + 1.2 + 1.4) / 5
    )


def test_cfo_quality_score_uses_latest_five_years():

    rows = [
        {
            "year": 2019,
            "operating_activity": 50,
            "net_profit": 100
        },
        {
            "year": 2020,
            "operating_activity": 60,
            "net_profit": 100
        },
        {
            "year": 2021,
            "operating_activity": 80,
            "net_profit": 100
        },
        {
            "year": 2022,
            "operating_activity": 100,
            "net_profit": 100
        },
        {
            "year": 2023,
            "operating_activity": 120,
            "net_profit": 100
        },
        {
            "year": 2024,
            "operating_activity": 140,
            "net_profit": 100
        }
    ]

    score = calculate_cfo_quality_score(
        rows,
        2024
    )

    expected = (
        0.6 +
        0.8 +
        1.0 +
        1.2 +
        1.4
    ) / 5

    assert score == pytest.approx(
        expected
    )


def test_cfo_quality_ignores_zero_pat():

    rows = [
        {
            "year": 2020,
            "operating_activity": 100,
            "net_profit": 0
        },
        {
            "year": 2021,
            "operating_activity": 100,
            "net_profit": 100
        },
        {
            "year": 2022,
            "operating_activity": 100,
            "net_profit": 100
        }
    ]

    score = calculate_cfo_quality_score(
        rows,
        2022
    )

    assert score == pytest.approx(1.0)


def test_cfo_quality_all_zero_pat_returns_none():

    rows = [
        {
            "year": 2020,
            "operating_activity": 100,
            "net_profit": 0
        },
        {
            "year": 2021,
            "operating_activity": 100,
            "net_profit": 0
        }
    ]

    score = calculate_cfo_quality_score(
        rows,
        2021
    )

    assert score is None


def test_cfo_quality_high():
    assert classify_cfo_quality(
        1.01
    ) == "High Quality"


def test_cfo_quality_moderate():
    assert classify_cfo_quality(
        0.5
    ) == "Moderate"

    assert classify_cfo_quality(
        1.0
    ) == "Moderate"


def test_cfo_quality_accrual_risk():
    assert classify_cfo_quality(
        0.49
    ) == "Accrual Risk"


def test_capex_intensity():
    assert calculate_capex_intensity(
        -20,
        1000
    ) == pytest.approx(2.0)


def test_capex_zero_sales():
    assert calculate_capex_intensity(
        -100,
        0
    ) is None


def test_capex_asset_light():
    assert classify_capex_intensity(
        2.99
    ) == "Asset Light"


def test_capex_moderate():
    assert classify_capex_intensity(
        3.0
    ) == "Moderate"

    assert classify_capex_intensity(
        8.0
    ) == "Moderate"


def test_capex_capital_intensive():
    assert classify_capex_intensity(
        8.01
    ) == "Capital Intensive"


def test_fcf_conversion():
    assert calculate_fcf_conversion_rate(
        80,
        100
    ) == pytest.approx(80.0)


def test_fcf_conversion_zero_operating_profit():
    assert calculate_fcf_conversion_rate(
        100,
        0
    ) is None


def test_cashflow_signs():
    assert get_cashflow_sign(100) == "+"
    assert get_cashflow_sign(-100) == "-"
    assert get_cashflow_sign(0) == "0"


def test_annual_march_period():

    assert is_annual_march_period(
        "Mar 2024"
    )

    assert is_annual_march_period(
        "Mar 2013"
    )

    assert not is_annual_march_period(
        "Mar 24"
    )

    assert not is_annual_march_period(
        "Mar 2023 15"
    )

    assert not is_annual_march_period(
        "Mar 2016 9m"
    )

    assert not is_annual_march_period(
        "TTM"
    )

    assert not is_annual_march_period(
        "Dec 2023"
    )


def test_reinvestor():

    assert classify_capital_allocation(
        100,
        -80,
        -20,
        1.0
    ) == "Reinvestor"


def test_shareholder_returns():

    assert classify_capital_allocation(
        150,
        -50,
        -100,
        1.01
    ) == "Shareholder Returns"


def test_liquidating_assets():

    assert classify_capital_allocation(
        100,
        50,
        -50
    ) == "Liquidating Assets"


def test_distress_signal():

    assert classify_capital_allocation(
        -100,
        50,
        50
    ) == "Distress Signal"


def test_growth_funded_by_debt():

    assert classify_capital_allocation(
        -100,
        -50,
        150
    ) == "Growth Funded by Debt"


def test_cash_accumulator():

    assert classify_capital_allocation(
        100,
        50,
        50
    ) == "Cash Accumulator"


def test_pre_revenue():

    assert classify_capital_allocation(
        -100,
        -50,
        -50
    ) == "Pre-Revenue"


def test_mixed():

    assert classify_capital_allocation(
        100,
        -50,
        50
    ) == "Mixed"