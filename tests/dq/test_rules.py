import pandas as pd

from src.etl import validator


def reset_failures():
    validator.failures = []


def get_failures():
    return validator.failures


def test_dq01_required_column_missing():
    reset_failures()

    df = pd.DataFrame(
        {
            "id": [1],
            "company_id": ["TCS"],
        }
    )

    validator.check_required_columns("balancesheet", df)

    failures = get_failures()

    assert len(failures) > 0

    assert all(failure["rule_id"] == "DQ-01" for failure in failures)

    assert all(failure["severity"] == "CRITICAL" for failure in failures)


def test_dq02_primary_key_null():
    reset_failures()

    df = pd.DataFrame(
        {
            "id": [None],
            "company_id": ["TCS"],
            "year": [2024],
        }
    )

    validator.dq02_primary_key_null("balancesheet", df)

    failures = get_failures()

    assert len(failures) == 1
    assert failures[0]["rule_id"] == "DQ-02"
    assert failures[0]["severity"] == "CRITICAL"


def test_dq03_primary_key_duplicate():
    reset_failures()

    df = pd.DataFrame(
        {
            "id": [1, 1],
            "company_id": ["TCS", "INFY"],
            "year": [2024, 2024],
        }
    )

    validator.dq03_primary_key_duplicate("balancesheet", df)

    failures = get_failures()

    assert len(failures) == 2

    assert all(failure["rule_id"] == "DQ-03" for failure in failures)

    assert all(failure["severity"] == "CRITICAL" for failure in failures)


def test_dq04_company_id_null():
    reset_failures()

    df = pd.DataFrame(
        {
            "id": [1],
            "company_id": [None],
            "year": [2024],
        }
    )

    validator.dq04_company_id_null("balancesheet", df)

    failures = get_failures()

    assert len(failures) == 1
    assert failures[0]["rule_id"] == "DQ-04"
    assert failures[0]["severity"] == "CRITICAL"


def test_dq05_invalid_company_foreign_key():
    reset_failures()

    companies = pd.DataFrame(
        {
            "id": ["TCS", "INFY"],
        }
    )

    balancesheet = pd.DataFrame(
        {
            "id": [1],
            "company_id": ["INVALID"],
            "year": [2024],
        }
    )

    all_data = {
        "companies": companies,
        "balancesheet": balancesheet,
    }

    validator.dq05_invalid_company_fk(all_data)

    failures = get_failures()

    assert len(failures) == 1
    assert failures[0]["rule_id"] == "DQ-05"
    assert failures[0]["severity"] == "CRITICAL"


def test_dq06_invalid_year():
    reset_failures()

    df = pd.DataFrame(
        {
            "id": [1],
            "company_id": ["TCS"],
            "year": ["INVALID_YEAR"],
        }
    )

    validator.dq06_invalid_year("balancesheet", df)

    failures = get_failures()

    assert len(failures) == 1
    assert failures[0]["rule_id"] == "DQ-06"
    assert failures[0]["severity"] == "CRITICAL"


def test_dq07_duplicate_company_year():
    reset_failures()

    df = pd.DataFrame(
        {
            "id": [1, 2],
            "company_id": ["TCS", "TCS"],
            "year": [2024, 2024],
        }
    )

    validator.dq07_duplicate_company_year("balancesheet", df)

    failures = get_failures()

    assert len(failures) == 2

    assert all(failure["rule_id"] == "DQ-07" for failure in failures)

    assert all(failure["severity"] == "CRITICAL" for failure in failures)


def test_dq08_invalid_numeric_value():
    reset_failures()

    df = pd.DataFrame(
        {
            "id": [1],
            "company_id": ["TCS"],
            "year": [2024],
            "sales": ["NOT_A_NUMBER"],
        }
    )

    validator.dq08_numeric_values("profitandloss", df)

    failures = get_failures()

    assert len(failures) == 1
    assert failures[0]["rule_id"] == "DQ-08"
    assert failures[0]["severity"] == "CRITICAL"


def test_dq09_sales_check_is_informational_only():
    reset_failures()

    df = pd.DataFrame(
        {
            "id": [1],
            "company_id": ["TCS"],
            "year": [2024],
            "sales": [-100],
        }
    )

    validator.dq09_sales_check("profitandloss", df)

    failures = get_failures()

    assert failures == []


def test_dq10_opm_check_is_disabled():
    reset_failures()

    df = pd.DataFrame(
        {
            "id": [1],
            "company_id": ["TCS"],
            "year": [2024],
            "sales": [1000],
            "operating_profit": [200],
            "opm_percentage": [99],
        }
    )

    validator.dq10_opm_check("profitandloss", df)

    failures = get_failures()

    assert failures == []


def test_dq11_pbt_check_is_disabled():
    reset_failures()

    df = pd.DataFrame(
        {
            "id": [1],
            "company_id": ["TCS"],
            "year": [2024],
            "profit_before_tax": [9999],
        }
    )

    validator.dq11_pbt_check("profitandloss", df)

    failures = get_failures()

    assert failures == []


def test_dq12_net_profit_check_is_disabled():
    reset_failures()

    df = pd.DataFrame(
        {
            "id": [1],
            "company_id": ["TCS"],
            "year": [2024],
            "profit_before_tax": [200],
            "tax_percentage": [25],
            "net_profit": [999],
        }
    )

    validator.dq12_net_profit_check("profitandloss", df)

    failures = get_failures()

    assert failures == []


def test_dq13_balance_sheet_check_is_disabled():
    reset_failures()

    df = pd.DataFrame(
        {
            "id": [1],
            "company_id": ["TCS"],
            "year": [2024],
            "total_assets": [1000],
            "total_liabilities": [100],
        }
    )

    validator.dq13_balance_sheet_check("balancesheet", df)

    failures = get_failures()

    assert failures == []


def test_dq14_cashflow_check_is_disabled():
    reset_failures()

    df = pd.DataFrame(
        {
            "id": [1],
            "company_id": ["TCS"],
            "year": [2024],
            "operating_activity": [100],
            "investing_activity": [-50],
            "financing_activity": [-20],
            "net_cash_flow": [999],
        }
    )

    validator.dq14_cashflow_check("cashflow", df)

    failures = get_failures()

    assert failures == []
