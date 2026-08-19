from sqlalchemy.engine import Engine

from backend.core.constants import POC_DISCLAIMER
from backend.core.exceptions import NotFoundError
from backend.repositories.aggregation_repository import AggregationRepository
from backend.repositories.prediction_repository import PredictionRepository


class DashboardService:
    def __init__(self, engine: Engine):
        self.predictions = PredictionRepository(engine)
        self.aggregations = AggregationRepository(engine)

    def active_run(self) -> dict:
        run = self.predictions.active_run()
        if not run:
            raise NotFoundError("No completed active scoring run. Run batch scoring first.")
        return run

    def summary(self, plan_key: str) -> dict:
        run = self.active_run()
        summary = self.aggregations.plan_summary(run["run_id"], plan_key)
        if not summary:
            raise NotFoundError(f"No dashboard summary for plan {plan_key}")
        summary["disclaimer"] = POC_DISCLAIMER
        return summary

