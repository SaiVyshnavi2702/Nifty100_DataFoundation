Sprint 2 Retrospective — Financial Ratios & Day 14 Review



## Sprint Summary



Sprint 2 focused on completing and reviewing the financial ratio calculation and screening workflow for the Nifty 100 Data Foundation.



During this sprint, the KPI formulas were implemented and tested using the financial data available in the project. The edge cases were reviewed and logged, and the Day 14 screening process was also completed.



The final automated test run was successful, with 111 tests passed and 0 failures.



## Formula Decisions



1. Return on Equity (ROE)



ROE is calculated using the following formula:



ROE = Net Profit / Total Equity × 100



Total Equity is calculated as:



Total Equity = Equity Capital + Reserves



The calculation uses the equity capital and reserves values available in the database. If the required values are missing or total equity is not positive, the ROE value is treated as unavailable.



2. Return on Capital Employed (ROCE)



ROCE is calculated as:



ROCE = EBIT / Capital Employed × 100



EBIT is calculated as:



EBIT = Operating Profit + Other Income



Capital Employed is calculated as:



Capital Employed = Equity Capital + Reserves + Borrowings



If any required input is missing or capital employed is not positive, the ROCE value is treated as unavailable.



3. Debt-to-Equity



Debt-to-Equity is calculated using borrowings and total equity:



D/E = Borrowings / (Equity Capital + Reserves)



## Other KPIs



The ratio engine also calculates other financial indicators covering profitability, interest coverage, asset efficiency, cash flow, per-share values, dividend payout, and growth. These calculations use the corresponding financial values stored in the database.



## Edge-Case Review



The generated output/ratio_edge_cases.log file was reviewed as part of the Day 14 checks.



The log contains:



42 total ratio edge cases

36 ROCE anomalies

18 ROE anomalies



The identified cases were grouped into the following categories:



VERSION_DIFFERENCE

FORMULA_DISCREPANCY

DATA_SOURCE_ISSUE



These cases were documented instead of being ignored. The main approach was to keep the defined ratio-engine formulas consistent while separately identifying differences caused by formula versions or source-data issues.



Some companies also show unusually high ROE values because their equity value is very small. These cases need to be looked at along with the underlying balance-sheet values rather than automatically being considered calculation errors.



## Screener Review



The Day 14 fundamental screener uses the following criteria:



ROE > 15%

Debt-to-Equity < 1

Interest Coverage ≥ 3

Revenue CAGR (5Y) ≥ 10%

PAT CAGR (5Y) ≥ 10%

EPS CAGR (5Y) ≥ 10%



The complete screener produced the following results:



91 companies evaluated

15 PASS

66 FAIL

10 INSUFFICIENT DATA



A separate check was also performed using the main quick-filter conditions of ROE > 15% and D/E < 1.



This check returned 37 companies, which is within the required range of 15–50 companies.



The quick-filter returned 37 companies, which is within the required 15–50 range. The result provides a manageable candidate set for further fundamental analysis.



## Demo Data



For the planned team-lead demo, I identified five companies from the financial_ratios table using the latest annual March 2024 data:

ABB
ADANIENSOL
ADANIENT
ADANIGREEN
ADANIPORTS
The financial_ratios table contains the calculated profitability, leverage, interest coverage, efficiency, cash-flow, per-share, growth, and composite-score KPIs.

The planned demo will use these five companies to show the computed KPI values and explain how the different metrics work together. For example, a company may have strong revenue or profit growth but still fail the overall screen because of high debt or weak interest coverage.

The five-company financial_ratios demo is still pending and will be presented to the team lead once the review meeting is scheduled.



## What Went Well

* The KPI formulas were implemented centrally and covered by automated tests.
* The final test run completed with 111 passed and 0 failures.
* Edge cases were recorded with clear categories.
* Missing data is marked as INSUFFICIENT_DATA instead of being treated as a passing result.
* The screener produces a manageable number of companies for further review.
* Latest annual data can be retrieved consistently from the financial_ratios table.



## Lessons and Improvements

* Formula definitions and source-data conventions should be documented clearly whenever the data is refreshed.
* Unusually high ratios should be checked against the underlying financial values before drawing conclusions.
* Screening thresholds should remain separate from the KPI calculation formulas so that the screening rules can be changed independently.
* Future demonstrations should use one latest annual row per company to keep the demo clear and avoid showing unnecessary historical records.



## Sprint 2 Outcome
Overall, Sprint 2 successfully completed the financial-ratio calculation, testing, edge-case review, and fundamental screening workflow.

The project now has a tested ratio engine, documented edge-case handling, a working fundamental screener, and a usable financial_ratios dataset for demonstration.

The remaining Sprint 2 activity is the team-lead demo of the financial_ratios table. The demo will cover five companies and their computed KPIs once the review meeting is scheduled.

Final automated test result: 111 passed, 0 failures.

