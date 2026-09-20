from src.etl.normaliser import normalize_year


def test_normalize_dec_2012():
    assert normalize_year("Dec 2012") == 2012


def test_normalize_mar_2014():
    assert normalize_year("Mar 2014") == 2014


def test_normalize_mar_dash_2014():
    assert normalize_year("Mar-2014") == 2014


def test_normalize_mar_dash_14():
    assert normalize_year("Mar-14") == 2014


def test_normalize_sep_2024():
    assert normalize_year("Sep 2024") == 2024


def test_normalize_integer_string():
    assert normalize_year("2024") == 2024


def test_normalize_decimal_string():
    assert normalize_year("2024.5") == 2024


def test_normalize_integer():
    assert normalize_year(2024) == 2024


def test_normalize_float():
    assert normalize_year(2024.5) == 2024


def test_normalize_ttm():
    assert normalize_year("TTM") == "TTM"


def test_normalize_ttm_lowercase():
    assert normalize_year("ttm") == "TTM"


def test_normalize_ttm_with_spaces():
    assert normalize_year("  TTM  ") == "TTM"


def test_normalize_none():
    assert normalize_year(None) is None


def test_normalize_nan():
    assert normalize_year(float("nan")) is None


def test_normalize_empty_string():
    assert normalize_year("") is None


def test_normalize_whitespace():
    assert normalize_year("   ") is None


def test_normalize_two_digit_year_49():
    assert normalize_year("Mar-49") == 2049


def test_normalize_two_digit_year_50():
    assert normalize_year("Mar-50") == 1950


def test_normalize_text_without_year():
    assert normalize_year("Unknown") is None


def test_normalize_year_inside_text():
    assert normalize_year("FY 2024 Annual") == 2024
