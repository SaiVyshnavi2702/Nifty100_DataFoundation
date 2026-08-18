import re
import pandas as pd


def normalize_year(value):
    """
    Convert financial period values into a consistent form.

    Examples:
        Dec 2012 -> 2012
        Mar-2014 -> 2014
        Mar-14 -> 2014
        2020 -> 2020
        TTM -> TTM
    """

    if value is None or pd.isna(value):
        return None

    value = str(value).strip()

    if not value:
        return None

    if value.upper() == "TTM":
        return "TTM"

    match = re.search(r"(\d{4})", value)

    if match:
        return int(match.group(1))

    match = re.search(r"(\d{2})$", value)

    if match:
        year = int(match.group(1))

        if year >= 50:
            return 1900 + year

        return 2000 + year

    if value.isdigit():
        return int(value)

    return None

def normalize_ticker(value):
    """
    Normalize company/ticker identifiers.

    Examples:
        ' abb ' -> 'ABB'
        'HDFCBANK' -> 'HDFCBANK'
        'tcs' -> 'TCS'
    """

    if pd.isna(value):
        return None

    text = str(value).strip()

    if not text:
        return None

    text = text.upper()

    # Remove unnecessary spaces inside the ticker
    text = re.sub(r"\s+", "", text)

    return text


def normalize_column_name(value):
    """
    Convert column names into lowercase snake_case.
    """

    if pd.isna(value):
        return ""

    text = str(value).strip().lower()

    text = text.replace("&", "and")
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = re.sub(r"_+", "_", text)

    return text.strip("_")