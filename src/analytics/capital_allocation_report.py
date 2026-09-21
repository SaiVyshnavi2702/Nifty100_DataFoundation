import os

import pandas as pd

CAPITAL_ALLOCATION_INPUT = "output/capital_allocation.csv"

CASHFLOW_INTELLIGENCE_INPUT = "output/cashflow_intelligence.xlsx"

PATTERN_CHANGES_OUTPUT = "output/pattern_changes.csv"


EXPECTED_PATTERNS = [
    "Shareholder Returns",
    "Reinvestor",
    "Liquidating Assets",
    "Distress Signal",
    "Growth Funded by Debt",
    "Cash Accumulator",
    "Pre-Revenue",
    "Mixed",
]


def load_capital_allocation():
    """Load capital allocation."""
    if not os.path.exists(CAPITAL_ALLOCATION_INPUT):

        raise FileNotFoundError(
            f"Capital allocation file not found: {CAPITAL_ALLOCATION_INPUT}"
        )

    df = pd.read_csv(CAPITAL_ALLOCATION_INPUT)

    required_columns = [
        "company_id",
        "year",
        "cfo_sign",
        "cfi_sign",
        "cff_sign",
        "pattern_label",
    ]

    missing_columns = [
        column for column in required_columns if column not in df.columns
    ]

    if missing_columns:

        raise ValueError(
            f"Missing columns in capital_allocation.csv: {missing_columns}"
        )

    df["year"] = pd.to_numeric(df["year"], errors="coerce")

    df = df.dropna(subset=["company_id", "year"]).copy()

    df["year"] = df["year"].astype(int)

    df.sort_values(["company_id", "year"], inplace=True)

    df.reset_index(drop=True, inplace=True)

    return df


def verify_capital_allocation(df):
    """Verify capital allocation."""
    print()

    print("CAPITAL ALLOCATION VERIFICATION")

    company_count = df["company_id"].nunique()

    years = sorted(df["year"].unique())

    print("Companies:", company_count)

    print("Years:", years)

    print("Rows:", len(df))

    expected_columns = [
        "company_id",
        "year",
        "cfo_sign",
        "cfi_sign",
        "cff_sign",
        "pattern_label",
    ]

    columns_valid = list(df.columns) == expected_columns

    print("Columns valid:", columns_valid)

    if not columns_valid:

        raise ValueError("Capital allocation columns are not correct.")

    if company_count == 0:

        raise ValueError("No companies found in capital_allocation.csv.")

    if df["pattern_label"].isna().any():

        raise ValueError("Some capital allocation rows have missing pattern labels.")

    invalid_patterns = sorted(set(df["pattern_label"]) - set(EXPECTED_PATTERNS))

    print("Invalid patterns:", invalid_patterns)

    if invalid_patterns:

        raise ValueError(f"Unexpected capital allocation patterns: {invalid_patterns}")

    company_year_counts = df.groupby("company_id")["year"].nunique()

    min_year_count = int(company_year_counts.min())

    max_year_count = int(company_year_counts.max())

    print("Minimum years per company:", min_year_count)

    print("Maximum years per company:", max_year_count)

    return company_count, years


def generate_latest_year_distribution(df):
    """Generate latest year distribution."""
    latest_year = int(df["year"].max())

    latest_df = df[df["year"] == latest_year].copy()

    distribution = (
        latest_df["pattern_label"]
        .value_counts()
        .reindex(EXPECTED_PATTERNS, fill_value=0)
    )

    print()

    print(f"CAPITAL ALLOCATION DISTRIBUTION - LATEST YEAR ({latest_year})")

    for pattern, count in distribution.items():

        print(f"{pattern}: {count}")

    print("Companies in latest year:", latest_df["company_id"].nunique())

    return distribution


def update_cashflow_intelligence(df):
    """Update cashflow intelligence."""
    if not os.path.exists(CASHFLOW_INTELLIGENCE_INPUT):

        raise FileNotFoundError(
            f"Cash flow intelligence file not found: {CASHFLOW_INTELLIGENCE_INPUT}"
        )

    intelligence_df = pd.read_excel(CASHFLOW_INTELLIGENCE_INPUT)

    if "company_id" not in intelligence_df.columns:

        raise ValueError("cashflow_intelligence.xlsx does not contain company_id.")

    if "capital_allocation" in intelligence_df.columns:

        intelligence_df.drop(columns=["capital_allocation"], inplace=True)

    latest_year = int(df["year"].max())

    latest_allocation = df[df["year"] == latest_year][
        ["company_id", "pattern_label"]
    ].copy()

    latest_allocation.rename(
        columns={"pattern_label": "capital_allocation"}, inplace=True
    )

    intelligence_df["company_id"] = intelligence_df["company_id"].astype(str)

    latest_allocation["company_id"] = latest_allocation["company_id"].astype(str)

    intelligence_df = intelligence_df.merge(
        latest_allocation, on="company_id", how="left"
    )

    if intelligence_df["capital_allocation"].isna().any():

        missing_companies = intelligence_df[
            intelligence_df["capital_allocation"].isna()
        ]["company_id"].tolist()

        raise ValueError(
            "Capital allocation could not be assigned to companies: "
            f"{missing_companies}"
        )

    intelligence_df.to_excel(CASHFLOW_INTELLIGENCE_INPUT, index=False)

    print()

    print("Updated:", CASHFLOW_INTELLIGENCE_INPUT)

    print("Added column: capital_allocation")

    print("Intelligence rows:", len(intelligence_df))

    print("Intelligence companies:", intelligence_df["company_id"].nunique())

    return intelligence_df


