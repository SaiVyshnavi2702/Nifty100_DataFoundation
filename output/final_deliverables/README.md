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


Nifty100_DataFoundation/
│
├── config/
│   └── screener_config.yaml
│
├── data/
│   ├── nifty100.db
│   └── raw/
│       ├── core/
│       └── supporting/
│
├── docs/
│   ├── openapi.json
│   ├── nifty100_postman_collection.json
│   ├── verification documents
│   ├── sprint retrospectives
│   └── analyst_guide.pdf
│
├── notebooks/
│   └── exploratory_queries.sql
│
├── output/
│   ├── NLP outputs
│   ├── cash-flow intelligence
│   ├── clustering outputs
│   ├── screener and valuation outputs
│   ├── QA and validation outputs
│   └── final_deliverables/
│
├── reports/
│   ├── portfolio/
│   ├── radar_charts/
│   ├── sector/
│   ├── tearsheets/
│   ├── correlation_heatmap.png
│   ├── elbow_plot.png
│   └── pytest_report.html
│
├── src/
│   ├── analytics/
│   │   ├── CAGR analysis
│   │   ├── financial ratios
│   │   ├── cash-flow intelligence
│   │   ├── capital allocation
│   │   ├── clustering
│   │   ├── peer analysis
│   │   ├── quality scoring
│   │   ├── screener
│   │   └── valuation
│   │
│   ├── api/
│   │   ├── main.py
│   │   └── routers/
│   │
│   ├── dashboard/
│   │   ├── app.py
│   │   ├── pages/
│   │   │   ├── 01_home.py
│   │   │   ├── 02_profile.py
│   │   │   ├── 03_screener.py
│   │   │   ├── 04_peers.py
│   │   │   ├── 05_trends.py
│   │   │   ├── 06_sectors.py
│   │   │   ├── 07_capital.py
│   │   │   └── 08_reports.py
│   │   └── utils/
│   │
│   ├── db/
│   │   ├── schema.sql
│   │   └── database utilities
│   │
│   ├── etl/
│   │   ├── normaliser.py
│   │   ├── validator.py
│   │   └── loader.py
│   │
│   ├── nlp/
│   │   ├── parser.py
│   │   ├── cagr_validation.py
│   │   └── pros_cons_generator.py
│   │
│   ├── reports/
│   │   ├── tearsheet.py
│   │   ├── batch_reports.py
│   │   ├── sector_reports.py
│   │   └── portfolio_summary.py
│   │
│   └── screener/
│       ├── engine.py
│       ├── presets.py
│       ├── composite_score.py
│       └── export.py
│
├── tests/
│   ├── api/
│   ├── dq/
│   ├── etl/
│   ├── kpi/
│   └── performance/
│
├── README.md
├── requirements.txt
├── pytest.ini
└── Makefile


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


validation_failures.csv


The load process generates:


output/load_audit.csv


The load audit records the number of rows loaded for each table and any rejected records.

## Exploratory SQL

Basic database verification and exploratory queries are stored in:


notebooks/exploratory_queries.sql


These queries are used to check table counts, relationships, year coverage and sample financial records.

## Testing

The project includes unit tests for the ETL normalisation functions.

Tests can be executed using:

pytest

## Running the ETL Loader

Activate the virtual environment first:


.\.venv\Scripts\Activate.ps1


Then run:

python .\src\etl\loader.py


The SQLite database is created at:


data/nifty100.db


## Checking the Database

To check the tables:

python -c "import sqlite3; c=sqlite3.connect('data/nifty100.db'); print(c.execute(\"SELECT name FROM sqlite_master WHERE type='table' ORDER BY name\").fetchall()); c.close()"


To check foreign-key violations:


python -c "import sqlite3; c=sqlite3.connect('data/nifty100.db'); print(c.execute('PRAGMA foreign_key_check').fetchall()); c.close()"


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

## Day 08–09 — Profitability, Leverage and Efficiency Ratios

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

