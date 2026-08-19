from collections.abc import Iterable
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.engine import Connection, Engine

from backend.repositories.base import row, rows


class PredictionRepository:
    def __init__(self, engine: Engine):
        self.engine = engine

    def active_run(self) -> dict | None:
        return row(self.engine, """
            SELECT run_id, model_name, model_version, generation_version,
                   artifact_sha256, decision_threshold, row_count, status,
                   started_at, completed_at
            FROM ml_model_runs WHERE is_active=1 AND status='completed'
            ORDER BY completed_at DESC LIMIT 1
        """)

    @staticmethod
    def start_run(connection: Connection, values: dict) -> None:
        connection.execute(text("UPDATE ml_model_runs SET is_active=0 WHERE is_active=1"))
        connection.execute(text("""
            INSERT INTO ml_model_runs
                (run_id, model_name, model_version, generation_version,
                 artifact_sha256, decision_threshold, feature_contract_json,
                 row_count, status, is_active, started_at)
            VALUES
                (:run_id, :model_name, :model_version, :generation_version,
                 :artifact_sha256, :decision_threshold, :feature_contract_json,
                 0, 'running', 0, :started_at)
        """), values)

    @staticmethod
    def insert_predictions(connection: Connection, values: Iterable[dict]) -> None:
        connection.execute(text("""
            INSERT INTO ml_adherence_predictions
                (run_id, member_id, base_profile_id, plan_key,
                 predicted_non_adherence_probability, predicted_class,
                 decision_threshold, scored_at)
            VALUES
                (:run_id, :member_id, :base_profile_id, :plan_key,
                 :probability, :predicted_class, :decision_threshold, :scored_at)
        """), list(values))

    @staticmethod
    def complete_run(connection: Connection, run_id: str, row_count: int, completed_at: datetime) -> None:
        connection.execute(text("""
            UPDATE ml_model_runs
            SET row_count=:row_count, status='completed', is_active=1,
                completed_at=:completed_at
            WHERE run_id=:run_id
        """), {"run_id": run_id, "row_count": row_count, "completed_at": completed_at})

    def list_predictions(self, run_id: str, plan_key: str | None, limit: int, offset: int) -> list[dict]:
        condition = "AND plan_key=:plan_key" if plan_key else ""
        return rows(self.engine, f"""
            SELECT member_id, base_profile_id, plan_key,
                   predicted_non_adherence_probability, predicted_class,
                   decision_threshold, scored_at
            FROM ml_adherence_predictions
            WHERE run_id=:run_id {condition}
            ORDER BY plan_key, member_id LIMIT :limit OFFSET :offset
        """, {"run_id": run_id, "plan_key": plan_key, "limit": limit, "offset": offset})

