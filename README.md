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
