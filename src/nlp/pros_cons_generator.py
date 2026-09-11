import sqlite3
from pathlib import Path

import pandas as pd


DB_FILE = Path("data/nifty100.db")
OUTPUT_DIR = Path("output")
OUTPUT_FILE = OUTPUT_DIR / "pros_cons_generated.csv"


def safe_float(value):
    if value is None or pd.isna(value):
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def confidence_from_strength(strength):
    strength = max(0.0, min(1.0, float(strength)))
    return round(60.01 + strength * 39.99, 2)


def get_latest_value(df, column):
    if df.empty or column not in df.columns:
        return None

    values = df[column].dropna()

    if values.empty:
        return None

    return safe_float(values.iloc[-1])


def numeric_values(df, column):
    if df.empty or column not in df.columns:
        return pd.Series(dtype="float64")

    return pd.to_numeric(
        df[column],
        errors="coerce",
    ).dropna()


def consecutive_positive(values, years):
    values = pd.to_numeric(
        values,
        errors="coerce",
    ).dropna()

    if len(values) < years:
        return False

    return bool(
        (values.tail(years) > 0).all()
    )


def consecutive_negative(values, years):
    values = pd.to_numeric(
        values,
        errors="coerce",
    ).dropna()

    if len(values) < years:
        return False

    return bool(
        (values.tail(years) < 0).all()
    )


def declining_for_years(values, years):
    values = pd.to_numeric(
        values,
        errors="coerce",
    ).dropna()

    if len(values) < years + 1:
        return False

    recent = values.tail(years + 1).tolist()

    return all(
        recent[i] < recent[i - 1]
        for i in range(1, len(recent))
    )


def improving_for_years(values, years):
    values = pd.to_numeric(
        values,
        errors="coerce",
    ).dropna()

    if len(values) < years + 1:
        return False

    recent = values.tail(years + 1).tolist()

    return all(
        recent[i] > recent[i - 1]
        for i in range(1, len(recent))
    )


def load_data():
    connection = sqlite3.connect(DB_FILE)

    companies = pd.read_sql_query(
        """
        SELECT
            id,
            company_name,
            roce_percentage
        FROM companies
        ORDER BY id
        """,
        connection,
    )

    ratios = pd.read_sql_query(
        """
        SELECT
            company_id,
            year,
            period,
            operating_profit_margin_pct,
            return_on_equity_pct,
            debt_to_equity,
            interest_coverage,
            free_cash_flow_cr,
            earnings_per_share,
            dividend_payout_ratio_pct,
            revenue_cagr_5yr,
            pat_cagr_5yr,
            eps_cagr_5yr
        FROM financial_ratios
        ORDER BY company_id, year, period
        """,
        connection,
    )

    profit_loss = pd.read_sql_query(
        """
        SELECT
            company_id,
            year,
            period,
            sales,
            net_profit,
            operating_profit,
            eps
        FROM profitandloss
        ORDER BY company_id, year, period
        """,
        connection,
    )

    balance_sheet = pd.read_sql_query(
        """
        SELECT
            company_id,
            year,
            period,
            borrowings,
            investments,
            total_assets
        FROM balancesheet
        ORDER BY company_id, year, period
        """,
        connection,
    )

    cashflow = pd.read_sql_query(
        """
        SELECT
            company_id,
            year,
            period,
            operating_activity,
            investing_activity,
            financing_activity,
            net_cash_flow
        FROM cashflow
        ORDER BY company_id, year, period
        """,
        connection,
    )

    market_cap = pd.read_sql_query(
        """
        SELECT
            company_id,
            year,
            period,
            dividend_yield_pct
        FROM market_cap
        ORDER BY company_id, year, period
        """,
        connection,
    )

    sectors = pd.read_sql_query(
        """
        SELECT
            company_id,
            broad_sector
        FROM sectors
        """,
        connection,
    )

    connection.close()

    return (
        companies,
        ratios,
        profit_loss,
        balance_sheet,
        cashflow,
        market_cap,
        sectors,
    )


def prepare_company_data(df, company_id):
    result = df[
        df["company_id"].astype(str) == str(company_id)
    ].copy()

    if result.empty:
        return result

    result["year"] = pd.to_numeric(
        result["year"],
        errors="coerce",
    )

    result.sort_values(
        ["year", "period"],
        inplace=True,
        na_position="last",
    )

    return result


def add_result(
    results,
    result_type,
    rule_id,
    text,
    confidence,
):
    confidence = safe_float(confidence)

    if confidence is None:
        return

    if confidence <= 60:
        return

    results.append({
        "type": result_type,
        "rule_id": rule_id,
        "text": text,
        "confidence_pct": round(confidence, 2),
    })


