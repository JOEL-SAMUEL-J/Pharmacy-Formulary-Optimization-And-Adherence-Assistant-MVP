import re

from fastapi import APIRouter, Query

from backend.api.dependencies import EngineDep, SettingsDep
from backend.core.exceptions import ValidationError
from backend.schemas.prescriber import (
    PrescriberListResponse,
    PrescriberMedicationResponse,
    PrescriberSummaryResponse,
)
from backend.services.prescriber_analysis_service import PrescriberAnalysisService
from backend.utils.identifiers import validate_plan_key


router = APIRouter(prefix="/analytics/prescribers", tags=["analytics", "prescribers"])
PRESCRIBER_ID_PATTERN = re.compile(r"^PR[0-9]{5}$")
RXCUI_PATTERN = re.compile(r"^[0-9]{1,20}$")


def service(engine, settings) -> PrescriberAnalysisService:
    return PrescriberAnalysisService(
        engine=engine,
        generation_version=settings.generation_version,
        minimum_members=settings.prescriber_minimum_members,
        high_tier_threshold=settings.prescriber_high_tier_threshold,
        cost_burden_threshold=settings.prescriber_cost_burden_threshold,
    )


def optional_plan_key(value: str | None) -> str | None:
    return validate_plan_key(value) if value else None


def validate_prescriber_id(value: str) -> str:
    if not PRESCRIBER_ID_PATTERN.fullmatch(value):
        raise ValidationError("prescriber_id must use PR followed by five digits")
    return value


def optional_rxcui(value: str | None) -> str | None:
    if value and not RXCUI_PATTERN.fullmatch(value):
        raise ValidationError("rxcui must contain 1 to 20 digits")
    return value


@router.get("", response_model=PrescriberListResponse)
def list_prescribers(
    engine: EngineDep,
    settings: SettingsDep,
    plan_key: str | None = None,
    rxcui: str | None = None,
    specialty: str | None = Query(None, min_length=1, max_length=80),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    data = service(engine, settings).list_prescribers(
        optional_plan_key(plan_key), optional_rxcui(rxcui), specialty, limit, offset
    )
    return {"data": data}


@router.get("/{prescriber_id}", response_model=PrescriberSummaryResponse)
def get_prescriber(
    prescriber_id: str,
    engine: EngineDep,
    settings: SettingsDep,
    plan_key: str | None = None,
):
    data = service(engine, settings).get_prescriber(
        validate_prescriber_id(prescriber_id), optional_plan_key(plan_key)
    )
    return {"data": data}


@router.get(
    "/{prescriber_id}/medications",
    response_model=PrescriberMedicationResponse,
)
def prescriber_medications(
    prescriber_id: str,
    engine: EngineDep,
    settings: SettingsDep,
    plan_key: str | None = None,
    rxcui: str | None = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    data = service(engine, settings).medications(
        validate_prescriber_id(prescriber_id),
        optional_plan_key(plan_key),
        optional_rxcui(rxcui),
        limit,
        offset,
    )
    return {"data": data}


@router.get(
    "/{prescriber_id}/opportunities",
    response_model=PrescriberMedicationResponse,
)
def prescriber_opportunities(
    prescriber_id: str,
    engine: EngineDep,
    settings: SettingsDep,
    plan_key: str | None = None,
    rxcui: str | None = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    data = service(engine, settings).opportunities(
        validate_prescriber_id(prescriber_id),
        optional_plan_key(plan_key),
        optional_rxcui(rxcui),
        limit,
        offset,
    )
    return {"data": data}
