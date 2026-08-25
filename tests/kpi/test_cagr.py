from src.analytics.cagr import (
    calculate_cagr,
    calculate_period_cagr,
    calculate_all_cagrs,
    calculate_financial_cagrs,
)



def test_normal_cagr():
    value, flag = calculate_cagr(100, 150, 5)

    assert round(value, 2) == 8.45
    assert flag is None


def test_decline_to_loss():
    value, flag = calculate_cagr(100, -50, 5)

    assert value is None
    assert flag == "DECLINE_TO_LOSS"


def test_turnaround():
    value, flag = calculate_cagr(-50, 100, 5)

    assert value is None
    assert flag == "TURNAROUND"


def test_both_negative():
    value, flag = calculate_cagr(-100, -50, 5)

    assert value is None
    assert flag == "BOTH_NEGATIVE"


def test_zero_base():
    value, flag = calculate_cagr(0, 100, 5)

    assert value is None
    assert flag == "ZERO_BASE"


def test_insufficient_data():
    data = {
        2021: 100,
        2022: 110,
        2023: 120,
        2024: 130,
        2025: 140,
    }

    value, flag = calculate_period_cagr(data, 2025, 10)

    assert value is None
    assert flag == "INSUFFICIENT"


def test_three_year_cagr():
    data = {
        2022: 100,
        2023: 110,
        2024: 121,
        2025: 133.1,
    }

    value, flag = calculate_period_cagr(data, 2025, 3)

    assert round(value, 2) == 10.00
    assert flag is None


def test_five_year_cagr():
    data = {
        2020: 100,
        2021: 105,
        2022: 110,
        2023: 115,
        2024: 120,
        2025: 150,
    }

    value, flag = calculate_period_cagr(data, 2025, 5)

    assert round(value, 2) == 8.45
    assert flag is None


def test_ten_year_cagr():
    data = {
        2015: 100,
        2016: 105,
        2017: 110,
        2018: 115,
        2019: 120,
        2020: 125,
        2021: 130,
        2022: 135,
        2023: 140,
        2024: 145,
        2025: 200,
    }

    value, flag = calculate_period_cagr(data, 2025, 10)

    assert round(value, 2) == 7.18
    assert flag is None


def test_all_cagrs():
    data = {
        2015: 100,
        2016: 105,
        2017: 110,
        2018: 115,
        2019: 120,
        2020: 125,
        2021: 130,
        2022: 135,
        2023: 140,
        2024: 145,
        2025: 150,
    }

    result = calculate_all_cagrs(data, 2025)

    assert "cagr_3yr" in result
    assert "cagr_3yr_flag" in result

    assert "cagr_5yr" in result
    assert "cagr_5yr_flag" in result

    assert "cagr_10yr" in result
    assert "cagr_10yr_flag" in result

def test_financial_cagrs():
    revenue = {
        2019: 100,
        2020: 105,
        2021: 110,
        2022: 120,
        2023: 135,
        2024: 150,
    }

    pat = {
        2019: 50,
        2020: 52,
        2021: 55,
        2022: 60,
        2023: 65,
        2024: 75,
    }

    eps = {
        2019: 10,
        2020: 10.5,
        2021: 11,
        2022: 12,
        2023: 13.5,
        2024: 15,
    }

    result = calculate_financial_cagrs(
        revenue,
        pat,
        eps,
        2024,
    )

    assert "revenue_cagr_3yr" in result
    assert "revenue_cagr_3yr_flag" in result

    assert "revenue_cagr_5yr" in result
    assert "revenue_cagr_5yr_flag" in result

    assert "revenue_cagr_10yr" in result
    assert "revenue_cagr_10yr_flag" in result

    assert "pat_cagr_3yr" in result
    assert "pat_cagr_3yr_flag" in result

    assert "pat_cagr_5yr" in result
    assert "pat_cagr_5yr_flag" in result

    assert "pat_cagr_10yr" in result
    assert "pat_cagr_10yr_flag" in result

    assert "eps_cagr_3yr" in result
    assert "eps_cagr_3yr_flag" in result

    assert "eps_cagr_5yr" in result
    assert "eps_cagr_5yr_flag" in result

    assert "eps_cagr_10yr" in result
    assert "eps_cagr_10yr_flag" in result
