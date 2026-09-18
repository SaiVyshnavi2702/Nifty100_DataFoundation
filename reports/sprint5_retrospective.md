Sprint 5 Retrospective

Sprint Overview



Sprint 5 mainly focused on adding intelligence, NLP-based analysis, and PDF reporting to the Nifty100 Data Foundation project. The goal was to turn the financial data we already had into useful insights and easy-to-read reports.



What We Completed



During this sprint, we completed several important tasks:



Used the NLP parser to extract and analyze company growth and performance metrics.

Calculated CAGR for different financial metrics and reviewed companies with significant changes or differences.

Added cash flow intelligence to classify different company-level cash flow patterns.

Generated Pros and Cons analysis for individual companies.

Created company tearsheets using Python and ReportLab.

Automated the generation of tearsheets for all available companies.

Created sector-level reports showing median KPIs along with individual company metrics.

Created a portfolio summary PDF with a separate page for each company.

Added KPI trend indicators to show how the latest annual values compare with the previous year.

Checked the generated reports and visually reviewed sample PDFs to make sure the layouts were clean and there were no overflow or blank-page issues.

What Went Well



A major positive from this sprint was that the report generation process was automated. Instead of creating reports manually for each company, we built reusable functions that could generate them automatically.



The PDF reports also turned out well. The layouts were clean and readable in the reports we tested. We also made sure that missing data was displayed as N/A rather than causing the entire report generation process to fail.



Company and sector reports were successfully generated using data from the project database. The portfolio summary was also useful because it brings important KPIs for multiple companies together in a single document, making it easier to review the overall performance.



Challenges We Faced



One of the main challenges was the availability and quality of historical financial data. Some companies did not have enough historical information to calculate certain metrics properly.



There were also cases where financial metrics could not be calculated because the required values were missing or negative. We had to handle these cases carefully so that they did not break the reporting process.



Another challenge was that sector information was not available for every company in the database. Because of this, some sector-level analysis was limited.



The PDF reports also needed manual visual checking. Although the reports were generated successfully, we had to review sample PDFs to make sure there was no text overflow, unwanted blank pages, or layout issues.



What We Learned



This sprint gave us practical experience in automating financial report generation using Python and ReportLab.



We also learned more about calculating and interpreting CAGR and year-over-year financial trends. Handling incomplete and inconsistent financial data was another important learning, especially when working with real-world financial datasets.



We also learned how to create reusable reporting functions that can work across multiple companies and sectors instead of building each report separately.



Finally, we understood that generating a PDF successfully is not enough. The final report also needs to be visually checked to make sure the information is presented properly.



What Could Be Improved



There are still a few areas we can improve in the next sprint:



Improve historical financial data coverage for companies that currently have limited data.

Improve the validation and handling of missing financial metrics.

Add more automated checks for PDF layout issues such as overflow, missing content, and unexpected blank pages.

Improve the way financial insights and KPI trends are presented so that the reports are easier to understand.

Improve sector mapping so that more companies can be included in sector-level analysis.



Sprint Outcome



Overall, Sprint 5 was successfully completed and delivered the planned intelligence, analysis, and reporting features.



The project now has automated company tearsheets, sector-level reports, and a portfolio summary. These reports make it much easier to understand company performance, compare financial trends, and get a broader view of the Nifty100 data.



The sprint also helped us move beyond simply storing financial data and start turning that data into meaningful and presentable insights.

