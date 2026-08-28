import sqlite3


DB_PATH = "data/nifty100.db"


# Day 14 screening thresholds
MIN_ROE = 15.0
MAX_DEBT_TO_EQUITY = 1.0
MIN_INTEREST_COVERAGE = 3.0

MIN_REVENUE_CAGR_5YR = 10.0
MIN_PAT_CAGR_5YR = 10.0
MIN_EPS_CAGR_5YR = 10.0


def screen_company(row):
    """
    Screen one company using the Day 14 fundamental criteria.

    Returns:
        PASS
        FAIL
        INSUFFICIENT_DATA
    """

    required_fields = [
        "return_on_equity_pct",
        "debt_to_equity",
        "interest_coverage",
        "revenue_cagr_5yr",
        "pat_cagr_5yr",
        "eps_cagr_5yr",
    ]

    for field in required_fields:
        if row[field] is None:
            return "INSUFFICIENT_DATA"

    if row["return_on_equity_pct"] < MIN_ROE:
        return "FAIL"

    if row["debt_to_equity"] > MAX_DEBT_TO_EQUITY:
        return "FAIL"

    if row["interest_coverage"] < MIN_INTEREST_COVERAGE:
        return "FAIL"

    if row["revenue_cagr_5yr"] < MIN_REVENUE_CAGR_5YR:
        return "FAIL"

    if row["pat_cagr_5yr"] < MIN_PAT_CAGR_5YR:
        return "FAIL"

    if row["eps_cagr_5yr"] < MIN_EPS_CAGR_5YR:
        return "FAIL"

    return "PASS"


def get_latest_annual_rows(connection):
    """
    Get the latest March annual row for every company.
    """

    query = """
        SELECT
            f.company_id,
            f.year,
            f.period,
            f.return_on_equity_pct,
            f.debt_to_equity,
            f.interest_coverage,
            f.revenue_cagr_5yr,
            f.pat_cagr_5yr,
            f.eps_cagr_5yr,
            f.composite_quality_score
        FROM financial_ratios f
        INNER JOIN (
            SELECT
                company_id,
                MAX(year) AS latest_year
            FROM financial_ratios
            WHERE period LIKE 'Mar %'
            GROUP BY company_id
        ) latest
            ON f.company_id = latest.company_id
            AND f.year = latest.latest_year
        WHERE f.period LIKE 'Mar %'
        ORDER BY f.company_id
    """

    connection.row_factory = sqlite3.Row

    return connection.execute(query).fetchall()


def screen_latest_companies(db_path=DB_PATH):
    """
    Screen the latest annual data for every company.
    """

    connection = sqlite3.connect(db_path)

    rows = get_latest_annual_rows(connection)

    results = []

    for row in rows:
        result = screen_company(row)

        results.append(
            {
                "company_id": row["company_id"],
                "year": row["year"],
                "period": row["period"],
                "status": result,
                "return_on_equity_pct":
                    row["return_on_equity_pct"],
                "debt_to_equity":
                    row["debt_to_equity"],
                "interest_coverage":
                    row["interest_coverage"],
                "revenue_cagr_5yr":
                    row["revenue_cagr_5yr"],
                "pat_cagr_5yr":
                    row["pat_cagr_5yr"],
                "eps_cagr_5yr":
                    row["eps_cagr_5yr"],
                "composite_quality_score":
                    row["composite_quality_score"],
            }
        )

    connection.close()

    return results


def print_screening_results(results):
    """
    Print a readable Day 14 screening report.
    """

    passed = [
        row for row in results
        if row["status"] == "PASS"
    ]

    failed = [
        row for row in results
        if row["status"] == "FAIL"
    ]

    insufficient = [
        row for row in results
        if row["status"] == "INSUFFICIENT_DATA"
    ]

    print()
    print("=" * 70)
    print("DAY 14 - FUNDAMENTAL SCREENING")
    print("=" * 70)

    print()
    print("Total companies:", len(results))
    print("PASS:", len(passed))
    print("FAIL:", len(failed))
    print("INSUFFICIENT DATA:", len(insufficient))

    print()
    print("-" * 70)
    print("PASSING COMPANIES")
    print("-" * 70)

    for row in passed:
        print(
            f"{row['company_id']:15} "
            f"Score: {row['composite_quality_score']}"
        )

    print()
    print("-" * 70)
    print("INSUFFICIENT DATA")
    print("-" * 70)

    for row in insufficient:
        print(row["company_id"])

    print()
    print("-" * 70)
    print("FAILED COMPANIES")
    print("-" * 70)

    for row in failed:
        print(row["company_id"])

    print()


if __name__ == "__main__":
    results = screen_latest_companies()

    print_screening_results(results)
