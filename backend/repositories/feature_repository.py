import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine

from backend.core.constants import FEATURE_COLUMNS, TRACE_COLUMNS


SCORING_VIEW_BY_GENERATION = {
    "mvp_v2.3": "ml_adherence_training_view_v2_3",
    "mvp_v2.3-dashboard-01": "ml_adherence_dashboard_scoring_view_v2_3",
}


class FeatureRepository:
    def __init__(self, engine: Engine):
        self.engine = engine

    def scoring_frame(self, generation_version: str) -> pd.DataFrame:
        source_view = SCORING_VIEW_BY_GENERATION.get(generation_version)
        if not source_view:
            supported = ", ".join(sorted(SCORING_VIEW_BY_GENERATION))
            raise ValueError(
                f"Unsupported generation_version={generation_version}. "
                f"Supported values: {supported}"
            )

        selected = ", ".join((*TRACE_COLUMNS, *FEATURE_COLUMNS))
        # source_view comes only from the fixed allowlist above. The generation
        # value remains a bound parameter.
        query = text(
            f"SELECT {selected} FROM {source_view} "
            "WHERE generation_version=:generation_version ORDER BY member_id"
        )
        with self.engine.connect() as connection:
            return pd.read_sql(
                query,
                connection,
                params={"generation_version": generation_version},
            )
