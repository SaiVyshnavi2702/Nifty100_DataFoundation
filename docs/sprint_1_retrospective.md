# Sprint 1 - Data Foundation Retrospective





Sprint 1 focused on building the data foundation for the Nifty100 project.



The sprint covered environment setup, Excel data loading, data normalization, validation, SQLite schema creation, full data loading, manual data review, testing, and final exploratory analysis.



The sprint was planned for 34 story points across Day 01 to Day 07.





## What Went Well



The ETL pipeline was successfully developed and used to load the available source data into the SQLite database.



Year and ticker normalization were implemented and tested thoroughly.



The SQLite schema was created with primary keys, foreign keys, unique constraints, and supporting indexes.



The final database was checked for foreign-key integrity and returned zero violations.



Data-quality validation was completed across DQ-01 to DQ-16. The final validation report contains no failure records and no critical failures.



The load audit confirmed that the source row counts matched the database row counts for all loaded datasets.



The ETL test suite finished with 38 tests passing and zero failures.



The 10 exploratory SQL queries were executed successfully against the final database.





## What Could Be Improved



The expected company count and table count in the original sprint specification did not completely match the actual source data and final implementation.



The reporting file locations should have been standardized earlier so that generated reports were placed directly in the required output directory.



The validation and load reports could be integrated more directly into the main ETL workflow so that they are generated automatically whenever the pipeline is run.



More automated tests could be added for the loader and validator in future sprints.





## What We Learned



The actual source data should always be checked before relying on expected row counts in the project specification.



Database integrity checks should be performed after every major load.



Automated validation is important for identifying data-quality problems before the database is used by later modules.



Keeping audit reports and verification results in the project repository makes the work easier to review and reproduce.



Running exploratory queries against the final database provides a useful final check that the loaded data can actually be queried as expected.





## Sprint Outcome



The Sprint 1 data foundation is technically complete.



The database is populated and usable, foreign-key integrity is clean, data-quality validation has no recorded failures, all 38 ETL tests pass, and all 10 exploratory queries execute successfully.



The remaining step is final Sprint Review sign-off and updating the project board.





