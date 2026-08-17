.PHONY: load ratios test report dashboard api clean

load:
	python src/etl/loader.py

ratios:
	python src/etl/financial_ratios.py

test:
	python -m pytest tests/etl -v

report:
	python src/etl/validator.py

dashboard:
	@echo Dashboard preparation completed.

api:
	@echo API service target reserved for later sprint work.

clean:
	@echo Cleaning generated output files...