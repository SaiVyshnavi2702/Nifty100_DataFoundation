import sqlite3

DB = "data/nifty100.db"

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row

query = """
SELECT *
FROM financial_ratios
WHERE period LIKE 'Mar %'
  AND year = (
      SELECT MAX(f2.year)
      FROM financial_ratios f2
      WHERE f2.company_id = financial_ratios.company_id
        AND f2.period LIKE 'Mar %'
  )
ORDER BY company_id
LIMIT 5
"""

rows = conn.execute(query).fetchall()

print("=" * 90)
print("DAY 14 - FINANCIAL RATIOS TABLE DEMO")
print("Latest Annual Data - March 2024")
print("=" * 90)

for row in rows:
    print("\n" + "-" * 90)
    print(f"Company: {row['company_id']}    Year: {row['year']}    Period: {row['period']}")
    print("-" * 90)

    print("Profitability")
    print(f"  Net Profit Margin       : {row['net_profit_margin_pct']:.2f}%")
    print(f"  Operating Profit Margin : {row['operating_profit_margin_pct']:.2f}%")
    print(f"  Return on Equity (ROE)  : {row['return_on_equity_pct']:.2f}%")

    print("\nLeverage & Coverage")
    print(f"  Debt-to-Equity           : {row['debt_to_equity']:.4f}")
    print(f"  Interest Coverage        : {row['interest_coverage']:.2f}")
    print(f"  Total Debt               : {row['total_debt_cr']:.2f} Cr")

    print("\nEfficiency & Cash Flow")
    print(f"  Asset Turnover           : {row['asset_turnover']:.4f}")
    print(f"  Free Cash Flow           : {row['free_cash_flow_cr']:.2f} Cr")
    print(f"  Capex                    : {row['capex_cr']:.2f} Cr")
    print(f"  Cash from Operations     : {row['cash_from_operations_cr']:.2f} Cr")

    print("\nPer-Share & Dividend")
    print(f"  Earnings Per Share       : {row['earnings_per_share']:.2f}")
    print(f"  Book Value Per Share     : {row['book_value_per_share']:.4f}")
    print(f"  Dividend Payout Ratio    : {row['dividend_payout_ratio_pct']:.2f}%")

    print("\n5-Year Growth")

    revenue = row["revenue_cagr_5yr"]
    pat = row["pat_cagr_5yr"]
    eps = row["eps_cagr_5yr"]

    print(f"  Revenue CAGR             : {revenue:.2f}%" if revenue is not None else "  Revenue CAGR             : N/A")
    print(f"  PAT CAGR                 : {pat:.2f}%" if pat is not None else "  PAT CAGR                 : N/A")
    print(f"  EPS CAGR                 : {eps:.2f}%" if eps is not None else "  EPS CAGR                 : N/A")

    score = row["composite_quality_score"]
    print(f"\n  Composite Quality Score  : {score:.2f}" if score is not None
          else "\n  Composite Quality Score  : N/A")

print("\n" + "=" * 90)
print("END OF DAY 14 FINANCIAL RATIOS DEMO")
print("=" * 90)

conn.close()

