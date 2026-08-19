from fastapi.testclient import TestClient

from backend.app.main import app


def test_root_does_not_require_database():
    response = TestClient(app).get("/")
    assert response.status_code == 200
    assert response.json()["version"] == "2.3.0"


def test_openapi_contains_dashboard_and_scoring_routes():
    schema = TestClient(app).get("/openapi.json").json()
    assert "/api/v1/scoring/batch" in schema["paths"]
    assert "/api/v1/dashboard/plans/{plan_key}/summary" in schema["paths"]

