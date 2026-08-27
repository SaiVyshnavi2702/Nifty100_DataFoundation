import os
import sqlite3

import pandas as pd

from src.analytics.ratios import (
    return_on_equity,
    return_on_capital_employed,
    high_leverage_flag,
)


DB_PATH = "data/nifty100.db"
COMPANIES_FILE = "data/raw/core/companies.xlsx"
LOG_FILE = "output/ratio_edge_cases.log"

ANOMALY_THRESHOLD = 5
EXPECTED_FINANCIALS_COUNT = 19


def load_source_data():
    companies = pd.read_excel(
        COMPANIES_FILE,
        header=1,
    )

    companies.columns = [
        str(column).strip()
        for column in companies.columns
    ]

    companies["id"] = (
        companies["id"]
        .astype(str)
        .str.strip()
    )

    return companies


def get_financials_companies(connection):
    query = """
        SELECT DISTINCT
            c.id,
            c.company_name,
            s.broad_sector
        FROM companies AS c
        JOIN sectors AS s
            ON c.id = s.company_id
        WHERE LOWER(TRIM(s.broad_sector)) = 'financials'
        ORDER BY c.id
    """

    return connection.execute(query).fetchall()


def get_financial_data(connection):
    query = """
        SELECT
            p.company_id,
            c.company_name,
            p.year,
            p.period,
            p.operating_profit,
            p.other_income,
            p.net_profit,
            b.equity_capital,
            b.reserves,
            b.borrowings
        FROM profitandloss AS p
        JOIN companies AS c
            ON c.id = p.company_id
        LEFT JOIN balancesheet AS b
            ON b.company_id = p.company_id
            AND b.year = p.year
            AND b.period = p.period
        WHERE p.period LIKE 'Mar %'
          AND p.year = (
              SELECT MAX(p2.year)
              FROM profitandloss AS p2
              WHERE p2.company_id = p.company_id
                AND p2.period LIKE 'Mar %'
          )
        ORDER BY p.company_id
    """

    return connection.execute(query).fetchall()


def get_balance_sheet_issues(connection):
    query = """
        SELECT
            b1.company_id,
            c1.company_name,
            b2.company_id,
            c2.company_name,
            b1.year,
            b1.period,
            b1.equity_capital,
            b1.reserves,
            b1.borrowings
        FROM balancesheet AS b1
        JOIN balancesheet AS b2
            ON b1.year = b2.year
            AND b1.period = b2.period
            AND b1.equity_capital = b2.equity_capital
            AND b1.reserves = b2.reserves
            AND b1.borrowings = b2.borrowings
            AND b1.company_id < b2.company_id
        LEFT JOIN companies AS c1
            ON c1.id = b1.company_id
        LEFT JOIN companies AS c2
            ON c2.id = b2.company_id
        ORDER BY
            b1.year,
            b1.period,
            b1.company_id,
            b2.company_id
    """

    return connection.execute(query).fetchall()


def calculate_ratios(row):
    (
        company_id,
        company_name,
        year,
        period,
        operating_profit,
        other_income,
        net_profit,
        equity_capital,
        reserves,
        borrowings,
    ) = row

    roce = return_on_capital_employed(
        operating_profit,
        other_income,
        equity_capital,
        reserves,
        borrowings,
    )

    roe = return_on_equity(
        net_profit,
        equity_capital,
        reserves,
    )

    return {
        "company_id": company_id,
        "company_name": company_name,
        "year": year,
        "period": period,
        "calculated_roce": roce,
        "calculated_roe": roe,
        "equity_capital": equity_capital,
        "reserves": reserves,
        "borrowings": borrowings,
        "operating_profit": operating_profit,
        "other_income": other_income,
        "net_profit": net_profit,
    }


def get_source_values(source_data, company_id):
    matches = source_data[
        source_data["id"] == str(company_id).strip()
    ]

    if matches.empty:
        return None, None

    row = matches.iloc[0]

    source_roce = row["roce_percentage"]
    source_roe = row["roe_percentage"]

    if pd.isna(source_roce):
        source_roce = None

    if pd.isna(source_roe):
        source_roe = None

    return source_roce, source_roe


def calculate_difference(calculated, source):
    if calculated is None or source is None:
        return None

    return abs(calculated - source)


