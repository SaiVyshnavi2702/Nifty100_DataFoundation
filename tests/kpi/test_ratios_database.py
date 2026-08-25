from src.analytics.ratios_data import get_ratio_data_by_year
from src.analytics.ratios_service import calculate_company_ratios


def test_get_ratio_data_by_year():
    data = get_ratio_data_by_year("ABB")

    assert "sales" in data
    assert "operating_profit" in data
    assert "other_income" in data
    assert "interest" in data
    assert "net_profit" in data

    assert "equity_capital" in data
    assert "reserves" in data
    assert "borrowings" in data
    assert "investments" in data
    assert "total_assets" in data

    assert 2019 in data["sales"]
    assert 2024 in data["sales"]

    assert 2019 in data["net_profit"]
    assert 2024 in data["net_profit"]


def test_ttm_is_excluded():
    data = get_ratio_data_by_year("ABB")

    assert "TTM" not in data["sales"]
    assert "TTM" not in data["net_profit"]
    assert "TTM" not in data["borrowings"]


def test_ratio_data_contains_balance_sheet_values():
    data = get_ratio_data_by_year("ABB")

    assert 2024 in data["equity_capital"]
    assert 2024 in data["reserves"]
    assert 2024 in data["borrowings"]
    assert 2024 in data["total_assets"]


def test_ratio_data_contains_sector():
    data = get_ratio_data_by_year("ABB")

    assert 2024 in data["broad_sector"]


def test_calculate_company_ratios():
    result = calculate_company_ratios("ABB", 2024)

    assert result["company_id"] == "ABB"
    assert result["year"] == 2024
    assert result["status"] == "OK"

    assert result["net_profit_margin"] is not None
    assert result["operating_profit_margin"] is not None
    assert result["return_on_equity"] is not None
    assert result["return_on_capital_employed"] is not None
    assert result["return_on_assets"] is not None

    assert result["debt_to_equity"] is not None
    assert result["interest_coverage"] is not None
    assert result["asset_turnover"] is not None
    assert result["net_debt"] is not None


def test_calculate_company_ratios_actual_values():
    result = calculate_company_ratios("ABB", 2024)

    assert round(result["net_profit_margin"], 2) == 20.53
    assert round(result["operating_profit_margin"], 2) == 24.84


def test_company_ratios_insufficient_year():
    result = calculate_company_ratios("ABB", 2030)

    assert result["status"] == "INSUFFICIENT"
