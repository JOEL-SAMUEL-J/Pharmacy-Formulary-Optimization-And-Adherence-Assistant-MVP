from fastapi import APIRouter, Query

from backend.api.dependencies import EngineDep
from backend.repositories.prediction_repository import PredictionRepository
from backend.services.dashboard_service import DashboardService
from backend.utils.identifiers import validate_plan_key


router = APIRouter(prefix="/predictions", tags=["predictions"])


@router.get("")
def list_predictions(
    engine: EngineDep,
    plan_key: str | None = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    if plan_key:
        validate_plan_key(plan_key)
    run = DashboardService(engine).active_run()
    data = PredictionRepository(engine).list_predictions(
        run["run_id"], plan_key, limit, offset
    )
    return {"data": data, "limit": limit, "offset": offset}