def classify_anomaly(
    company_id,
    calculated_roce,
    source_roce,
    calculated_roe,
    source_roe,
):
    if (
        company_id == "TCS"
        and source_roe is not None
        and source_roe == 0.52
    ):
        return "DATA_SOURCE_ISSUE"

    if calculated_roce is None or source_roce is None:
        return "DATA_SOURCE_ISSUE"

    if calculated_roe is None or source_roe is None:
        return "DATA_SOURCE_ISSUE"

    roce_difference = calculate_difference(
        calculated_roce,
        source_roce,
    )

    roe_difference = calculate_difference(
        calculated_roe,
        source_roe,
    )

    roce_anomaly = (
        roce_difference is not None
        and roce_difference > ANOMALY_THRESHOLD
    )

    roe_anomaly = (
        roe_difference is not None
        and roe_difference > ANOMALY_THRESHOLD
    )

    if not roce_anomaly and not roe_anomaly:
        return "NO_ANOMALY"

    if (
        roce_difference is not None
        and roce_difference >= 20
    ):
        return "FORMULA_DISCREPANCY"

    if (
        roe_difference is not None
        and roe_difference >= 20
    ):
        return "FORMULA_DISCREPANCY"

    return "VERSION_DIFFERENCE"


def review_financials(connection):
    rows = get_financials_companies(connection)

    print("Financials company check")
    print(f"Distinct Financials companies: {len(rows)}")
    print(
        f"Expected Financials companies: "
        f"{EXPECTED_FINANCIALS_COUNT}"
    )

    if len(rows) == EXPECTED_FINANCIALS_COUNT:
        print("Financials count check: PASS")
    else:
        print(
            "Financials count check: REVIEW - "
            f"expected {EXPECTED_FINANCIALS_COUNT}, "
            f"found {len(rows)}"
        )

    print()
    print("Financials D/E warning check")

    for company_id, company_name, broad_sector in rows:
        ratio_rows = connection.execute(
            """
            SELECT
                year,
                debt_to_equity
            FROM financial_ratios
            WHERE company_id = ?
            ORDER BY year
            """,
            (company_id,),
        ).fetchall()

        for year, debt_equity in ratio_rows:
            warning = high_leverage_flag(
                debt_equity,
                broad_sector,
            )

            if warning:
                print(
                    f"{company_id} {year}: "
                    f"D/E={debt_equity} "
                    f"high_leverage_warning={warning}"
                )

    return rows


def print_balance_sheet_issues(balance_sheet_issues):
    print("Balance-sheet integrity check")

    if not balance_sheet_issues:
        print(
            "No exact duplicate balance-sheet "
            "value pairs found."
        )
        return

    print(
        "Potential duplicate balance-sheet "
        f"value pairs: {len(balance_sheet_issues)}"
    )

    for row in balance_sheet_issues:
        (
            company_id_1,
            company_name_1,
            company_id_2,
            company_name_2,
            year,
            period,
            equity_capital,
            reserves,
            borrowings,
        ) = row

        name_1 = (
            company_name_1.strip()
            if company_name_1
            else ""
        )

        name_2 = (
            company_name_2.strip()
            if company_name_2
            else ""
        )

        print(
            f"{company_id_1} ({name_1}) <-> "
            f"{company_id_2} ({name_2}) | "
            f"{year} | {period} | "
            f"equity_capital={equity_capital} | "
            f"reserves={reserves} | "
            f"borrowings={borrowings}"
        )


def build_audit_rows(financial_rows, source_data):
    audit_rows = []

    for row in financial_rows:
        calculated = calculate_ratios(row)

        source_roce, source_roe = get_source_values(
            source_data,
            calculated["company_id"],
        )

        calculated["source_roce"] = source_roce
        calculated["source_roe"] = source_roe

        calculated["roce_difference"] = calculate_difference(
            calculated["calculated_roce"],
            source_roce,
        )

        calculated["roe_difference"] = calculate_difference(
            calculated["calculated_roe"],
            source_roe,
        )

        calculated["category"] = classify_anomaly(
            calculated["company_id"],
            calculated["calculated_roce"],
            source_roce,
            calculated["calculated_roe"],
            source_roe,
        )

        audit_rows.append(calculated)

    return audit_rows


def is_roce_anomaly(row):
    difference = row["roce_difference"]

    return (
        difference is not None
        and difference > ANOMALY_THRESHOLD
    )


def is_roe_anomaly(row):
    difference = row["roe_difference"]

    return (
        difference is not None
        and difference > ANOMALY_THRESHOLD
    )


