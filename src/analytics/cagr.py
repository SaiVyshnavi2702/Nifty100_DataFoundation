CAGR_YEARS = [3, 5, 10]


def calculate_cagr(start_value, end_value, years):
    """Calculate CAGR and return (value, flag)."""

    if start_value is None or end_value is None:
        return None, "INSUFFICIENT"

    if years is None or years <= 0:
        return None, "INSUFFICIENT"

    if start_value == 0:
        return None, "ZERO_BASE"

    if start_value > 0 and end_value > 0:
        cagr = ((end_value / start_value) ** (1.0 / years) - 1) * 100
        return cagr, None

    if start_value > 0 and end_value < 0:
        return None, "DECLINE_TO_LOSS"

    if start_value < 0 and end_value > 0:
        return None, "TURNAROUND"

    if start_value < 0 and end_value < 0:
        return None, "BOTH_NEGATIVE"

    return None, "INSUFFICIENT"


def calculate_period_cagr(values_by_year, end_year, years):
    """Calculate CAGR for a specific number of years."""

    start_year = end_year - years

    if start_year not in values_by_year:
        return None, "INSUFFICIENT"

    if end_year not in values_by_year:
        return None, "INSUFFICIENT"

    start_value = values_by_year[start_year]
    end_value = values_by_year[end_year]

    return calculate_cagr(start_value, end_value, years)


def calculate_all_cagrs(values_by_year, end_year):
    """Calculate 3-year, 5-year and 10-year CAGR."""

    result = {}

    for years in CAGR_YEARS:
        value, flag = calculate_period_cagr(
            values_by_year,
            end_year,
            years
        )

        result[f"cagr_{years}yr"] = value
        result[f"cagr_{years}yr_flag"] = flag

    return result

def calculate_financial_cagrs(
    revenue_by_year,
    pat_by_year,
    eps_by_year,
    end_year,
):
    """Calculate Revenue, PAT and EPS CAGR for 3, 5 and 10 years."""

    result = {}

    revenue_cagrs = calculate_all_cagrs(
        revenue_by_year,
        end_year,
    )

    pat_cagrs = calculate_all_cagrs(
        pat_by_year,
        end_year,
    )

    eps_cagrs = calculate_all_cagrs(
        eps_by_year,
        end_year,
    )

    for years in CAGR_YEARS:
        result[f"revenue_cagr_{years}yr"] = (
            revenue_cagrs[f"cagr_{years}yr"]
        )

        result[f"revenue_cagr_{years}yr_flag"] = (
            revenue_cagrs[f"cagr_{years}yr_flag"]
        )

        result[f"pat_cagr_{years}yr"] = (
            pat_cagrs[f"cagr_{years}yr"]
        )

        result[f"pat_cagr_{years}yr_flag"] = (
            pat_cagrs[f"cagr_{years}yr_flag"]
        )

        result[f"eps_cagr_{years}yr"] = (
            eps_cagrs[f"cagr_{years}yr"]
        )

        result[f"eps_cagr_{years}yr_flag"] = (
            eps_cagrs[f"cagr_{years}yr_flag"]
        )

    return result
