from fastapi import APIRouter

from backend.api.dependencies import EngineDep
from backend.schemas.scoring import BatchScoreRequest, BatchScoreResponse
from backend.services.scoring_service import ScoringService


router = APIRouter(prefix="/scoring", tags=["scoring"])


@router.post("/batch", response_model=BatchScoreResponse)
def score_batch(request: BatchScoreRequest, engine: EngineDep):
    return ScoringService(engine).score_generation(
        request.generation_version, request.dry_run
    )