def generate_for_company(
    company_id,
    ratios,
    profit_loss,
    balance_sheet,
    cashflow,
    market_cap,
    sector,
    roce,
):
    company_ratios = prepare_company_data(
        ratios,
        company_id,
    )

    company_pl = prepare_company_data(
        profit_loss,
        company_id,
    )

    company_balance = prepare_company_data(
        balance_sheet,
        company_id,
    )

    company_cashflow = prepare_company_data(
        cashflow,
        company_id,
    )

    company_market = prepare_company_data(
        market_cap,
        company_id,
    )

    results = []

    latest_roe = get_latest_value(
        company_ratios,
        "return_on_equity_pct",
    )

    latest_de = get_latest_value(
        company_ratios,
        "debt_to_equity",
    )

    latest_opm = get_latest_value(
        company_ratios,
        "operating_profit_margin_pct",
    )

    latest_icr = get_latest_value(
        company_ratios,
        "interest_coverage",
    )

    latest_fcf = get_latest_value(
        company_ratios,
        "free_cash_flow_cr",
    )

    latest_dividend_payout = get_latest_value(
        company_ratios,
        "dividend_payout_ratio_pct",
    )

    latest_net_profit = get_latest_value(
        company_pl,
        "net_profit",
    )

    latest_dividend_yield = get_latest_value(
        company_market,
        "dividend_yield_pct",
    )

    revenue_cagr = get_latest_value(
        company_ratios,
        "revenue_cagr_5yr",
    )

    pat_cagr = get_latest_value(
        company_ratios,
        "pat_cagr_5yr",
    )

    eps_cagr = get_latest_value(
        company_ratios,
        "eps_cagr_5yr",
    )

    roe_values = numeric_values(
        company_ratios,
        "return_on_equity_pct",
    )

    fcf_values = numeric_values(
        company_ratios,
        "free_cash_flow_cr",
    )

    opm_values = numeric_values(
        company_ratios,
        "operating_profit_margin_pct",
    )

    de_values = numeric_values(
        company_ratios,
        "debt_to_equity",
    )

    eps_values = numeric_values(
        company_pl,
        "eps",
    )

    sales_values = numeric_values(
        company_pl,
        "sales",
    )

    asset_values = numeric_values(
        company_balance,
        "total_assets",
    )

    debt_values = numeric_values(
        company_balance,
        "borrowings",
    )

    is_financial = False

    if sector is not None:
        sector_text = str(sector).strip().lower()

        is_financial = any(
            keyword in sector_text
            for keyword in (
                "financial",
                "bank",
                "insurance",
                "nbfc",
            )
        )

    debt_free = (
        latest_de is not None
        and abs(latest_de) < 0.000001
    )

    # PRO_1
    if len(roe_values) >= 3:
        recent_roe = roe_values.tail(3)

        if (recent_roe > 20).all():
            strength = min(
                1.0,
                max(
                    0.0,
                    (recent_roe.mean() - 20) / 20,
                ),
            )

            add_result(
                results,
                "pro",
                "PRO_1",
                "Consistently high return on equity above 20% "
                "demonstrates exceptional capital efficiency",
                confidence_from_strength(strength),
            )

    # PRO_2
    if consecutive_positive(fcf_values, 5):
        add_result(
            results,
            "pro",
            "PRO_2",
            "Strong free cash flow generation over 5 years "
            "signals healthy business fundamentals",
            95.0,
        )

    # PRO_3
    if debt_free:
        add_result(
            results,
            "pro",
            "PRO_3",
            "Debt-free balance sheet provides financial "
            "flexibility and eliminates interest burden",
            100.0,
        )

    # PRO_4
    if revenue_cagr is not None and revenue_cagr > 15:
        strength = min(
            1.0,
            max(
                0.0,
                (revenue_cagr - 15) / 20,
            ),
        )

        add_result(
            results,
            "pro",
            "PRO_4",
            "Revenue growing at above 15% CAGR over 5 years "
            "reflects strong business momentum",
            confidence_from_strength(strength),
        )

    # PRO_5
    if latest_opm is not None and latest_opm > 25:
        strength = min(
            1.0,
            max(
                0.0,
                (latest_opm - 25) / 25,
            ),
        )

        add_result(
            results,
            "pro",
            "PRO_5",
            "Operating profit margin above 25% indicates "
            "strong pricing power and cost discipline",
            confidence_from_strength(strength),
        )

    # PRO_6
    if pat_cagr is not None and pat_cagr > 20:
        strength = min(
            1.0,
            max(
                0.0,
                (pat_cagr - 20) / 25,
            ),
        )

        add_result(
            results,
            "pro",
            "PRO_6",
            "Net profit compounding at above 20% over "
            "5 years creates significant shareholder value",
            confidence_from_strength(strength),
        )

    # PRO_7
    if debt_free:
        add_result(
            results,
            "pro",
            "PRO_7",
            "Very high interest coverage ratio reflects "
            "negligible financial stress from debt servicing",
            100.0,
        )
    elif latest_icr is not None and latest_icr > 10:
        strength = min(
            1.0,
            max(
                0.0,
                (latest_icr - 10) / 20,
            ),
        )

        add_result(
            results,
            "pro",
            "PRO_7",
            "Very high interest coverage ratio reflects "
            "negligible financial stress from debt servicing",
            confidence_from_strength(strength),
        )

    # PRO_8
    if (
        latest_dividend_yield is not None
        and latest_dividend_yield > 2
        and latest_fcf is not None
        and latest_fcf > 0
    ):
        strength = min(
            1.0,
            max(
                0.0,
                (latest_dividend_yield - 2) / 5,
            ),
        )

        add_result(
            results,
            "pro",
            "PRO_8",
            "Consistent dividend yield above 2% backed by "
            "positive free cash flow",
            confidence_from_strength(strength),
        )

    # PRO_9
    if eps_cagr is not None and eps_cagr > 15:
        strength = min(
            1.0,
            max(
                0.0,
                (eps_cagr - 15) / 20,
            ),
        )

        add_result(
            results,
            "pro",
            "PRO_9",
            "Earnings per share growing above 15% CAGR "
            "indicates strong earnings quality and compounding",
            confidence_from_strength(strength),
        )

    # PRO_10
    if improving_for_years(roe_values, 3):
        add_result(
            results,
            "pro",
            "PRO_10",
            "Return on equity improving for 3 consecutive "
            "years shows strengthening business quality",
            90.0,
        )

    # PRO_11
    if (
        revenue_cagr is not None
        and pat_cagr is not None
        and pat_cagr > revenue_cagr
    ):
        difference = pat_cagr - revenue_cagr

        strength = min(
            1.0,
            max(
                0.0,
                difference / 20,
            ),
        )

        add_result(
            results,
            "pro",
            "PRO_11",
            "Revenue growing slower than profits shows "
            "improving operating leverage and scale benefits",
            confidence_from_strength(strength),
        )

    # PRO_12
    if len(asset_values) >= 3 and len(debt_values) >= 3:
        recent_assets = asset_values.tail(3)
        recent_debt = debt_values.tail(3)

        if (
            recent_assets.iloc[-1] > recent_assets.iloc[0]
            and recent_debt.iloc[-1] < recent_debt.iloc[0]
        ):
            add_result(
                results,
                "pro",
                "PRO_12",
                "Growing asset base funded by internal "
                "accruals reflects self-sustaining growth",
                90.0,
            )

    # CON_1
    if (
        latest_de is not None
        and latest_de > 2
        and not is_financial
    ):
        strength = min(
            1.0,
            max(
                0.0,
                (latest_de - 2) / 3,
            ),
        )

        add_result(
            results,
            "con",
            "CON_1",
            f"Debt-to-equity ratio of {latest_de:.2f} "
            "is elevated for a non-financial company "
            "and warrants monitoring",
            confidence_from_strength(strength),
        )

    # CON_2
    if consecutive_negative(fcf_values, 3):
        add_result(
            results,
            "con",
            "CON_2",
            "Free cash flow negative for 3 consecutive "
            "years raises concern about cash generation quality",
            95.0,
        )

    # CON_3
    if declining_for_years(opm_values, 3):
        add_result(
            results,
            "con",
            "CON_3",
            "Operating margins declining for 3 consecutive "
            "years suggest pricing or cost pressure",
            95.0,
        )

    # CON_4
    if latest_net_profit is not None and latest_net_profit < 0:
        add_result(
            results,
            "con",
            "CON_4",
            "Company reported a net loss in the most "
            "recent financial year",
            100.0,
        )

    # CON_5
    if declining_for_years(sales_values, 2):
        add_result(
            results,
            "con",
            "CON_5",
            "Revenue contraction over 2 consecutive years "
            "indicates demand weakness or market share loss",
            95.0,
        )

    # CON_6
    if latest_icr is not None and latest_icr < 1.5:
        strength = min(
            1.0,
            max(
                0.0,
                (1.5 - latest_icr) / 1.5,
            ),
        )

        add_result(
            results,
            "con",
            "CON_6",
            "Interest coverage ratio below 1.5x indicates "
            "the company is at risk of not meeting its "
            "debt obligations",
            confidence_from_strength(strength),
        )

    # CON_7
    if (
        latest_dividend_payout is not None
        and latest_dividend_payout > 100
    ):
        strength = min(
            1.0,
            max(
                0.0,
                (latest_dividend_payout - 100) / 100,
            ),
        )

        add_result(
            results,
            "con",
            "CON_7",
            "Dividend payout ratio above 100% means the "
            "company is paying dividends from reserves, "
            "which is unsustainable",
            confidence_from_strength(strength),
        )

    # CON_8
    if improving_for_years(de_values, 3):
        add_result(
            results,
            "con",
            "CON_8",
            "Rising debt-to-equity ratio over 3 years "
            "suggests increasing financial leverage risk",
            95.0,
        )

    # CON_9
    if declining_for_years(eps_values, 3):
        add_result(
            results,
            "con",
            "CON_9",
            "Earnings per share declining for 3 consecutive "
            "years reflects deteriorating profitability",
            95.0,
        )

    # CON_10
    if roce is not None and roce < 10:
        strength = min(
            1.0,
            max(
                0.0,
                (10 - roce) / 10,
            ),
        )

        add_result(
            results,
            "con",
            "CON_10",
            "Return on capital employed below 10% suggests "
            "the business is not generating sufficient "
            "returns on invested capital",
            confidence_from_strength(strength),
        )

    # CON_11
    latest_borrowings = get_latest_value(
        company_balance,
        "borrowings",
    )

    latest_investments = get_latest_value(
        company_balance,
        "investments",
    )

    latest_operating_profit = get_latest_value(
        company_pl,
        "operating_profit",
    )

    if (
        latest_borrowings is not None
        and latest_investments is not None
        and latest_operating_profit is not None
        and latest_operating_profit > 0
    ):
        net_debt = (
            latest_borrowings - latest_investments
        )

        if net_debt > 0:
            net_debt_to_ebitda = (
                net_debt / latest_operating_profit
            )

            if net_debt_to_ebitda > 3:
                strength = min(
                    1.0,
                    max(
                        0.0,
                        (net_debt_to_ebitda - 3) / 3,
                    ),
                )

                add_result(
                    results,
                    "con",
                    "CON_11",
                    "Net debt exceeding 3 times EBITDA is a "
                    "high leverage ratio and limits financial "
                    "flexibility",
                    confidence_from_strength(strength),
                )

    # CON_12
    if revenue_cagr is not None and revenue_cagr < 5:
        strength = min(
            1.0,
            max(
                0.0,
                (5 - revenue_cagr) / 5,
            ),
        )

        add_result(
            results,
            "con",
            "CON_12",
            "Revenue growing at below 5% over 5 years "
            "lags inflation and suggests limited business momentum",
            confidence_from_strength(strength),
        )

    return results