## Day 10 — CAGR Engine

A CAGR engine was added to calculate growth rates for revenue, net profit and EPS over different time periods.

The implementation also handles cases where the starting value is zero or negative, where the company has insufficient historical data, and where the business changes from profit to loss or loss to profit. These cases are recorded using appropriate flags instead of producing misleading CAGR values.

## Day 11 — Cash Flow and Capital Allocation

Cash-flow based KPIs were added, including Free Cash Flow, CFO quality, CapEx intensity and FCF conversion.

Companies were also classified into capital allocation patterns based on their operating, investing and financing cash flows. The capital allocation results were exported to:

output/capital_allocation.csv

## Day 12–13 — Ratio Table and Edge Cases

The calculated KPIs were populated into the financial_ratios SQLite table for the available company-year data.

Additional checks were performed by comparing calculated ROE and ROCE values with the source values. Differences and unusual source values were documented in the ratio edge-case log.

The ratio engine uses the calculated values for analytics while source values are retained where required for display purposes.

## Day 14 — Testing and Review

The financial ratio calculations were tested using unit tests covering normal calculations and important edge cases such as zero denominators, negative equity, debt-free companies and CAGR turnarounds.

The ratio engine and financial ratio table were reviewed before moving to the next sprint.

## Sprint 3 — Screener and Peer Comparison Engine

Sprint 3 focused on building the financial screener and peer comparison functionality on top of the financial ratio data created in Sprint 2.

## Day 15–16 — Screener and Presets

A screener engine was developed to filter companies using financial metrics such as ROE, D/E, FCF, Revenue CAGR, PAT CAGR, OPM, P/E, P/B, Dividend Yield and ICR.

Six preset screeners were implemented:

Quality Compounder
Value Pick
Growth Accelerator
Dividend Champion
Debt-Free Blue Chip
Turnaround Watch

The screener also handles Financials companies differently for D/E filtering because higher leverage is normal for this sector. Debt-free companies are also handled correctly for ICR filtering.

## Day 17 — Composite Quality Score and Export

A composite quality score was implemented to provide an overall assessment of company quality using profitability, cash quality, growth and leverage metrics.

The screener results can be exported to Excel, with the results organised according to the different screening presets.

## Day 18–20 — Peer Analysis

Peer-group analysis was implemented for the available peer groups. Companies are compared using financial metrics such as ROE, ROCE, Net Profit Margin, D/E, FCF, Revenue CAGR, PAT CAGR, EPS CAGR, Interest Coverage and Asset Turnover.

Percentile rankings were calculated within peer groups, with D/E treated as an inverse metric because lower leverage is generally better.

Peer comparison reports and radar-style comparisons were also prepared to make it easier to compare an individual company with its peer group.

## Day 21 — Testing and Review

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

## Sprint 4 Testing and Findings

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

## Sprint 4 Retrospective

During Sprint 4, the dashboard was kept simple and easy to use by using search boxes, dropdowns, KPI cards and interactive Plotly charts.

The main data-related issue found during testing was that some companies do not have a complete 10-year history. Instead of treating this as a system error, the dashboard displays the available data and informs the user when data is limited.

Some companies also have missing information such as sector details, company descriptions, ROE/ROCE values or Pros and Cons. These cases are handled with suitable unavailable-data messages or N/A values.

Overall, Sprint 4 completed the dashboard development, valuation work, integration testing, missing-data handling and performance checks required for the sprint.

## Sprint 5 – Intelligence, NLP and PDF Reports

Sprint 5 focused on adding intelligence, NLP based analysis and automated PDF reporting to the Nifty 100 Data Foundation project.

The main objective was to convert the financial data and calculated KPIs into useful company level insights, cash flow intelligence and readable reports.

## Day 29 – NLP Parser

An NLP parser was developed to extract financial performance metrics from the analysis data.

The parser handles metrics including:

Compounded Sales Growth

Compounded Profit Growth

Stock Price CAGR

ROE

