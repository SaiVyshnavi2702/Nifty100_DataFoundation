import pandas as pd

from src.etl import validator


def reset_failures():
    validator.failures = []


def rule_ids():
    return [
        failure["rule_id"]
        for failure in validator.failures
    ]


def test_dq01_required_columns():
    reset_failures()

    df = pd.DataFrame({
        "id": [1],
        "company_id": ["TCS"],
    })

    validator.check_required_columns(
        "balancesheet",
        df
    )

    assert "DQ-01" in rule_ids()


def test_dq02_primary_key_null():
    reset_failures()

    df = pd.DataFrame({
        "id": [None],
        "company_id": ["TCS"],
        "year": [2024],
    })

    validator.dq02_primary_key_null(
        "balancesheet",
        df
    )

    assert "DQ-02" in rule_ids()


def test_dq03_primary_key_duplicate():
    reset_failures()

    df = pd.DataFrame({
        "id": [1, 1],
        "company_id": ["TCS", "INFY"],
        "year": [2024, 2024],
    })

    validator.dq03_primary_key_duplicate(
        "balancesheet",
        df
    )

    assert "DQ-03" in rule_ids()


def test_dq04_company_id_null():
    reset_failures()

    df = pd.DataFrame({
        "id": [1],
        "company_id": [None],
        "year": [2024],
    })

    validator.dq04_company_id_null(
        "balancesheet",
        df
    )

    assert "DQ-04" in rule_ids()


def test_dq05_invalid_company_fk():
    reset_failures()

    companies = pd.DataFrame({
        "id": ["TCS", "INFY"],
    })

    balancesheet = pd.DataFrame({
        "id": [1],
        "company_id": ["INVALID"],
        "year": [2024],
    })

    all_data = {
        "companies": companies,
        "balancesheet": balancesheet,
    }

    validator.dq05_invalid_company_fk(
        all_data
    )

    assert "DQ-05" in rule_ids()


def test_dq06_invalid_year():
    reset_failures()

    df = pd.DataFrame({
        "id": [1],
        "company_id": ["TCS"],
        "year": ["INVALID_YEAR"],
    })

    validator.dq06_invalid_year(
        "balancesheet",
        df
    )

    assert "DQ-06" in rule_ids()


def test_dq07_duplicate_company_year():
    reset_failures()

    df = pd.DataFrame({
        "id": [1, 2],
        "company_id": ["TCS", "TCS"],
        "year": [2024, 2024],
    })

    validator.dq07_duplicate_company_year(
        "balancesheet",
        df
    )

    assert "DQ-07" in rule_ids()


def test_dq08_numeric_values():
    reset_failures()

    df = pd.DataFrame({
        "id": [1],
        "company_id": ["TCS"],
        "year": [2024],
        "sales": ["NOT_A_NUMBER"],
    })

    validator.dq08_numeric_values(
        "profitandloss",
        df
    )

    assert "DQ-08" in rule_ids()


def test_dq09_sales_check():
    reset_failures()

    df = pd.DataFrame({
        "id": [1],
        "company_id": ["TCS"],
        "year": [2024],
        "sales": [-100],
    })

    validator.dq09_sales_check(
        "profitandloss",
        df
    )

    assert "DQ-09" not in rule_ids()


def test_dq10_opm_check():
    reset_failures()

    df = pd.DataFrame({
        "id": [1],
        "company_id": ["TCS"],
        "year": [2024],
        "sales": [1000],
        "operating_profit": [200],
        "opm_percentage": [20],
    })

    validator.dq10_opm_check(
        "profitandloss",
        df
    )

    assert "DQ-10" not in rule_ids()


def test_dq11_pbt_check():
    reset_failures()

    df = pd.DataFrame({
        "id": [1],
        "company_id": ["TCS"],
        "year": [2024],
        "profit_before_tax": [200],
    })

    validator.dq11_pbt_check(
        "profitandloss",
        df
    )

    assert "DQ-11" not in rule_ids()


def test_dq12_net_profit_check():
    reset_failures()

    df = pd.DataFrame({
        "id": [1],
        "company_id": ["TCS"],
        "year": [2024],
        "profit_before_tax": [200],
        "tax_percentage": [25],
        "net_profit": [150],
    })

    validator.dq12_net_profit_check(
        "profitandloss",
        df
    )

    assert "DQ-12" not in rule_ids()


def test_dq13_balance_sheet_check():
    reset_failures()

    df = pd.DataFrame({
        "id": [1],
        "company_id": ["TCS"],
        "year": [2024],
        "total_assets": [1000],
        "total_liabilities": [900],
    })

    validator.dq13_balance_sheet_check(
        "balancesheet",
        df
    )

    assert "DQ-13" not in rule_ids()


def test_dq14_cashflow_check():
    reset_failures()

    df = pd.DataFrame({
        "id": [1],
        "company_id": ["TCS"],
        "year": [2024],
        "operating_activity": [100],
        "investing_activity": [-50],
        "financing_activity": [-20],
        "net_cash_flow": [30],
    })

    validator.dq14_cashflow_check(
        "cashflow",
        df
    )

    assert "DQ-14" not in rule_ids()