def print_ratio_anomalies(audit_rows):
    roce_anomalies = [
        row
        for row in audit_rows
        if is_roce_anomaly(row)
    ]

    roe_anomalies = [
        row
        for row in audit_rows
        if is_roe_anomaly(row)
    ]

    print(
        f"ROCE anomalies greater than "
        f"{ANOMALY_THRESHOLD}: {len(roce_anomalies)}"
    )

    print(
        f"ROE anomalies greater than "
        f"{ANOMALY_THRESHOLD}: {len(roe_anomalies)}"
    )

    print()
    print("Ratio anomaly details")

    for row in audit_rows:
        if not is_roce_anomaly(row) and not is_roe_anomaly(row):
            continue

        name = (
            row["company_name"].strip()
            if row["company_name"]
            else ""
        )

        print(
            f"{row['company_id']} ({name})"
        )

        print(f"  Year: {row['year']}")
        print(f"  Period: {row['period']}")

        print(
            f"  Calculated ROCE: "
            f"{row['calculated_roce']}"
        )

        print(
            f"  Source ROCE: "
            f"{row['source_roce']}"
        )

        print(
            f"  ROCE difference: "
            f"{row['roce_difference']}"
        )

        print(
            f"  Calculated ROE: "
            f"{row['calculated_roe']}"
        )

        print(
            f"  Source ROE: "
            f"{row['source_roe']}"
        )

        print(
            f"  ROE difference: "
            f"{row['roe_difference']}"
        )

        print(
            f"  Category: "
            f"{row['category']}"
        )

        print()


def write_log(
    financials,
    audit_rows,
    balance_sheet_issues,
):
    os.makedirs(
        os.path.dirname(LOG_FILE),
        exist_ok=True,
    )

    with open(
        LOG_FILE,
        "w",
        encoding="utf-8",
    ) as log:

        log.write(
            "Day 13 - Ratio Edge Case Review\n\n"
        )

        log.write("Financials sector check\n\n")

        log.write(
            f"Distinct Financials companies found: "
            f"{len(financials)}\n"
        )

        log.write(
            f"Expected Financials companies: "
            f"{EXPECTED_FINANCIALS_COUNT}\n"
        )

        if len(financials) == EXPECTED_FINANCIALS_COUNT:
            log.write(
                "Financials count check: PASS\n\n"
            )
        else:
            log.write(
                "Financials count check: REVIEW - "
                f"expected {EXPECTED_FINANCIALS_COUNT}, "
                f"found {len(financials)}\n\n"
            )

        log.write(
            "The high-leverage warning is intentionally "
            "suppressed for companies classified as Financials. "
            "High D/E is structurally normal for banks and "
            "financial institutions.\n\n"
        )

        log.write("Financials companies\n\n")

        for company_id, company_name, broad_sector in financials:
            name = (
                company_name.strip()
                if company_name
                else ""
            )

            log.write(
                f"{company_id} | {name} | "
                f"{broad_sector}\n"
            )

        log.write("\n")

        log.write("Balance-sheet integrity check\n\n")

        if not balance_sheet_issues:
            log.write(
                "No exact duplicate balance-sheet "
                "value pairs were found.\n"
            )
        else:
            log.write(
                "Potential duplicate balance-sheet "
                f"value pairs: {len(balance_sheet_issues)}\n"
            )

            log.write(
                "These records are flagged for review only. "
                "The database was not changed.\n\n"
            )

            for row in balance_sheet_issues:
                (
                    company_id_1,
                    company_name_1,
                    company_id_2,
                    company_name_2,
                    year,
                    period,
                    equity_capital,
                    reserves,
                    borrowings,
                ) = row

                name_1 = (
                    company_name_1.strip()
                    if company_name_1
                    else ""
                )

                name_2 = (
                    company_name_2.strip()
                    if company_name_2
                    else ""
                )

                log.write(
                    f"{company_id_1} | {name_1} | "
                    f"{company_id_2} | {name_2} | "
                    f"{year} | {period} | "
                    f"equity_capital={equity_capital} | "
                    f"reserves={reserves} | "
                    f"borrowings={borrowings}\n"
                )

        log.write("\n")
        log.write("Ratio edge cases\n\n")

        anomaly_count = 0
        roce_anomaly_count = 0
        roe_anomaly_count = 0

        for row in audit_rows:
            roce_anomaly = is_roce_anomaly(row)
            roe_anomaly = is_roe_anomaly(row)

            if roce_anomaly:
                roce_anomaly_count += 1

            if roe_anomaly:
                roe_anomaly_count += 1

            if not roce_anomaly and not roe_anomaly:
                continue

            anomaly_count += 1

            name = (
                row["company_name"].strip()
                if row["company_name"]
                else ""
            )

            log.write(
                f"Company: {name}\n"
            )

            log.write(
                f"Company ID: {row['company_id']}\n"
            )

            log.write(
                f"Year: {row['year']}\n"
            )

            log.write(
                f"Period: {row['period']}\n"
            )

            log.write(
                f"Calculated ROCE: "
                f"{row['calculated_roce']}\n"
            )

            log.write(
                f"Source ROCE: "
                f"{row['source_roce']}\n"
            )

            log.write(
                f"ROCE difference: "
                f"{row['roce_difference']}\n"
            )

            log.write(
                f"Calculated ROE: "
                f"{row['calculated_roe']}\n"
            )

            log.write(
                f"Source ROE: "
                f"{row['source_roe']}\n"
            )

            log.write(
                f"ROE difference: "
                f"{row['roe_difference']}\n"
            )

            log.write(
                f"Category: "
                f"{row['category']}\n"
            )

            log.write(
                "Note: The ratio engine value is used "
                "for analytics. The companies.xlsx "
                "value is used only for source comparison.\n\n"
            )

        log.write(
            f"Total ratio edge cases: {anomaly_count}\n"
        )

        log.write(
            f"ROCE anomalies greater than "
            f"{ANOMALY_THRESHOLD}: "
            f"{roce_anomaly_count}\n"
        )

        log.write(
            f"ROE anomalies greater than "
            f"{ANOMALY_THRESHOLD}: "
            f"{roe_anomaly_count}\n\n"
        )

        log.write("Category definitions\n\n")

        log.write(
            "DATA_SOURCE_ISSUE: The source value is missing, "
            "clearly incorrect, or the calculated value "
            "cannot be produced from the available data.\n"
        )

        log.write(
            "VERSION_DIFFERENCE: The calculated and source "
            "values differ by more than the configured "
            "threshold but not enough to indicate a major "
            "formula or denominator difference.\n"
        )

        log.write(
            "FORMULA_DISCREPANCY: The difference is large "
            "enough to suggest materially different "
            "calculation definitions or denominator treatment.\n"
        )

        log.write(
            "NO_ANOMALY: The calculated and source values "
            "are within the configured threshold.\n"
        )

        log.write("\n")

        log.write("ANALYTICS RULE\n\n")

        log.write(
            "The ratio engine calculation is used for "
            "analytics. The companies.xlsx value is used "
            "only as a source comparison reference.\n"
        )

        log.write("\n")

        log.write("DATA QUALITY RULE\n\n")

        log.write(
            "Balance-sheet integrity checks are audit-only. "
            "The script does not modify financial records.\n"
        )


