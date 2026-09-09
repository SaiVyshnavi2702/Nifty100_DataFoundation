# Nifty 100 Data Foundation

This project is the data foundation for a Nifty 100 financial analytics system. The main objective of Sprint 1 was to collect the source Excel files, clean and normalise the data, validate the datasets, and load the final data into a SQLite database.

The project also includes data quality checks so that problems with primary keys, foreign keys, duplicate records, financial calculations, and other data issues can be identified before the data is used for further analysis.

## Sprint 1

Sprint 1 focused on building the complete data foundation from Day 01 to Day 07.

### Day 01 – Environment Setup

The project structure and Python virtual environment were created first. Required libraries were installed and the basic project configuration was added.

### Day 02 – Excel Loader and Normalisation

The Excel files were loaded using Pandas and common fields were normalised.

The normalisation work includes:

* Year normalisation
* Company/ticker normalisation
* Column-name normalisation
* Removing unnecessary spaces from values
* Handling Excel files with different header positions

Unit tests were also added for the normalisation functions.

### Day 03 – Schema Validation

A schema validator was implemented with 16 data quality rules.

The rules check areas such as:

* Primary key problems
* Duplicate records
* Missing company IDs
* Invalid company references
* Invalid years
* Duplicate company-year records
* Numeric values
* Sales and profit calculations
* Balance sheet consistency
* Cash flow consistency
* Stock price validation
* Financial ratio sanity checks

Validation results are written to `validation_failures.csv`.

### Day 04 – SQLite Database Schema

A SQLite database schema was created for the Nifty 100 datasets.

The database uses primary keys, foreign keys, unique constraints and indexes where required.

SQLite foreign-key enforcement is enabled using:

```sql
PRAGMA foreign_keys = ON;
```

### Day 05 – Full Data Load

The Excel datasets were loaded into SQLite using the ETL loader.

The loader handles:

1. Reading the Excel files
2. Cleaning column names
3. Normalising common fields
4. Loading the company master table first
5. Loading dependent tables after the company table
6. Removing duplicate company-year records where required
7. Checking the database schema
8. Checking foreign-key integrity
9. Printing table row counts after loading

The main expected dataset sizes include:

| Table         | Approximate Rows |
| ------------- | ---------------: |
| companies     |               100|
| profitandloss |            1,263 |
| balancesheet  |            1,225 |
| cashflow      |            1,152 |
| stock_prices  |            5,520 |

### Day 06 – Data Quality Manual Review

A manual review was performed on selected companies and year coverage.

The review was used to check whether the loaded records were consistent with the source data and to identify issues that needed to be fixed in the loader or source data.

### Day 07 – Sprint Review

The final verification included database checks, exploratory SQL queries, unit tests and documentation of the Sprint 1 work.

## Database Tables

The SQLite database contains the following tables:

* `companies`
* `profitandloss`
* `balancesheet`
* `cashflow`
* `analysis`
* `documents`
* `prosandcons`
* `sectors`
* `stock_prices`
* `financial_ratios`
* `market_cap`
* `peer_groups`

## Project Structure

```text
Nifty100_DataFoundation/
│
├── data/
│   ├── raw/
│   │   ├── core/
│   │   └── supporting/
│   ├── processed/
│   └── nifty100.db
│
├── db/
│
├── docs/
│   ├── day_07_verification.md
│   ├── day06_data_quality_review.md
│   └── sprint_1_retrospective.md
│
├── notebooks/
│   └── exploratory_queries.sql
│
├── output/
│   ├── load_audit.csv
│   └── validation_failures.csv
│
├── src/
│   ├── db/
│   │   └── schema.sql
│   │
│   └── etl/
│       ├── loader.py
│       ├── normaliser.py
│       └── validator.py
│
├── tests/
│   └── etl/
│       └── test_normaliser.py
│
├── .env
├── .gitignore
├── Makefile
├── requirements.txt
└── README.md
```

## ETL Components

### `normaliser.py`

Contains the common normalisation functions used by the project.

### `loader.py`

Responsible for loading the Excel source files into SQLite.

The loader also performs common cleaning and normalisation before inserting the data.

### `validator.py`

Runs the 16 data quality rules and generates the validation failure report.

### `schema.sql`

Contains the SQLite database structure, including tables, primary keys, foreign keys, constraints and indexes.

## Validation Output

The validation process generates:

