from sqlalchemy.engine import Engine

from backend.repositories.base import row, rows


PLAN_SELECT = """
    SELECT plan_key, MIN(plan_name) AS plan_name,
           MIN(contract_id) AS contract_id, MIN(plan_id) AS plan_id,
           MIN(segment_id) AS segment_id, COUNT(*) AS available_scenarios
    FROM analytics_member_features_v2_3
"""


class PlanRepository:
    def __init__(self, engine: Engine):
        self.engine = engine

    def list_plans(self, generation_version: str) -> list[dict]:
        return rows(
            self.engine,
            PLAN_SELECT + " WHERE generation_version=:generation_version GROUP BY plan_key ORDER BY plan_key",
            {"generation_version": generation_version},
        )

    def get_plan(self, plan_key: str, generation_version: str) -> dict | None:
        return row(
            self.engine,
            PLAN_SELECT + """
                WHERE plan_key=:plan_key AND generation_version=:generation_version
                GROUP BY plan_key
            """,
            {"plan_key": plan_key, "generation_version": generation_version},
        )
