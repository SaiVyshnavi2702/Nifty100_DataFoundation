import sqlite3

from src.analytics.cagr_service import calculate_company_cagrs
from src.analytics.quality_score import (
    calculate_composite_quality_score,
)


DB_PATH = "data/nifty100.db"


def update_quality_scores(
    db_path=DB_PATH,
):
    """
    Calculate and store 5-year CAGR metrics
    and composite quality score for every
    company/year available in the database.
    """

    connection = sqlite3.connect(db_path)

    companies = connection.execute(
        """
        SELECT DISTINCT company_id
        FROM profitandloss
        WHERE typeof(year) = 'integer'
        ORDER BY company_id
        """
    ).fetchall()

    updated_rows = 0
    insufficient_rows = 0

    for (company_id,) in companies:

        years = connection.execute(
            """
            SELECT DISTINCT year
            FROM profitandloss
            WHERE company_id = ?
              AND typeof(year) = 'integer'
            ORDER BY year
            """,
            (company_id,),
        ).fetchall()

        for (year,) in years:

            cagrs = calculate_company_cagrs(
                company_id,
                year,
                db_path=db_path,
            )

            revenue_cagr_5yr = cagrs["revenue"].get(
                "cagr_5yr"
            )

            pat_cagr_5yr = cagrs["pat"].get(
                "cagr_5yr"
            )

            eps_cagr_5yr = cagrs["eps"].get(
                "cagr_5yr"
            )

            composite_score = (
                calculate_composite_quality_score(
                    revenue_cagr_5yr,
                    pat_cagr_5yr,
                    eps_cagr_5yr,
                )
            )

            if composite_score is None:
                insufficient_rows += 1
            else:
                updated_rows += 1

            connection.execute(
                """
                UPDATE financial_ratios
                SET
                    revenue_cagr_5yr = ?,
                    pat_cagr_5yr = ?,
                    eps_cagr_5yr = ?,
                    composite_quality_score = ?
                WHERE company_id = ?
                  AND year = ?
                """,
                (
                    revenue_cagr_5yr,
                    pat_cagr_5yr,
                    eps_cagr_5yr,
                    composite_score,
                    company_id,
                    year,
                ),
            )

    connection.commit()
    connection.close()

    print(
        "Quality-score update completed."
    )

    print(
        "Rows with calculated score:",
        updated_rows,
    )

    print(
        "Rows with insufficient data:",
        insufficient_rows,
    )


if __name__ == "__main__":
    update_quality_scores()