```text
validation_failures.csv
```

The load process generates:

```text
output/load_audit.csv
```

The load audit records the number of rows loaded for each table and any rejected records.

## Exploratory SQL

Basic database verification and exploratory queries are stored in:

```text
notebooks/exploratory_queries.sql
```

These queries are used to check table counts, relationships, year coverage and sample financial records.

## Testing

The project includes unit tests for the ETL normalisation functions.

Tests can be executed using:

```powershell
pytest
```

## Running the ETL Loader

Activate the virtual environment first:

```powershell
.\.venv\Scripts\Activate.ps1
```

Then run:

```powershell
python .\src\etl\loader.py
```

The SQLite database is created at:

```text
data/nifty100.db
```

## Checking the Database

To check the tables:

```powershell
python -c "import sqlite3; c=sqlite3.connect('data/nifty100.db'); print(c.execute(\"SELECT name FROM sqlite_master WHERE type='table' ORDER BY name\").fetchall()); c.close()"
```

To check foreign-key violations:

```powershell
python -c "import sqlite3; c=sqlite3.connect('data/nifty100.db'); print(c.execute('PRAGMA foreign_key_check').fetchall()); c.close()"
```

An empty result means no foreign-key violations were found.

## Sprint 1 Outcome

Sprint 1 established the initial data foundation for the Nifty 100 analytics project.

The main outputs are:

* Cleaned and normalised source data
* SQLite database schema
* Loaded financial datasets
* Data quality validation
* Load audit report
* Validation failure report
* ETL scripts
* Unit tests
* Exploratory SQL queries
* Sprint documentation

The database and ETL layer will be used as the base for the next stages of the project, including financial analysis, reporting and dashboard development.


## Sprint 2 — Financial Ratio Engine

Sprint 2 focused on building the financial ratio and KPI engine for the Nifty 100 analytics project. The main objective was to calculate financial ratios consistently across companies and available financial years and store the results in the SQLite database.

Day 08–09 — Profitability, Leverage and Efficiency Ratios

The ratio engine was developed to calculate key profitability, leverage and efficiency metrics, including:

Net Profit Margin
Operating Profit Margin
Return on Equity (ROE)
Return on Capital Employed (ROCE)
Return on Assets (ROA)
Debt-to-Equity (D/E)
Interest Coverage Ratio (ICR)
Net Debt
Asset Turnover

The calculations include handling for zero denominators, negative equity and debt-free companies. Debt-free companies are represented with a D/E value of 0 and an appropriate ICR display label.

Special handling was also added for companies in the Financials sector because high leverage is structurally common in banks, NBFCs and insurance companies.

Day 10 — CAGR Engine

A CAGR engine was added to calculate growth rates for revenue, net profit and EPS over different time periods.

The implementation also handles cases where the starting value is zero or negative, where the company has insufficient historical data, and where the business changes from profit to loss or loss to profit. These cases are recorded using appropriate flags instead of producing misleading CAGR values.

Day 11 — Cash Flow and Capital Allocation

Cash-flow based KPIs were added, including Free Cash Flow, CFO quality, CapEx intensity and FCF conversion.

Companies were also classified into capital allocation patterns based on their operating, investing and financing cash flows. The capital allocation results were exported to:

output/capital_allocation.csv

Day 12–13 — Ratio Table and Edge Cases

The calculated KPIs were populated into the financial_ratios SQLite table for the available company-year data.

Additional checks were performed by comparing calculated ROE and ROCE values with the source values. Differences and unusual source values were documented in the ratio edge-case log.

The ratio engine uses the calculated values for analytics while source values are retained where required for display purposes.

Day 14 — Testing and Review

The financial ratio calculations were tested using unit tests covering normal calculations and important edge cases such as zero denominators, negative equity, debt-free companies and CAGR turnarounds.

The ratio engine and financial ratio table were reviewed before moving to the next sprint.

## Sprint 3 — Screener and Peer Comparison Engine

Sprint 3 focused on building the financial screener and peer comparison functionality on top of the financial ratio data created in Sprint 2.

Day 15–16 — Screener and Presets

A screener engine was developed to filter companies using financial metrics such as ROE, D/E, FCF, Revenue CAGR, PAT CAGR, OPM, P/E, P/B, Dividend Yield and ICR.

Six preset screeners were implemented:

Quality Compounder
Value Pick
Growth Accelerator
Dividend Champion
Debt-Free Blue Chip
Turnaround Watch

