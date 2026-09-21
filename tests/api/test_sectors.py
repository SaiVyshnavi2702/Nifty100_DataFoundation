from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


def test_get_sectors():
    response = client.get("/api/v1/sectors")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 10


def test_information_technology_sector():
    response = client.get("/api/v1/sectors/Information%20Technology/companies")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 5

    for company in data:
        assert company["broad_sector"] == "Information Technology"
