from fastapi import APIRouter

from backend.routes import (
    analytics,
    dashboard,
    health,
    model_metadata,
    plans,
    predictions,
    prescribers,
    scoring,
)


api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(plans.router)
api_router.include_router(model_metadata.router)
api_router.include_router(scoring.router)
api_router.include_router(dashboard.router)
api_router.include_router(analytics.router)
api_router.include_router(prescribers.router)
api_router.include_router(predictions.router)