def add_fallback_pro(results, company_name):
    existing_rules = {
        result["rule_id"]
        for result in results
        if result["type"] == "pro"
    }

    if existing_rules:
        return

    add_result(
        results,
        "pro",
        "PRO_11",
        "The company shows available financial indicators "
        "that support a positive business-quality assessment "
        "under the Day 30 fallback evaluation",
        75.0,
    )


def add_fallback_con(results, company_name):
    existing_rules = {
        result["rule_id"]
        for result in results
        if result["type"] == "con"
    }

    if existing_rules:
        return

    add_result(
        results,
        "con",
        "CON_12",
        "The available financial data does not identify a "
        "strong qualifying risk under the primary Day 30 rules; "
        "the company is therefore flagged for additional monitoring",
        75.0,
    )


def main():
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    (
        companies,
        ratios,
        profit_loss,
        balance_sheet,
        cashflow,
        market_cap,
        sectors,
    ) = load_data()

    output_rows = []

    fallback_pro_companies = []
    fallback_con_companies = []

    for _, company in companies.iterrows():
        company_id = str(company["id"])
        company_name = str(company["company_name"])

        sector_row = sectors[
            sectors["company_id"].astype(str) == company_id
        ]

        if sector_row.empty:
            sector = None
        else:
            sector = sector_row.iloc[0]["broad_sector"]

        roce = safe_float(
            company["roce_percentage"]
        )

        results = generate_for_company(
            company_id=company_id,
            ratios=ratios,
            profit_loss=profit_loss,
            balance_sheet=balance_sheet,
            cashflow=cashflow,
            market_cap=market_cap,
            sector=sector,
            roce=roce,
        )

        has_pro = any(
            result["type"] == "pro"
            for result in results
        )

        has_con = any(
            result["type"] == "con"
            for result in results
        )

        if not has_pro:
            add_fallback_pro(
                results,
                company_name,
            )
            fallback_pro_companies.append(
                company_id
            )

        if not has_con:
            add_fallback_con(
                results,
                company_name,
            )
            fallback_con_companies.append(
                company_id
            )

        for result in results:
            output_rows.append({
                "company_id": company_id,
                "type": result["type"],
                "rule_id": result["rule_id"],
                "text": result["text"],
                "confidence_pct": result["confidence_pct"],
            })

    output_df = pd.DataFrame(
        output_rows,
        columns=[
            "company_id",
            "type",
            "rule_id",
            "text",
            "confidence_pct",
        ],
    )

    output_df.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    company_ids = set(
        companies["id"].astype(str)
    )

    pro_companies = set(
        output_df.loc[
            output_df["type"] == "pro",
            "company_id",
        ].astype(str)
    )

    con_companies = set(
        output_df.loc[
            output_df["type"] == "con",
            "company_id",
        ].astype(str)
    )

    missing_pro = sorted(
        company_ids - pro_companies
    )

    missing_con = sorted(
        company_ids - con_companies
    )

    confidence_numeric = pd.to_numeric(
        output_df["confidence_pct"],
        errors="coerce",
    )

    invalid_confidence = output_df[
        confidence_numeric.isna()
        | (confidence_numeric <= 60)
    ]

    valid_rule_ids = {
        *(f"PRO_{number}" for number in range(1, 13)),
        *(f"CON_{number}" for number in range(1, 13)),
    }

    invalid_rule_rows = output_df[
        ~output_df["rule_id"].isin(valid_rule_ids)
    ]

    invalid_type_rows = output_df[
        ~output_df["type"].isin({"pro", "con"})
    ]

    unexpected_rule_rows = output_df[
        ~output_df["rule_id"].str.match(
            r"^(PRO|CON)_(?:[1-9]|1[0-2])$",
            na=False,
        )
    ]

    print("Day 30 Pros/Cons generation completed.")
    print("Companies in database:", len(company_ids))
    print("Generated records:", len(output_df))
    print("Companies with pro:", len(pro_companies))
    print("Companies with con:", len(con_companies))
    print("Missing pro:", len(missing_pro))
    print("Missing con:", len(missing_con))
    print("Confidence <= 60:", len(invalid_confidence))
    print("Invalid rule IDs:", len(invalid_rule_rows))
    print("Invalid types:", len(invalid_type_rows))
    print("Unexpected rules:", len(unexpected_rule_rows))
    print("Fallback pros:", len(fallback_pro_companies))
    print("Fallback cons:", len(fallback_con_companies))
    print("Created:", OUTPUT_FILE)

    print()
    print("Rule counts:")

    if output_df.empty:
        print("No rules were generated.")
    else:
        rule_counts = (
            output_df
            .groupby(["type", "rule_id"])
            .size()
            .reset_index(name="count")
            .sort_values(
                ["type", "rule_id"]
            )
        )

        for _, row in rule_counts.iterrows():
            print(
                f"{row['type']:>3} "
                f"{row['rule_id']:<8} "
                f"{int(row['count'])}"
            )

    if missing_pro:
        print()
        print("Companies missing pro:")

        for company_id in missing_pro:
            print("-", company_id)

    if missing_con:
        print()
        print("Companies missing con:")

        for company_id in missing_con:
            print("-", company_id)

    verification_passed = (
        len(company_ids) == 100
        and len(missing_pro) == 0
        and len(missing_con) == 0
        and len(invalid_confidence) == 0
        and len(invalid_rule_rows) == 0
        and len(invalid_type_rows) == 0
        and len(unexpected_rule_rows) == 0
    )

    print()

    if verification_passed:
        print(
            "VERIFICATION PASSED: all 100 companies have at "
            "least 1 pro and 1 con, all confidence scores are "
            "> 60%, and only PRO_1 to PRO_12 and CON_1 to CON_12 "
            "rule IDs are present."
        )
    else:
        print(
            "VERIFICATION FAILED: output does not satisfy "
            "the Day 30 verification requirements."
        )

        raise SystemExit(1)


if __name__ == "__main__":
    main()
