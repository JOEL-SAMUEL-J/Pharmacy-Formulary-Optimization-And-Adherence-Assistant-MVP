from fastapi import APIRouter

from backend.api.dependencies import EngineDep, SettingsDep
from backend.core.exceptions import NotFoundError
from backend.repositories.plan_repository import PlanRepository
from backend.utils.identifiers import validate_plan_key


router = APIRouter(prefix="/plans", tags=["plans"])


@router.get("")
def list_plans(engine: EngineDep, settings: SettingsDep):
    return {"data": PlanRepository(engine).list_plans(settings.generation_version)}


@router.get("/{plan_key}")
def get_plan(plan_key: str, engine: EngineDep, settings: SettingsDep):
    validate_plan_key(plan_key)
    plan = PlanRepository(engine).get_plan(plan_key, settings.generation_version)
    if not plan:
        raise NotFoundError(f"Plan not found: {plan_key}")
    return {"data": plan}

