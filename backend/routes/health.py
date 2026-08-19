from fastapi import APIRouter

from backend.api.dependencies import EngineDep, SettingsDep
from backend.db.health import database_health


router = APIRouter(tags=["health"])


@router.get("/health")
def health(engine: EngineDep, settings: SettingsDep):
    return {
        "status": "ok",
        "application": settings.app_name,
        "environment": settings.app_env,
        "database": database_health(engine),
    }

