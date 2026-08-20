import re
import pandas as pd


def normalize_year(value):
    """
    Convert a financial reporting period into its calendar year.

    Examples:
        Dec 2012  -> 2012
        Mar 2014  -> 2014
        Mar-2014  -> 2014
        Mar-14    -> 2014
        Sep 2024  -> 2024
        2024      -> 2024
        2024.5    -> 2024
        TTM       -> TTM
    """

    if value is None or pd.isna(value):
        return None

    text = str(value).strip()

    if not text:
        return None

    if text.upper() == "TTM":
        return "TTM"

    # Look for a four-digit year first.
    match = re.search(r"(\d{4})", text)

    if match:
        return int(match.group(1))

    # Handle two-digit years such as Mar-14.
    match = re.search(r"(\d{2})$", text)

    if match:
        year = int(match.group(1))

        if year >= 50:
            return 1900 + year

        return 2000 + year

    # Handle integer-like values.
    if text.isdigit():
        return int(text)

    return None


def normalize_period(value):
    """
    Preserve the actual reporting period.

    This is important because:
        Mar 2024
        Sep 2024

    are both year 2024 but are different reporting periods.

    Examples:
        Dec 2012  -> "Dec 2012"
        Mar 2014  -> "Mar 2014"
        Mar-2014  -> "Mar 2014"
        Sep 2024  -> "Sep 2024"
        2024      -> "2024"
        2024.5    -> "2024.5"
        TTM       -> "TTM"
    """

    if value is None or pd.isna(value):
        return None

    text = str(value).strip()

    if not text:
        return None

    # Normalize separators.
    text = re.sub(r"\s*-\s*", " ", text)

    # Normalize multiple spaces.
    text = re.sub(r"\s+", " ", text)

    # Standardize month names.
    month_map = {
        "JAN": "Jan",
        "FEB": "Feb",
        "MAR": "Mar",
        "APR": "Apr",
        "MAY": "May",
        "JUN": "Jun",
        "JUL": "Jul",
        "AUG": "Aug",
        "SEP": "Sep",
        "OCT": "Oct",
        "NOV": "Nov",
        "DEC": "Dec",
    }

    parts = text.split()

    # Handle values such as:
    # Mar 2024
    # Sep 2024
    if len(parts) == 2:
        month = month_map.get(parts[0].upper())
        year = parts[1]

        if month and re.fullmatch(r"\d{4}", year):
            return f"{month} {year}"

    return text


def normalize_ticker(value):
    """
    Normalize company/ticker identifiers.

    Examples:
        ' abb '    -> 'ABB'
        'HDFCBANK' -> 'HDFCBANK'
        'tcs'      -> 'TCS'
        'TATA MOTORS' -> 'TATAMOTORS'
    """

    if value is None or pd.isna(value):
        return None

    text = str(value).strip()

    if not text:
        return None

    text = text.upper()

    # Remove unnecessary whitespace.
    text = re.sub(r"\s+", "", text)

    return text


def normalize_column_name(value):
    """
    Convert column names into lowercase snake_case.

    Examples:
        "Company ID"      -> "company_id"
        "Operating Profit" -> "operating_profit"
        "P&L"             -> "p_and_l"
    """

    if value is None or pd.isna(value):
        return ""

    text = str(value).strip().lower()

    text = text.replace("&", "and")

    text = re.sub(r"[^a-z0-9]+", "_", text)

    text = re.sub(r"_+", "_", text)

    return text.strip("_")
