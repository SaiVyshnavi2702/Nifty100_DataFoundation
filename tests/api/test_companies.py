from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


def test_get_companies_returns_92_records():
    response = client.get("/api/v1/companies")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 92


def test_get_tcs_company():
    response = client.get("/api/v1/companies/TCS")

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == "TCS"
    assert data["company_name"] == "Tata Consultancy Services Ltd"
    assert data["broad_sector"] == "Information Technology"


def test_invalid_company_returns_404():
    response = client.get("/api/v1/companies/INVALID")

    assert response.status_code == 404