Regular expression based parsing was used to identify year periods and percentage values.

The parsed results are stored in:

output/analysis_parsed.csv

Parsing failures are recorded separately in:

output/parse_failures.csv

The parsed values were also compared with the Ratio Engine results, with significant differences identified for further review.

## Day 30 – Automatic Pros and Cons Generator

A rule based Pros and Cons generator was implemented to automatically generate company level financial insights.

The generator uses financial metrics and defined rules to identify positive and negative characteristics.

Each generated insight receives a confidence score. Only insights meeting the defined confidence threshold are included in the final output.

The results are stored in:

output/pros_cons_generated.csv

## Day 31 – Cash Flow Intelligence

Cash Flow Intelligence was implemented to analyse company cash flow quality.

The analysis includes:

CFO to PAT analysis

CFO quality classification

CapEx intensity

Capital allocation behaviour

Cash flow distress indicators

Deleveraging indicators

The main output is:

output/cashflow_intelligence.xlsx

Potential distress cases are also recorded in:

output/distress_alerts.csv

## Day 32 – Capital Allocation Report

Capital allocation patterns were verified across the available company data.

The analysis classifies companies based on operating, investing and financing cash flow behaviour.

Pattern changes across years were also tracked.

The main output is:

output/capital_allocation.csv

## Day 33 – Company PDF Tearsheet

A ReportLab based company tearsheet generator was developed.

Each company tearsheet is designed as a two page A4 report containing:

Company header and ticker

KPI cards

Revenue and Net Profit charts

ROE and ROCE trends

Balance sheet composition

Cash flow information

Pros and Cons

Capital allocation information

The generator also handles missing values using N/A and applies word wrapping to reduce PDF layout problems.

The main generator is:

src/reports/tearsheet.py

Standard test companies included:

TCS

HDFCBANK

RELIANCE

SUNPHARMA

TATASTEEL

## Day 34 – Batch Company and Sector Reports

The company report generation process was automated so that tearsheets could be generated in batch for eligible companies.

Companies with insufficient historical data can be recorded in:

output/skipped_tearsheets.csv

Sector level reports were also created using sector level KPI summaries and individual company metrics.

The sector reports are stored under:

reports/sector/

## Day 35 – Portfolio Summary and Sprint Review

A portfolio summary PDF was generated to bring company level KPI information together in a single report.

KPI trend indicators were also added to show whether the latest annual values improved, declined or remained relatively flat compared with the previous year.

Sample company, sector and portfolio reports were visually reviewed for:

Text overflow

Unexpected blank pages

Missing content

Incorrect layouts

Readability of charts and tables

The Sprint 5 retrospective is stored at:

reports/sprint5_retrospective.md

## Sprint 5 Outcome

Sprint 5 added an intelligence and reporting layer on top of the financial analytics system.

The sprint produced:

NLP based financial metric parsing

Automated Pros and Cons generation

Confidence based financial insights

Cash Flow Intelligence

Capital allocation analysis

Automated company tearsheets

Sector reports

Portfolio summary reporting

KPI trend indicators

PDF visual validation

The project was extended from financial data processing into automated financial analysis and report generation.

## Sprint 6 – Clustering, REST API, QA and Sign Off

Sprint 6 focused on company clustering, REST API development, automated testing, performance checks, documentation and final project validation.

The sprint connected the financial analytics and reporting components into a reusable API based system and added company archetype clustering.

## Day 36 – Company Clustering

A KMeans clustering model was implemented using company level financial features.

The clustering features include:

ROE

Debt-to-Equity

Revenue CAGR

FCF CAGR

Operating Profit Margin

Missing feature values were handled using sector median imputation.

The features were standardised using StandardScaler before applying KMeans.

The clustering configuration uses five clusters with a fixed random state for reproducibility.

Cluster assignments are stored in:

output/cluster_labels.csv

The cluster analysis also includes:

output/cluster_profile.csv
reports/elbow_plot.png

## Day 37 – Cluster Profiling and Portfolio Statistics

