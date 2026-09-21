.PHONY: load ratios test report dashboard api clean

load:
	python src/etl/loader.py

ratios:
	python src/etl/financial_ratios.py

test:
	python -m pytest -v --html=reports/pytest_report.html --self-contained-html

report:
	python -m src.reports.batch_reports
	python -m src.reports.sector_reports
	python -m src.reports.portfolio_summary

dashboard:
	python -m streamlit run src/dashboard/app.py --server.port 8501

api:
	python -m uvicorn src.api.main:app --host 127.0.0.1 --port 8000

clean:
	Get-ChildItem -Recurse -Force -Filter *.pyc | Remove-Item -Force
	Get-ChildItem -Recurse -Force -Directory -Filter __pycache__ | Remove-Item -Recurse -Force
	Remove-Item -Force -ErrorAction SilentlyContinue .pytest_cache