from fastapi import APIRouter

from backend.api.dependencies import EngineDep
from backend.core.constants import FEATURE_COLUMNS, POC_DISCLAIMER
from backend.services.dashboard_service import DashboardService
from backend.ml.model_loader import load_model


router = APIRouter(prefix="/metadata", tags=["metadata"])


@router.get("/active-run")
def active_run(engine: EngineDep):
    return {
        "data": DashboardService(engine).active_run(),
        "feature_contract": list(FEATURE_COLUMNS),
        "disclaimer": POC_DISCLAIMER,
    }


@router.get("/model")
def model_metadata():
    model = load_model()
    return {
        "data": {
            "model_run": model.run_name,
            "threshold": model.threshold,
            "artifact_sha256": model.artifact_sha256,
            "selection": model.metadata.get("primary_model_a_selected", {}),
        },
        "disclaimer": POC_DISCLAIMER,
    }
