def calculate_composite_quality_score(
    revenue_cagr_5yr,
    pat_cagr_5yr,
    eps_cagr_5yr,
):
    """
    Calculate the company's composite quality score
    using its 5-year revenue, profit, and EPS growth.
    """

    # A score cannot be calculated if any of the
    # required CAGR values are missing.
    if (
        revenue_cagr_5yr is None
        or pat_cagr_5yr is None
        or eps_cagr_5yr is None
    ):
        return None

    # Give higher importance to profit growth.
    score = (
        revenue_cagr_5yr * 0.30
        + pat_cagr_5yr * 0.40
        + eps_cagr_5yr * 0.30
    )

    return round(score, 2)