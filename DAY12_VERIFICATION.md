# Day 12 - Financial Ratios Verification

## Overview

As part of Day 12, the financial ratios table was populated using the
ratio calculation service.

The database was then manually spot-checked for three companies:

- RELIANCE
- INDIGO
- TRENT

For each company, I manually verified:

1. Return on Equity (ROE)
2. 5-year Revenue CAGR

The manually calculated values were compared with the corresponding
values stored in the `financial_ratios` table.



## 1. ROE Verification

### Formula

ROE = Net Profit / (Equity Capital + Reserves) × 100

### RELIANCE - 2024

Net Profit = 79,020

Equity Capital = 6,766

Reserves = 786,715

Manual calculation:

79,020 / (6,766 + 786,715) × 100

= 9.95865055%

Database value = 9.95865055%

Difference = 0.00000000%

Result: PASS



### INDIGO - 2024

Net Profit = 8,167

Equity Capital = 48

Reserves = 867

Manual calculation:

8,167 / (48 + 867) × 100

= 892.56830601%

Database value = 892.56830601%

Difference = 0.00000000%

Result: PASS



### TRENT - 2024

Net Profit = 1,477

Equity Capital = 36

Reserves = 4,032

Manual calculation:

1,477 / (36 + 4,032) × 100

= 36.30776794%

Database value = 36.30776794%

Difference = 0.00000000%

Result: PASS



## 2. 5-Year Revenue CAGR Verification

### Formula

5-Year Revenue CAGR =

((2024 Revenue / 2019 Revenue) ^ (1 / 5) - 1) × 100

### RELIANCE

2019 Revenue = 568,337

2024 Revenue = 899,041

Manual calculation:

((899,041 / 568,337) ^ (1 / 5) - 1) × 100

= 9.60609709%

Database value = 9.60609709%

Difference = 0.00000000%

Result: PASS


### INDIGO

2019 Revenue = 28,497

2024 Revenue = 68,904

Manual calculation:

((68,904 / 28,497) ^ (1 / 5) - 1) × 100

= 19.31335513%

Database value = 19.31335513%

Difference = 0.00000000%

Result: PASS



### TRENT

2019 Revenue = 2,630

2024 Revenue = 12,375

Manual calculation:

((12,375 / 2,630) ^ (1 / 5) - 1) × 100

= 36.30691600%

Database value = 36.30691600%

Difference = 0.00000000%

Result: PASS



## 3. Database Verification

The financial ratios table was checked after running the ratio engine.

Financial ratios rows: 1,161

Rows processed: 1,161

Rows with composite quality score: 581

The required minimum row count was 1,100.

Since the table contains 1,161 rows, the row count requirement is satisfied.

Result: PASS



## 4. Final Verification

All three companies passed the manual ROE verification.

All three companies passed the 5-year Revenue CAGR verification.

The difference between the manually calculated values and the database
values was less than 0.1% for all checks.

| Company | ROE Check | Revenue CAGR Check |
|---|---|---|
| RELIANCE | PASS | PASS |
| INDIGO | PASS | PASS |
| TRENT | PASS | PASS |

### Overall Day 12 Result

- Financial ratios row count: PASS
- Required minimum of 1,100 rows: PASS
- ROE manual verification: PASS
- 5-year Revenue CAGR manual verification: PASS
- Difference less than 0.1%: PASS

