import json
import uuid

from sqlalchemy.engine import Engine

from backend.core.config import get_settings
from backend.core.constants import FEATURE_COLUMNS
from backend.ml.model_loader import load_model
from backend.ml.predictor import predict
from backend.repositories.aggregation_repository import AggregationRepository
from backend.repositories.feature_repository import FeatureRepository
from backend.repositories.prediction_repository import PredictionRepository
from backend.utils.timestamps import utc_now


class ScoringService:
    def __init__(self, engine: Engine):
        self.engine = engine

    def score_generation(self, generation_version: str, dry_run: bool = False) -> dict:
        frame = FeatureRepository(self.engine).scoring_frame(generation_version)
        if frame.empty:
            raise ValueError(f"No scoring rows for generation_version={generation_version}")
        model = load_model()
        result = predict(frame, model)
        if dry_run:
            return {
                "status": "validated",
                "run_id": None,
                "row_count": len(frame),
                "threshold": result.threshold,
                "flagged_count": int(result.classes.sum()),
            }

        run_id = str(uuid.uuid4())
        started_at = utc_now()
        run_values = {
            "run_id": run_id,
            "model_name": "logistic_regression",
            "model_version": model.run_name,
            "generation_version": generation_version,
            "artifact_sha256": model.artifact_sha256,
            "decision_threshold": result.threshold,
            "feature_contract_json": json.dumps(list(FEATURE_COLUMNS)),
            "started_at": started_at,
        }
        predictions = [
            {
                "run_id": run_id,
                "member_id": item.member_id,
                "base_profile_id": item.base_profile_id,
                "plan_key": item.plan_key,
                "probability": float(probability),
                "predicted_class": int(predicted_class),
                "decision_threshold": result.threshold,
                "scored_at": started_at,
            }
            for item, probability, predicted_class in zip(
                frame.itertuples(index=False), result.probabilities, result.classes, strict=True
            )
        ]
        batch_size = get_settings().scoring_batch_size
        with self.engine.begin() as connection:
            PredictionRepository.start_run(connection, run_values)
            for start in range(0, len(predictions), batch_size):
                PredictionRepository.insert_predictions(
                    connection, predictions[start : start + batch_size]
                )
            AggregationRepository.refresh_plan_kpis(connection, run_id)
            PredictionRepository.complete_run(connection, run_id, len(predictions), utc_now())
        return {
            "status": "completed",
            "run_id": run_id,
            "row_count": len(predictions),
            "threshold": result.threshold,
            "flagged_count": int(result.classes.sum()),
        }