The five clusters were profiled using their financial characteristics.

The project uses the following cluster labels:

Diversified Core Companies

Growth and High Margin Leaders

Leveraged Financials

High Margin Defensive

Strategic Industrials

Additional analysis outputs include:

reports/correlation_heatmap.png
output/outlier_report.csv
output/portfolio_stats.csv

The correlation heatmap was used to understand relationships between the clustering features.

The outlier report identifies companies with unusual financial feature values.

Portfolio statistics provide summary information for the overall company dataset and cluster level analysis.

## Day 38 – FastAPI Application

A FastAPI application was created to expose the project data and analytics through REST endpoints.

The API includes separate routers for:

Companies

Screener

Sectors

Peers

Valuation

Portfolio

Documents

Health

The API uses the versioned base path:

/api/v1/

The health endpoint is:

/api/v1/health

CORS support and request logging were also added.

## Day 39 – Company API Endpoints

Company related API endpoints were implemented for accessing company information and financial data.

The endpoints include:

GET /api/v1/companies
GET /api/v1/companies/{ticker}
GET /api/v1/companies/{ticker}/pl
GET /api/v1/companies/{ticker}/bs
GET /api/v1/companies/{ticker}/cashflow
GET /api/v1/companies/{ticker}/ratios
GET /api/v1/companies/{ticker}/tearsheet

These endpoints provide access to company profiles, financial statements, ratios and generated tearsheets.

## Day 40 – Additional API Endpoints

Additional endpoints were implemented for screening, sectors, peer comparison, market capitalisation, portfolio statistics and company documents.

The endpoints include:

GET /api/v1/screener
GET /api/v1/sectors
GET /api/v1/sectors/{sector}/companies
GET /api/v1/peers/{group_name}
GET /api/v1/companies/{ticker}/peers/compare
GET /api/v1/market-cap/{ticker}
GET /api/v1/portfolio/stats
GET /api/v1/companies/{ticker}/documents

The complete OpenAPI specification is stored in:

docs/openapi.json

A Postman collection is also available at:

docs/nifty100_postman_collection.json

The project currently maps companies across 10 broad sectors in the database.

## Day 41 – Test Suite Expansion

Tests were expanded across the ETL, KPI and data quality components.

The test coverage includes:

20 normalisation tests

10 loader tests

20 financial ratio tests

14 data quality rule tests

API and integration tests were also added during the sprint.

## Day 42 – API and Integration Testing

API tests were created for:

Health endpoint

Company endpoints

Screener

Sector endpoints

Integration behaviour

The generated test report is stored at:

reports/pytest_report.html

The complete project test suite was expanded to cover the major ETL, analytics, API and integration components.

## Day 43 – Performance and Database Optimisation

Performance testing was performed for API screener requests and company profile data loading.

Ten concurrent screener requests completed successfully with all requests returning HTTP 200.

Company Profile data loading was also benchmarked using:

TCS

HDFCBANK

RELIANCE

SUNPHARMA

TATASTEEL

Database indexes were added to improve queries involving company and financial year combinations.

Indexes were added for:

financial_ratios

profitandloss

balancesheet

cashflow

The performance notes are stored in:

output/perf_notes.md

The FastAPI API and Streamlit dashboard were also tested while running simultaneously on their respective local ports.

## Day 44 – Documentation and Code Quality

Public functions across the project were checked for docstrings.

The final verification reported:

TOTAL MISSING DOCSTRINGS: 0

Black formatting was applied and verified.

Ruff code quality checks were also completed successfully.

Final checks included:

python -m ruff check src/ tests/
python -m black --check src/ tests/

The final Black check confirmed that the project files were already formatted.

The complete test suite produced:

179 passed
0 failed
1 warning

The warning was a third party Starlette and httpx deprecation warning and did not result in a project test failure.

## Day 45 – Final Verification

The final sprint verification covers the main project acceptance areas, including:

Company count validation

Historical financial data coverage

Foreign key integrity