The screener also handles Financials companies differently for D/E filtering because higher leverage is normal for this sector. Debt-free companies are also handled correctly for ICR filtering.

Day 17 — Composite Quality Score and Export

A composite quality score was implemented to provide an overall assessment of company quality using profitability, cash quality, growth and leverage metrics.

The screener results can be exported to Excel, with the results organised according to the different screening presets.

Day 18–20 — Peer Analysis

Peer-group analysis was implemented for the available peer groups. Companies are compared using financial metrics such as ROE, ROCE, Net Profit Margin, D/E, FCF, Revenue CAGR, PAT CAGR, EPS CAGR, Interest Coverage and Asset Turnover.

Percentile rankings were calculated within peer groups, with D/E treated as an inverse metric because lower leverage is generally better.

Peer comparison reports and radar-style comparisons were also prepared to make it easier to compare an individual company with its peer group.

Day 21 — Testing and Review

The screener and peer comparison functionality were tested using different filters, presets and peer groups. The results were checked to ensure that the filtering logic and percentile rankings behaved as expected.

The Sprint 3 work provided the foundation for the Streamlit dashboard screens developed in Sprint 4.




## Sprint 4 – Dashboard and Valuation

Sprint 4 focused on building and testing the Nifty 100 Analytics Streamlit dashboard. The dashboard has eight screens covering company information, screening, peer comparison, trends, sector analysis, capital allocation and annual reports.

How to Run the Dashboard

First, activate the virtual environment:

.\.venv\Scripts\Activate.ps1


Then start the Streamlit application:

streamlit run src/dashboard/app.py


The dashboard will open in the browser using the local Streamlit server.

Dashboard Screens

The dashboard contains eight screens:

Home – Shows the main Nifty 100 summary KPIs, year selection, sector breakdown and top companies based on the quality score.

Company Profile – Allows users to search for a company or ticker and view company details, financial metrics, Revenue and Net Profit charts, ROE and ROCE trends, and Pros and Cons.

Screener – Allows users to filter companies using financial metrics such as ROE, D/E, FCF, Revenue CAGR, P/E, P/B and other indicators. Preset filters and CSV export are also available.

Peer Comparison – Compares companies within a peer group using financial KPIs and a radar chart.

Trend Analysis – Allows users to select a company and view financial trends for up to three selected metrics.

Sector Analysis – Shows companies within a selected sector using a bubble chart and sector-level median KPIs.

Capital Allocation Map – Groups companies into different capital allocation patterns using a treemap and displays the companies belonging to each pattern.

Annual Reports – Allows users to search for a company and view available annual report years and report links.

Sprint 4 Testing and Findings

During integration testing, the dashboard was tested with companies from different sectors including IT, Financials, FMCG, Energy and Healthcare. Companies with partial financial data were also tested to make sure the pages loaded without crashing.

When financial values are missing, the dashboard displays N/A instead of producing an error. For companies with fewer years of available data, a data-availability message is displayed.

One example was Zomato, where Revenue and Net Profit data was available but ROE and ROCE trend data was not available. The page handled the missing data without crashing.

The Screener was also tested with extreme minimum and maximum filter values to make sure it continued to work correctly.

Charts were checked at different browser widths to make sure they stayed within the page and did not cause horizontal overflow.

Company Profile load time was checked for five companies, and all tested load times were below the required three-second limit.

The detailed Day 27 QA results are stored in:

output/Day27_QA_Testing.xlsx

Valuation Module

The valuation module calculates FCF Yield and compares company P/E values with the sector median P/E.

Companies are classified as Caution, Discount or Fair based on the defined valuation rules.

The valuation results are generated as:

output/valuation_summary.xlsx
output/valuation_flags.csv

Sprint 4 Retrospective

During Sprint 4, the dashboard was kept simple and easy to use by using search boxes, dropdowns, KPI cards and interactive Plotly charts.

The main data-related issue found during testing was that some companies do not have a complete 10-year history. Instead of treating this as a system error, the dashboard displays the available data and informs the user when data is limited.

Some companies also have missing information such as sector details, company descriptions, ROE/ROCE values or Pros and Cons. These cases are handled with suitable unavailable-data messages or N/A values.

Overall, Sprint 4 completed the dashboard development, valuation work, integration testing, missing-data handling and performance checks required for the sprint.