



\## 1. Screener API Load Test



I tested the Screener API with 10 requests running concurrently using Python threads.



The endpoint tested was:



`GET /api/v1/screener?min\_roe=15`



All 10 requests completed successfully with HTTP 200 responses.



\- Number of concurrent requests: 10

\- Successful requests: 10/10

\- Total time for all 10 requests: 0.754 seconds

\- Required target: less than 10 seconds

\- Result: \*\*PASS\*\*



The Screener API handled the concurrent requests well within the required performance target.



\## 2. Company Profile Performance



I measured the data-loading time for the Company Profile page using five representative companies.



|Company|Load Time|
|-|-|
|TCS|0.805 seconds|
|HDFCBANK|0.043 seconds|
|RELIANCE|0.169 seconds|
|SUNPHARMA|0.026 seconds|
|TATASTEEL|0.037 seconds|



The required target was less than 3 seconds for each company.



All five companies completed within the target, so the performance test passed.



The measurement covered the main data-loading operations used by the Company Profile page, including company details, sector, financial ratios, profit and loss data, and pros and cons.



\## 3. SQLite Query Optimisation



Before making any changes, I checked the existing database indexes and query plans.



Some tables already had indexes on `company\_id`, but the Company Profile queries for `financial\_ratios` and `profitandloss` were still performing table scans and using a temporary B-tree when sorting the data by year.



To improve these queries, I added composite indexes using `company\_id` and `year` to the following tables:



\- `financial\_ratios`

\- `profitandloss`

\- `balancesheet`

\- `cashflow`



After adding the indexes, I checked the query plans again using `EXPLAIN QUERY PLAN`.



The updated query plans confirmed that SQLite is using the new indexes for the `financial\_ratios` and `profitandloss` queries.



\## 4. End-to-End Test



I started both application services simultaneously:



\- FastAPI: `http://127.0.0.1:8000`

\- Streamlit: `http://127.0.0.1:8501`



Both services started successfully without any port conflict.



I also verified both services using PowerShell.



The FastAPI health endpoint returned HTTP 200 with `"status": "ok"` and the database row counts.



The Streamlit application also returned HTTP 200, confirming that the dashboard server was running successfully.



While starting Streamlit, I initially encountered an import-path issue because the dashboard pages use `dashboard` imports from the `src` directory. I resolved this by setting the `src` directory in `PYTHONPATH` before starting Streamlit:



`$env:PYTHONPATH="$PWD\\src"`



No dashboard page imports were modified.



\## 5. Performance Observations



The performance tests did not identify any major bottlenecks.



The main database optimisation identified during testing was the use of `company\_id` and `year` together in the frequently accessed financial tables. The required composite indexes were added and verified.



The Company Profile performance test measured the underlying data-loading functions used by the page. It did not measure complete browser rendering time.



\## 6. Final Result



Day 43 performance and end-to-end testing was completed successfully.



\- 10 concurrent Screener API requests: \*\*PASS\*\*

\- Company Profile performance for 5 companies: \*\*PASS\*\*

\- SQLite query optimisation: \*\*COMPLETED\*\*

\- FastAPI and Streamlit running simultaneously: \*\*PASS\*\*

\- Port conflict check: \*\*PASS\*\*

