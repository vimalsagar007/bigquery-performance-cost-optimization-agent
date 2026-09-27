from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["read_only_mode"] is True


def test_dry_run_endpoint():
    response = client.post(
        "/query/dry-run",
        json={"sql": "SELECT name FROM `bigquery-public-data.usa_names.usa_1910_current` WHERE year = 2020"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert data["estimated_bytes_processed"] > 0


def test_analyze_query_endpoint():
    response = client.post(
        "/analyze/query",
        json={"sql": "SELECT * FROM `bigquery-public-data.usa_names.usa_1910_current` LIMIT 10"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "query_summary" in data
    assert len(data["cost_findings"]) >= 1


def test_chat_endpoint():
    response = client.post(
        "/chat",
        json={"message": "Optimize SELECT * FROM `bigquery-public-data.usa_names.usa_1910_current`"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
