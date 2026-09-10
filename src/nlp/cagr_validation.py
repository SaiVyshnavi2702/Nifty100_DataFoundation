import pandas as pd

from src.analytics.cagr_service import calculate_company_cagrs


# This is the CSV file created by parser.py
PARSED_FILE = "output/analysis_parsed.csv"

# This file will contain CAGR differences
# that need to be checked manually
REVIEW_FILE = "output/cagr_divergence_review.csv"


# Match the names used in analysis.xlsx
# with the names used by the CAGR engine
METRIC_MAPPING = {
    "compounded_sales_growth": "revenue",
    "compounded_profit_growth": "pat",
}


def main():

    # Read the parsed analysis data
    parsed_df = pd.read_csv(PARSED_FILE)

    # Store records that need manual review
    review_rows = []

    # The CAGR engine calculates
    # 3-year, 5-year and 10-year CAGRs
    valid_periods = [3, 5, 10]

    # Go through every row in the parsed CSV
    for _, row in parsed_df.iterrows():

        company_id = row["company_id"]
        metric_type = row["metric_type"]
        period_years = row["period_years"]
        parsed_value = row["value_pct"]

        # We only need to compare
        # sales growth and profit growth
        if metric_type not in METRIC_MAPPING:
            continue

        # TTM does not have a year period,
        # so it cannot be compared with the CAGR engine
        if pd.isna(period_years):
            continue

        period_years = int(period_years)

        # Only compare 3-year, 5-year and 10-year values
        if period_years not in valid_periods:
            continue

        # Calculate the CAGR using our existing CAGR engine
        cagrs = calculate_company_cagrs(
            company_id,
            2024,
        )

        # Find the matching metric
        engine_metric = METRIC_MAPPING[metric_type]

        engine_result = cagrs[engine_metric]

        # Build the CAGR field name
        # Example: cagr_10yr
        cagr_key = f"cagr_{period_years}yr"

        # Get the calculated CAGR
        calculated_value = engine_result.get(cagr_key)

        # If the CAGR engine does not have enough data,
        # record the case for manual review
        if calculated_value is None:

            review_rows.append({
                "company_id": company_id,
                "metric_type": metric_type,
                "period_years": period_years,
                "parsed_value_pct": parsed_value,
                "calculated_value_pct": None,
                "divergence_pct": None,
                "status": "INSUFFICIENT_ENGINE_DATA",
            })

            continue

        # Find the difference between
        # the Excel value and calculated value
        divergence = abs(
            parsed_value - calculated_value
        )

        # If the difference is greater than 5 percentage points,
        # add it to the manual review file
        if divergence > 5:

            review_rows.append({
                "company_id": company_id,
                "metric_type": metric_type,
                "period_years": period_years,
                "parsed_value_pct": parsed_value,
                "calculated_value_pct": calculated_value,
                "divergence_pct": divergence,
                "status": "MANUAL_REVIEW",
            })

    # Convert the review records into a DataFrame
    review_df = pd.DataFrame(
        review_rows,
        columns=[
            "company_id",
            "metric_type",
            "period_years",
            "parsed_value_pct",
            "calculated_value_pct",
            "divergence_pct",
            "status",
        ],
    )

    # Save the manual review results
    review_df.to_csv(
        REVIEW_FILE,
        index=False,
    )

    # Show a simple summary
    print("CAGR comparison completed.")
    print("Manual review records:", len(review_df))
    print("Created:", REVIEW_FILE)


# Run the program
if __name__ == "__main__":
    main()