def main():
    print("Day 13 - Ratio edge case review")
    print()

    source_data = load_source_data()

    connection = sqlite3.connect(DB_PATH)

    try:
        financials = review_financials(
            connection
        )

        print()

        balance_sheet_issues = (
            get_balance_sheet_issues(
                connection
            )
        )

        print_balance_sheet_issues(
            balance_sheet_issues
        )

        financial_rows = get_financial_data(
            connection
        )

        print()
        print(
            f"Latest annual financial rows: "
            f"{len(financial_rows)}"
        )

        latest_years = sorted(
            set(
                row[2]
                for row in financial_rows
            )
        )

        print(
            f"Latest annual years: {latest_years}"
        )

        print()

        audit_rows = build_audit_rows(
            financial_rows,
            source_data,
        )

        print_ratio_anomalies(
            audit_rows
        )

        write_log(
            financials,
            audit_rows,
            balance_sheet_issues,
        )

        print(
            f"Log created: {LOG_FILE}"
        )

        category_counts = {}

        for row in audit_rows:
            category = row["category"]

            category_counts[category] = (
                category_counts.get(category, 0) + 1
            )

        print()
        print("Category summary")

        for category in (
            "FORMULA_DISCREPANCY",
            "VERSION_DIFFERENCE",
            "DATA_SOURCE_ISSUE",
            "NO_ANOMALY",
        ):
            print(
                f"{category}: "
                f"{category_counts.get(category, 0)}"
            )

        print()
        print(
            "Ratio edge case review completed."
        )

    finally:
        connection.close()


if __name__ == "__main__":
    main()
