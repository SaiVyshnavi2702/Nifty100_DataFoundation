from src.etl.normaliser import (
    normalize_year,
    normalize_ticker
)



# normalize_year tests

def test_normalize_year_dec_2012():
    assert normalize_year("Dec 2012") == 2012


def test_normalize_year_mar_2014():
    assert normalize_year("Mar 2014") == 2014


def test_normalize_year_mar_dash_2015():
    assert normalize_year("Mar-2015") == 2015


def test_normalize_year_apr_2016():
    assert normalize_year("Apr 2016") == 2016


def test_normalize_year_2017_string():
    assert normalize_year("2017") == 2017


def test_normalize_year_2018_integer():
    assert normalize_year(2018) == 2018


def test_normalize_year_2019_float():
    assert normalize_year(2019.0) == 2019


def test_normalize_year_2020_string():
    assert normalize_year("2020") == 2020


def test_normalize_year_dec_2021():
    assert normalize_year("Dec 2021") == 2021


def test_normalize_year_mar_2022():
    assert normalize_year("Mar-2022") == 2022


def test_normalize_year_apr_2023():
    assert normalize_year("Apr 2023") == 2023


def test_normalize_year_dec_2024():
    assert normalize_year("Dec 2024") == 2024


def test_normalize_year_whitespace():
    assert normalize_year(" 2020 ") == 2020


def test_normalize_year_month_whitespace():
    assert normalize_year(" Mar 2021 ") == 2021


def test_normalize_year_lowercase_month():
    assert normalize_year("mar 2022") == 2022


def test_normalize_year_uppercase_month():
    assert normalize_year("MAR 2023") == 2023


def test_normalize_year_nan():
    assert normalize_year(float("nan")) is None


def test_normalize_year_none():
    assert normalize_year(None) is None


def test_normalize_year_empty_string():
    assert normalize_year("") is None


def test_normalize_year_invalid_text():
    assert normalize_year("unknown") is None



# normalize_ticker tests


def test_normalize_ticker_lowercase():
    assert normalize_ticker("abb") == "ABB"


def test_normalize_ticker_uppercase():
    assert normalize_ticker("TCS") == "TCS"


def test_normalize_ticker_mixed_case():
    assert normalize_ticker("TcS") == "TCS"


def test_normalize_ticker_leading_space():
    assert normalize_ticker(" TCS") == "TCS"


def test_normalize_ticker_trailing_space():
    assert normalize_ticker("TCS ") == "TCS"


def test_normalize_ticker_both_spaces():
    assert normalize_ticker(" TCS ") == "TCS"


def test_normalize_ticker_internal_spaces():
    assert normalize_ticker("HDFC BANK") == "HDFCBANK"


def test_normalize_ticker_multiple_spaces():
    assert normalize_ticker(" HDFC   BANK ") == "HDFCBANK"


def test_normalize_ticker_hdfcbank():
    assert normalize_ticker("hdfcbank") == "HDFCBANK"


def test_normalize_ticker_reliance():
    assert normalize_ticker("reliance") == "RELIANCE"


def test_normalize_ticker_infY():
    assert normalize_ticker("infy") == "INFY"


def test_normalize_ticker_sbilife():
    assert normalize_ticker("sbilife") == "SBILIFE"


def test_normalize_ticker_adani():
    assert normalize_ticker("adanient") == "ADANIENT"


def test_normalize_ticker_none():
    assert normalize_ticker(None) is None


def test_normalize_ticker_nan():
    assert normalize_ticker(float("nan")) is None


def test_normalize_ticker_empty():
    assert normalize_ticker("") is None


def test_normalize_ticker_whitespace_only():
    assert normalize_ticker("   ") is None


def test_normalize_ticker_numeric():
    assert normalize_ticker(123) == "123"