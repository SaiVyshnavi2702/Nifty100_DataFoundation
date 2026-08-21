# Day 06 — Data Quality Manual Review



## Objective



Reviewed the loaded financial data manually to check year coverage, missing data, duplicate records, and possible loader issues.



## 1. Random Company Review



I randomly selected and reviewed these 5 companies:



\- ADANIPOWER

\- RELIANCE

\- MOTHERSON

\- CIPLA

\- PNB



I checked their Balance Sheet, Profit \& Loss, and Cash Flow year coverage.



The sample companies had consistent historical data from 2013 through 2024, with TTM records also present in P\&L where applicable.



## 2. Overall Year Coverage



Current database coverage:



| Table | Year Coverage | Companies | Rows |

|---|---|---:|---:|

| Balance Sheet | 2011–2024 | 98 | 1,225 |

| Profit \& Loss | 2011–2024 + TTM | 100 | 1,263 |

| Cash Flow | 2011–2024 | 100 | 1,152 |



## 3. Companies With Less Than 5 Years of Data



I checked for companies having fewer than 5 financial years.



Only one company was found:



\- \*\*JIOFIN — 2 completed financial years (2023 to 2024)\*\*



I checked JIOFIN against the original Excel files and found that the source itself only contains:



\- Balance Sheet: Mar 2023, Mar 2024, Sep 2024

\- Profit \& Loss: Mar 2023, Mar 2024, TTM

\- Cash Flow: Mar 2023, Mar 2024



The database contains the same records, so this is a source-data limitation and not a loader issue.



## 4. Missing Balance Sheet Data



The database contains Balance Sheet data for 98 of the 100 companies.



The two companies without Balance Sheet records are:



\- \*\*SBIN — State Bank of India\*\*

\- \*\*VBL — Varun Beverages Ltd\*\*



I checked the original `balancesheet.xlsx` file and confirmed that both companies also have 0 rows in the source file.



Therefore, these missing records were not caused by the loader.



## 5. Duplicate Record Check



I checked for duplicate `(company\_id, period)` combinations.



Results:



\- Balance Sheet: 0 duplicates

\- Profit \& Loss: 0 duplicates

\- Cash Flow: 0 duplicates



No duplicate financial records were found.



## 6. Foreign Key Check



Foreign keys were enabled and checked again.



Result:



\- Foreign keys: Enabled

\- Foreign key violations: 0


## 7. Loader Review



I reviewed the loader after completing the manual checks.



No loader bug was found during this review, so no unnecessary changes were made to the loader.



## Conclusion



Day 06 data-quality review completed.



The main data gaps found were JIOFIN's limited history and missing Balance Sheet data for SBIN and VBL.



