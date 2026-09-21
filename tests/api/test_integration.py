from fastapi.testclient import TestClient

from src.api.main import app
from src.dashboard.utils.db import get_companies, get_ratios

client = TestClient(app)


def test_dashboard_screener_matches_api():
    response = client.get("/api/v1/screener?min_roe=15")

    assert response.status_code == 200

    api_data = response.json()

    companies = get_companies()

    dashboard_company_ids = []

    for _, company in companies.iterrows():
        data = get_ratios(company["company_name"], 2024)

        if not data.empty:
            roe = data.iloc[0]["return_on_equity_pct"]

            if roe is not None and roe >= 15:
                dashboard_company_ids.append(company["id"])

    api_company_ids = [company["ticker"] for company in api_data]

    assert set(dashboard_company_ids) == set(api_company_ids)
