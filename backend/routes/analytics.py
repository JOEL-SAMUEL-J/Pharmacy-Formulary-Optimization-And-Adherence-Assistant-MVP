from fastapi import APIRouter, Query

from backend.api.dependencies import EngineDep
from backend.services.dashboard_service import DashboardService
from backend.utils.identifiers import validate_plan_key


router = APIRouter(prefix="/analytics", tags=["analytics"])


def context(engine, plan_key):
    validate_plan_key(plan_key)
    service = DashboardService(engine)
    return service, service.active_run()["run_id"]


@router.get("/risk-distribution")
def risk_distribution(plan_key: str, engine: EngineDep):
    service, run_id = context(engine, plan_key)
    return {"data": service.aggregations.risk_distribution(run_id, plan_key)}


@router.get("/tiers")
def tiers(plan_key: str, engine: EngineDep):
    service, run_id = context(engine, plan_key)
    return {"data": service.aggregations.tier_summary(run_id, plan_key)}


@router.get("/restrictions")
def restrictions(plan_key: str, engine: EngineDep):
    service, run_id = context(engine, plan_key)
    return {"data": service.aggregations.restriction_summary(run_id, plan_key)}


@router.get("/pharmacies")
def pharmacies(plan_key: str, engine: EngineDep):
    service, run_id = context(engine, plan_key)
    return {"data": service.aggregations.pharmacy_summary(run_id, plan_key)}


@router.get("/cost-burden")
def cost_burden(plan_key: str, engine: EngineDep):
    service, run_id = context(engine, plan_key)
    return {"data": service.aggregations.cost_summary(run_id, plan_key)}


@router.get("/medications")
def medications(
    plan_key: str,
    engine: EngineDep,
    limit: int = Query(20, ge=1, le=100),
):
    service, run_id = context(engine, plan_key)
    return {
        "data": service.aggregations.medication_summary(run_id, plan_key, limit)
    }


@router.get("/matched-profiles")
def matched_profiles(engine: EngineDep, limit: int = Query(50, ge=1, le=500)):
    service = DashboardService(engine)
    run_id = service.active_run()["run_id"]
    return {
        "data": service.aggregations.matched_profile_comparison(run_id, limit)
    }


@router.get("/opportunities")
def opportunities(
    plan_key: str,
    engine: EngineDep,
    limit: int = Query(20, ge=1, le=100),
):
    service, run_id = context(engine, plan_key)
    return {
        "data": service.aggregations.review_opportunities(run_id, plan_key, limit),
        "label": "Potential Formulary Review Opportunity - Synthetic POC",
    }
