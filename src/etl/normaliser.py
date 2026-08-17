import re
import pandas as pd


def normalize_year(value):
    """
    Convert different year formats into a consistent value.

    Examples:
        Dec 2012 -> 2012
        Mar-2014 -> 2014
        2019 -> 2019
        2020.0 -> 2020
    """

    if pd.isna(value):
        return None

    text = str(value).strip()

    if not text:
        return None

    # Handle values such as 2019.0
    if re.match(r"^\d{4}\.0$", text):
        return int(float(text))

    # Find a four-digit year anywhere in the value
    match = re.search(r"(19|20)\d{2}", text)

    if match:
        return int(match.group(0))

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