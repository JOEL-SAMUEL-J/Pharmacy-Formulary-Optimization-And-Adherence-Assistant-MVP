from types import SimpleNamespace

from fastapi.testclient import TestClient

from backend.api.dependencies import get_engine, get_settings
from backend.app.main import app
import backend.routes.prescribers as prescriber_routes


def metric():
    return {
        "generation_version": "mvp_v2.3",
        "contract_id": "S4802",
        "plan_id": "138",
        "segment_id": "000",
        "plan_key": "S4802|138|000",
        "prescriber_id": "PR00001",
        "prescriber_display_name": "Synthetic Prescriber 001",
        "specialty": "Primary Care",
        "rxcui": "1048450",
        "drug_name": "Synthetic Drug",
        "distinct_member_count": 8,
        "assignment_exposure_count": 8,
        "minimum_tier": 4,
        "maximum_tier": 4,
        "average_tier": 4.0,
        "average_synthetic_cost_burden": 0.55,
        "prior_authorization_rate": 0.0,
        "step_therapy_rate": 0.0,
        "quantity_limit_rate": 1.0,
        "high_tier_member_count": 8,
        "prescriber_drug_share": 0.25,
        "formulary_review_flag": True,
        "review_reason_codes": ["HIGH_TIER_EXPOSURE", "QUANTITY_LIMIT_EXPOSURE"],
        "review_label": "Potential Formulary Review Opportunity - Synthetic POC",
        "disclaimer": "Synthetic POC only",
    }


class FakeService:
    def __init__(self, **_kwargs):
        pass

    def list_prescribers(self, *_args):
        return [{
            "prescriber_id": "PR00001",
            "prescriber_display_name": "Synthetic Prescriber 001",
            "specialty": "Primary Care",
            "prescriber_region": "South",
            "prescriber_zipcode": "30303",
            "distinct_member_count": 24,
            "assignment_exposure_count": 24,
            "distinct_drug_count": 4,
            "plan_count": 3,
        }]

    def get_prescriber(self, *_args):
        return {
            "generation_version": "mvp_v2.3",
            "prescriber_id": "PR00001",
            "prescriber_display_name": "Synthetic Prescriber 001",
            "specialty": "Primary Care",
            "prescriber_region": "South",
            "prescriber_zipcode": "30303",
            "prescriber_volume_weight": 0.02,
            "plan_count": 3,
            "distinct_drug_count": 4,
            "distinct_member_count": 24,
            "assignment_exposure_count": 24,
            "average_tier": 4.0,
            "average_synthetic_cost_burden": 0.5,
            "prior_authorization_rate": 0.1,
            "step_therapy_rate": 0.0,
            "quantity_limit_rate": 0.2,
            "disclaimer": "Synthetic POC only",
        }

    def medications(self, *_args):
        return [metric()]

    def opportunities(self, *_args):
        return [metric()]


def settings():
    return SimpleNamespace(
        generation_version="mvp_v2.3",
        prescriber_minimum_members=5,
        prescriber_high_tier_threshold=4,
        prescriber_cost_burden_threshold=0.50,
    )


def client(monkeypatch):
    monkeypatch.setattr(prescriber_routes, "PrescriberAnalysisService", FakeService)
    app.dependency_overrides[get_engine] = lambda: object()
    app.dependency_overrides[get_settings] = settings
    return TestClient(app)


def test_openapi_contains_prescriber_routes():
    paths = app.openapi()["paths"]
    assert "/api/v1/analytics/prescribers" in paths
    assert "/api/v1/analytics/prescribers/{prescriber_id}" in paths
    assert "/api/v1/analytics/prescribers/{prescriber_id}/medications" in paths
    assert "/api/v1/analytics/prescribers/{prescriber_id}/opportunities" in paths


def test_list_contract(monkeypatch):
    response = client(monkeypatch).get("/api/v1/analytics/prescribers")
    assert response.status_code == 200
    assert response.json()["data"][0]["prescriber_id"] == "PR00001"


def test_medication_contract(monkeypatch):
    response = client(monkeypatch).get(
        "/api/v1/analytics/prescribers/PR00001/medications",
        params={"plan_key": "S4802|138|000"},
    )
    assert response.status_code == 200
    assert response.json()["data"][0]["formulary_review_flag"] is True


def test_invalid_prescriber_id_returns_422(monkeypatch):
    response = client(monkeypatch).get(
        "/api/v1/analytics/prescribers/not-valid/medications"
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_invalid_plan_key_returns_422(monkeypatch):
    response = client(monkeypatch).get(
        "/api/v1/analytics/prescribers",
        params={"plan_key": "S4802-138-000"},
    )
    assert response.status_code == 422


def test_limit_bounds_return_422(monkeypatch):
    test_client = client(monkeypatch)
    assert test_client.get("/api/v1/analytics/prescribers", params={"limit": 0}).status_code == 422
    assert test_client.get("/api/v1/analytics/prescribers", params={"limit": 101}).status_code == 422