Financial ratio coverage

CAGR verification

ROE verification

Screener validation

Company Profile performance

Screener CSV validation

PDF tearsheet validation

API health validation

Company ratio endpoint validation

API and screener consistency

Peer percentile validation

Company clustering

Pros and Cons generation

Company tearsheets

Automated test results

Validation failure report

Analyst documentation

The final acceptance checklist is intended to record the status of each acceptance gate along with team lead sign off.

## Sprint 6 Main Deliverables

The major Sprint 6 deliverables include:

output/cluster_labels.csv
output/cluster_profile.csv
output/outlier_report.csv
output/portfolio_stats.csv
reports/elbow_plot.png
reports/correlation_heatmap.png
src/api/
docs/openapi.json
docs/nifty100_postman_collection.json
reports/pytest_report.html
output/perf_notes.md
docs/analyst_guide.pdf

## Sprint 6 Outcome

Sprint 6 extended the project with company clustering, REST API access, automated testing, performance optimisation and final documentation.

The project now provides a complete workflow from raw financial data and validation through financial analytics, screening, dashboard visualisation, company intelligence, PDF reporting, clustering and API access.

# Final Project Usage Guide

## Project Overview

The Nifty 100 Data Foundation project provides the data, analytics, dashboard, API and reporting components for a Nifty 100 financial analytics system.

The project covers the complete workflow from data loading and validation to financial analysis and presentation. It includes:

- Excel data ingestion and normalisation
- SQLite database storage
- Data quality validation
- Financial ratios and KPIs
- CAGR and cash-flow analysis
- Screener and screening presets
- Peer comparison
- Valuation analysis
- Company clustering and portfolio analytics
- Streamlit dashboard
- FastAPI REST API
- Company PDF tearsheets
- Annual report access
- Automated testing and performance checks

The main database is stored at:


data/nifty100.db


## Setup

Open PowerShell in the project directory and activate the virtual environment:


cd D:\Nifty100_DataFoundation
.\.venv\Scripts\Activate.ps1


If the dependencies have not been installed yet:


pip install -r requirements.txt


The project was developed and tested using Python 3.14.



## Running the ETL

The ETL loader reads the source Excel files, normalises the data, validates the datasets and loads them into the SQLite database.

Run:


python .\src\etl\loader.py


The database is created or updated at:


data/nifty100.db


The main ETL files are:

- `src/etl/normaliser.py` — data normalisation
- `src/etl/loader.py` — Excel and database loading
- `src/etl/validator.py` — data quality validation



## Running the Dashboard

The project contains eight Streamlit dashboard screens:

1. **Home** — Nifty 100 summary, sector breakdown and top companies
2. **Company Profile** — company information, financial metrics, trends and Pros and Cons
3. **Screener** — financial, growth, valuation, dividend and debt-based filtering
4. **Peer Comparison** — comparison of companies within peer groups
5. **Trend Analysis** — financial trends for selected companies and metrics
6. **Sector Analysis** — sector-level company and KPI analysis
7. **Capital Allocation Map** — capital allocation patterns and company groups
8. **Annual Reports** — available annual reports for selected companies

Because the dashboard pages use imports from the `dashboard` package, set the `src` directory in `PYTHONPATH` before starting Streamlit:


$env:PYTHONPATH="$PWD\src"
streamlit run src/dashboard/app.py --server.port 8501


The dashboard is available at:


http://127.0.0.1:8501


### Screener

The Screener allows users to filter companies using:

- ROE
- Debt-to-Equity
- Free Cash Flow
- Revenue CAGR
- PAT CAGR
- Operating Profit Margin
- P/E
- P/B
- Dividend Yield
- Interest Coverage Ratio

Six presets are available:

- Quality
- Value
- Growth
- Dividend
- Debt-Free
- Turnaround

Filtered results can be downloaded as a CSV file named:


nifty100_screening_results.csv


### Annual Reports

The Annual Reports screen allows users to select a company and access the available annual report links.

