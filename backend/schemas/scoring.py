from pydantic import BaseModel


class BatchScoreRequest(BaseModel):
    generation_version: str = "mvp_v2.3"
    dry_run: bool = False


class BatchScoreResponse(BaseModel):
    status: str
    run_id: str | None = None
    row_count: int
    threshold: float
    flagged_count: int

