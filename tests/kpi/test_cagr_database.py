from src.analytics.cagr_data import get_financial_data_by_year
from src.analytics.cagr_service import calculate_company_cagrs


def test_get_financial_data_by_year():
    data = get_financial_data_by_year("ABB")

    assert "revenue" in data
    assert "pat" in data
    assert "eps" in data

    assert 2019 in data["revenue"]
    assert 2021 in data["revenue"]
    assert 2024 in data["revenue"]

    assert 2019 in data["pat"]
    assert 2021 in data["pat"]
    assert 2024 in data["pat"]

    assert 2019 in data["eps"]
    assert 2021 in data["eps"]
    assert 2024 in data["eps"]


def test_ttm_is_excluded():
    data = get_financial_data_by_year("ABB")

    assert "TTM" not in data["revenue"]
    assert "TTM" not in data["pat"]
    assert "TTM" not in data["eps"]

def test_calculate_company_cagrs():
    result = calculate_company_cagrs("ABB", 2024)

    assert "revenue" in result
    assert "pat" in result
    assert "eps" in result

    assert "cagr_3yr" in result["revenue"]
    assert "cagr_5yr" in result["revenue"]
    assert "cagr_10yr" in result["revenue"]

    assert "cagr_3yr" in result["pat"]
    assert "cagr_5yr" in result["pat"]
    assert "cagr_10yr" in result["pat"]

    assert "cagr_3yr" in result["eps"]
    assert "cagr_5yr" in result["eps"]
    assert "cagr_10yr" in result["eps"]


def test_calculate_company_cagrs_values():
    result = calculate_company_cagrs("ABB", 2024)

    assert result["revenue"]["cagr_10yr"] is not None
    assert result["pat"]["cagr_10yr"] is not None
    assert result["eps"]["cagr_10yr"] is not None

def test_calculate_company_cagrs_actual_values():
    result = calculate_company_cagrs("ABB", 2024)

    assert round(result["revenue"]["cagr_3yr"], 2) == 10.71
    assert round(result["revenue"]["cagr_5yr"], 2) == 9.72
    assert round(result["revenue"]["cagr_10yr"], 2) == 9.90

    assert round(result["pat"]["cagr_3yr"], 2) == 20.23
    assert round(result["pat"]["cagr_5yr"], 2) == 21.69
    assert round(result["pat"]["cagr_10yr"], 2) == 19.75

    assert round(result["eps"]["cagr_3yr"], 2) == 20.24
    assert round(result["eps"]["cagr_5yr"], 2) == 21.66
    assert round(result["eps"]["cagr_10yr"], 2) == 19.77

def test_company_cagr_insufficient_history():
    result = calculate_company_cagrs("ADANIGREEN", 2024)

    assert result["revenue"]["cagr_10yr"] is None
    assert result["revenue"]["cagr_10yr_flag"] == "INSUFFICIENT"

    assert result["pat"]["cagr_10yr"] is None
    assert result["pat"]["cagr_10yr_flag"] == "INSUFFICIENT"

    assert result["eps"]["cagr_10yr"] is None
    assert result["eps"]["cagr_10yr_flag"] == "INSUFFICIENT"