This screen provides access to source annual reports. It is separate from the company PDF tearsheet generation described below.



## Running the FastAPI

The project provides a REST API for accessing company information, financial data, screening results, sectors, peer comparisons, valuation information, portfolio statistics and documents.

Start the API with:

uvicorn src.api.main:app --host 127.0.0.1 --port 8000


The API runs at:


http://127.0.0.1:8000


Interactive Swagger documentation is available at:


http://127.0.0.1:8000/docs


The OpenAPI specification and Postman collection are stored in:


docs/openapi.json
docs/nifty100_postman_collection.json


### API Examples

Check the API health:


curl http://127.0.0.1:8000/api/v1/health


Get the available companies:

curl http://127.0.0.1:8000/api/v1/companies


Get a specific company:


curl http://127.0.0.1:8000/api/v1/companies/TCS


Get financial ratios:


curl http://127.0.0.1:8000/api/v1/companies/TCS/ratios


Run a screener using a minimum ROE of 15%:


curl "http://127.0.0.1:8000/api/v1/screener?min_roe=15"


Get the available sectors:


curl http://127.0.0.1:8000/api/v1/sectors


Get companies from the Information Technology sector:


curl "http://127.0.0.1:8000/api/v1/sectors/Information%20Technology/companies"


## Generating Company PDF Tearsheets

The project includes a ReportLab-based PDF tearsheet generator. Each company tearsheet is designed as a two-page A4 report containing key financial and analytical information.

The generator is located at:


src/reports/tearsheet.py


To generate the standard test tearsheets:


python -m src.reports.tearsheet


The generated files are saved in:


reports/tearsheets


The standard test companies are:

- TCS
- HDFCBANK
- RELIANCE
- SUNPHARMA
- TATASTEEL

The reports include company information, KPI cards, Revenue and Net Profit charts, ROE and ROCE trends, balance-sheet composition, cash-flow information, Pros and Cons and capital allocation information.

For batch generation:


python -m src.reports.batch_reports


If any companies are skipped during batch generation, they are recorded in:


output/skipped_tearsheets.csv

## Testing

The project includes tests for ETL processing, financial calculations, data quality rules, API endpoints, dashboard/API integration, and performance.

Run the complete test suite:

pytest tests\ -v

The current test suite contains 179 tests, all of which pass successfully.

To generate an HTML test report:

pytest tests/ --html=reports/pytest_report.html

The report is saved at:

reports/pytest_report.html

Performance testing and database optimisation notes are documented in:

output/perf_notes.md

## Troubleshooting

### Streamlit import error

If Streamlit shows:

ModuleNotFoundError: No module named 'dashboard'

Set the src directory in PYTHONPATH:

$env:PYTHONPATH="$PWD\src"

Then restart Streamlit:

streamlit run src/dashboard/app.py --server.port 8501

### Port already in use

If port 8000 or 8501 is already being used, stop the running application with:

Ctrl+C

Then start the required service again.

### Database error

Make sure the SQLite database exists at:

data/nifty100.db

If the database needs to be created or reloaded, run:

python .\src\etl\loader.py

### Missing values

Some companies have incomplete historical data or missing source information. The dashboard displays available values and uses N/A or an appropriate availability message when data is not available.

### PDF tearsheet not generated

Make sure the database is available and contains the required company data.

Generate the standard company tearsheets with:

python -m src.reports.tearsheet

Generated files are saved in:

reports/tearsheets

### Batch PDF generation

To generate tearsheets for the available companies in batch:

python -m src.reports.batch_reports

Companies that cannot be generated are recorded in:

output/skipped_tearsheets.csv

## Documentation and Final Deliverables

The project includes an analyst guide covering dashboard usage, screening, reports, API usage, and troubleshooting.

The guide will be stored at:

docs/analyst_guide.pdf

Final project deliverables are archived under:

output/final_deliverables/

The project also includes public-function docstrings and has completed the final Black and Ruff code-quality checks.