def generate_pattern_changes(df):
    """Generate pattern changes."""
    changes = []

    for company_id, group in df.groupby("company_id", sort=False):

        group = group.sort_values("year").copy()

        previous_pattern = None

        previous_year = None

        for _, row in group.iterrows():

            current_year = int(row["year"])

            current_pattern = row["pattern_label"]

            if previous_pattern is not None and current_pattern != previous_pattern:
                changes.append(
                    {
                        "company_id": str(company_id),
                        "from_year": previous_year,
                        "to_year": current_year,
                        "previous_pattern": previous_pattern,
                        "new_pattern": current_pattern,
                    }
                )

            previous_pattern = current_pattern

            previous_year = current_year

    pattern_changes_df = pd.DataFrame(
        changes,
        columns=[
            "company_id",
            "from_year",
            "to_year",
            "previous_pattern",
            "new_pattern",
        ],
    )

    pattern_changes_df.to_csv(PATTERN_CHANGES_OUTPUT, index=False)

    print()

    print("Created:", PATTERN_CHANGES_OUTPUT)

    print("Pattern changes:", len(pattern_changes_df))

    return pattern_changes_df


def verify_day32_outputs(capital_df, intelligence_df, pattern_changes_df):
    """Verify day32 outputs."""
    latest_year = int(capital_df["year"].max())

    latest_company_count = capital_df[capital_df["year"] == latest_year][
        "company_id"
    ].nunique()

    intelligence_company_count = intelligence_df["company_id"].nunique()

    expected_intelligence_columns = [
        "company_id",
        "sector",
        "cfo_quality_score",
        "cfo_quality_label",
        "capex_intensity_pct",
        "capex_label",
        "fcf_cagr_5yr",
        "fcf_conversion_pct",
        "distress_flag",
        "deleveraging_flag",
        "capital_allocation_label",
        "capital_allocation",
    ]

    intelligence_columns_valid = (
        list(intelligence_df.columns) == expected_intelligence_columns
    )

    pattern_change_columns_valid = list(pattern_changes_df.columns) == [
        "company_id",
        "from_year",
        "to_year",
        "previous_pattern",
        "new_pattern",
    ]

    pattern_changes_valid = True

    if not pattern_changes_df.empty:

        pattern_changes_valid = (
            pattern_changes_df["previous_pattern"] != pattern_changes_df["new_pattern"]
        ).all()

    outputs_exist = (
        os.path.exists(CAPITAL_ALLOCATION_INPUT)
        and os.path.exists(CASHFLOW_INTELLIGENCE_INPUT)
        and os.path.exists(PATTERN_CHANGES_OUTPUT)
    )

    print()

    print("DAY 32 VERIFICATION")

    print("Latest year:", latest_year)

    print("Companies in latest year:", latest_company_count)

    print("Companies in intelligence:", intelligence_company_count)

    print(
        "Capital allocation column added:",
        "capital_allocation" in intelligence_df.columns,
    )

    print("Intelligence columns valid:", intelligence_columns_valid)

    print("Pattern changes columns valid:", pattern_change_columns_valid)

    print("Pattern changes valid:", pattern_changes_valid)

    print("Required output exists:", outputs_exist)

    verification_passed = (
        latest_company_count > 0
        and intelligence_company_count == latest_company_count
        and "capital_allocation" in intelligence_df.columns
        and intelligence_df["capital_allocation"].notna().all()
        and intelligence_columns_valid
        and pattern_change_columns_valid
        and pattern_changes_valid
        and outputs_exist
    )

    if verification_passed:

        print()

        print(
            "VERIFICATION PASSED: Day 32 Capital Allocation Report "
            "completed successfully."
        )

    else:

        print()

        print(
            "VERIFICATION FAILED: one or more Day 32 requirements "
            "were not satisfied."
        )

        raise SystemExit(1)


def main():
    """Run the main workflow."""
    print("DAY 32 - CAPITAL ALLOCATION REPORT")

    os.makedirs("output", exist_ok=True)

    print()

    print("Loading capital allocation data...")

    capital_df = load_capital_allocation()

    _company_count, _years = verify_capital_allocation(capital_df)

    print()

    print("Generating latest-year distribution...")

    generate_latest_year_distribution(capital_df)

    print()

    print("Updating cashflow intelligence Excel...")

    intelligence_df = update_cashflow_intelligence(capital_df)

    print()

    print("Detecting year-over-year pattern changes...")

    pattern_changes_df = generate_pattern_changes(capital_df)

    print()

    print("Pattern change summary:")

    if pattern_changes_df.empty:

        print("No year-over-year pattern changes found.")

    else:

        print(pattern_changes_df.head(20).to_string(index=False))

    verify_day32_outputs(capital_df, intelligence_df, pattern_changes_df)

    print()

    print("Day 32 Capital Allocation Report completed successfully.")


if __name__ == "__main__":

    main()
