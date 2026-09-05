Sprint 3 Retrospective
Overview

Sprint 3 covered Days 15–21 and focused on completing the screener engine, implementing the six preset screeners, calculating peer percentile rankings, generating radar charts and Excel reports, and carrying out the final validation and sprint review.

The main goal was to make the financial screener fully functional with configurable thresholds and six presets, while also completing peer analysis for all 11 peer groups and producing the required reporting outputs.

What I Completed
Day 15 — Filter Engine Core

I implemented the screener filter engine in src/screener/engine.py. The engine loads the threshold configuration from config/screener_config.yaml and applies the required filters to the financial ratios dataframe.

The engine supports the required filterable metrics, including ROE, D/E, FCF, Revenue CAGR, PAT CAGR, OPM, P/E, P/B, Dividend Yield, ICR, Market Cap, Net Profit, EPS CAGR, Asset Turnover, and Sales.

I also implemented the required handling for Financials when applying D/E filters and the Debt Free treatment for Interest Coverage Ratio.

The screener results are returned with the composite quality score and sorted accordingly.

Day 16 — Six Preset Screeners

I implemented and tested all six required presets:

Quality Compounder
Value Pick
Growth Accelerator
Dividend Champion
Debt-Free Blue Chip
Turnaround Watch

The presets were tested against the full 92-company universe.

Four presets returned between 5 and 50 companies as expected:

Quality Compounder — 22 companies
Growth Accelerator — 19 companies
Dividend Champion — 30 companies
Turnaround Watch — 32 companies

Two presets returned fewer than five companies under the exact prescribed thresholds:

Value Pick — 2 companies
Debt-Free Blue Chip — 2 companies

These were recorded as data-driven warnings rather than logic failures. The business-sense validation passed for all six presets, and the validation confirmed that the prescribed filter conditions were being correctly enforced.

Day 17 — Composite Score and Screener Export

I completed the composite quality score implementation using the required profitability, cash quality, growth, and leverage components.

The scoring process includes P10/P90 winsorisation before normalisation and sector-relative scoring so that companies are evaluated relative to their broad sector.

I also generated output/screener_output.xlsx with six sheets, one for each preset. The output contains the required KPI information, composite quality scores, sorting by score, and threshold-based colour coding.

The generated workbook was verified programmatically and contains the expected six preset sheets.

Day 18 — Peer Percentile Rankings

I implemented the peer percentile calculation in src/analytics/peer.py.

Percentile rankings were calculated for the required 10 metrics across all 11 peer groups. The D/E ranking uses the inverse percentile approach so that lower debt-to-equity results in a higher percentile rank.

The peer percentile results were stored in the SQLite peer_percentiles table with the required company, peer group, metric, value, percentile, and year information.

Day 19 — Radar Charts

I generated radar/polar charts for the companies using the required financial metrics and peer-group comparisons.

The charts include company values and peer-group reference values and were exported to the expected reports/radar_charts/ directory.

I verified that all 100 expected radar charts were successfully generated.

Day 20 — Peer Comparison Excel Report

I generated output/peer_comparison.xlsx containing 11 peer-group sheets:

Private Banks
Public Sector Banks
IT Services
Pharmaceuticals
Automobiles
Life Insurance
Oil & Gas
Power & Utilities
Steel
FMCG
Consumer Finance

The sheets contain company information, financial metrics, percentile rankings, percentile colour coding, benchmark highlighting, and peer-group median summary rows.

The workbook was verified to contain exactly 11 sheets as required.

Day 21 — Final Testing and Validation

I ran the dedicated DQ tests for DQ-01 through DQ-14. All 14 DQ tests passed with zero failures.

I then ran the complete project test suite:

125 tests passed, 0 failures.

I also manually verified the top five results from the Quality Compounder preset. All five companies satisfied the required conditions of ROE > 15% and D/E < 1.

For the IT Services peer group, I verified that TCS had the highest ROE and also the highest ROE percentile rank, confirming that the percentile ranking logic was working correctly for that spot-check.

The required screener_output.xlsx and peer_comparison.xlsx files were also verified to exist in the output directory.

What Went Well

The main Sprint 3 functionality was completed successfully and the required analytical outputs were generated.

The screener engine correctly applied the configured filters, and all six presets were implemented and validated against the 92-company universe.

The peer analysis was completed across all 11 peer groups, and the Excel report was generated with the required structure and formatting.

The testing results were particularly positive. All 14 dedicated DQ tests passed, and the complete project test suite finished with 125/125 tests passing.

The final manual validation also confirmed that the Quality Compounder and IT Services ranking requirements were working as expected.

Challenges

One challenge during validation was that two presets did not meet the requested minimum result count of five companies when the exact prescribed thresholds were applied. Value Pick returned two companies and Debt-Free Blue Chip also returned two companies.

Rather than changing the thresholds just to increase the number of results, I kept the prescribed business rules unchanged and recorded these as data-driven warnings. The business-sense validation still passed for all six presets.

I also faced some issues with PowerShell command quoting and differences between the expected and actual dataframe column names during validation. I resolved these by inspecting the actual dataframe structure and adjusting the validation commands.

Another issue occurred with imports in the ETL validator tests. Some imports worked when modules were executed directly but caused problems when the modules were imported as part of the src.etl package. I corrected the imports and successfully reran the tests.

What I Learned

This sprint reinforced the importance of validating the actual data and dataframe structure before making assumptions about column names or output formats.

I also gained more experience with programmatically checking Excel reports using Python and pandas, rather than relying entirely on manually opening the files.

The testing process helped me understand the value of both targeted tests for specific requirements and the complete project test suite for overall regression checking.

I also learned that a preset returning fewer companies than expected does not necessarily indicate an implementation problem. In this case, the exact business thresholds produced fewer results, so it was important to distinguish a data-driven outcome from a logic failure.

What Could Be Improved

For future sprints, I would add dedicated automated validation scripts for the major deliverables.

For example, the validation could automatically check:

Number of companies returned by each preset
Required screener threshold conditions
Excel sheet names and counts
Required columns and data types
Percentile calculations
Percentile colour coding
Benchmark company highlighting
Peer median summary rows
Radar chart count and filenames
SQLite peer percentile records

This would reduce the amount of manual checking required during the final sprint review.

I would also add explicit spot-check scripts for multiple peer groups, including both IT Services and FMCG, so that the peer-ranking validation is reproducible rather than dependent on manual inspection.

Final Status

Sprint 3 is substantially complete from the implementation and validation perspective.

The screener engine, six presets, composite scoring, peer percentile calculations, radar charts, and Excel reports were implemented successfully. The required output files were generated and verified.

The six presets correctly enforce their prescribed conditions. Four presets met the requested 5–50 result-count range, while Value Pick and Debt-Free Blue Chip returned two companies each under the exact prescribed thresholds. These were recorded as data-driven warnings rather than implementation failures, and no thresholds were changed simply to increase the number of results.

All 14 DQ tests passed, and the complete test suite passed with 125 tests and 0 failures.

The Quality Compounder top-five validation passed. The IT Services and FMCG peer-ranking spot-checks were also completed successfully, with the company having the highest ROE receiving the highest ROE percentile rank in both groups.

The required output files were generated and verified. The remaining Sprint 3 activity is the final demo of screener_output.xlsx and peer_comparison.xlsx to the team lead and formal team-lead sign-off.