from fastapi import APIRouter

from backend.api.dependencies import EngineDep
from backend.services.dashboard_service import DashboardService
from backend.utils.identifiers import validate_plan_key


router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/plans/compare")
def compare_plans(engine: EngineDep):
    service = DashboardService(engine)
    run = service.active_run()
    return {"data": service.aggregations.compare_plans(run["run_id"])}


@router.get("/plans/{plan_key}/summary")
def plan_summary(plan_key: str, engine: EngineDep):
    validate_plan_key(plan_key)
    return {"data": DashboardService(engine).summary(plan_key)}

