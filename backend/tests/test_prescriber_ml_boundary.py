from pathlib import Path

from backend.core.constants import FEATURE_COLUMNS, TRACE_COLUMNS
from backend.repositories.feature_repository import FeatureRepository


def test_prescriber_is_not_part_of_the_ml_contract():
    assert "prescriber_id" not in FEATURE_COLUMNS
    assert "prescriber_id" not in TRACE_COLUMNS


def test_feature_repository_does_not_reference_prescriber():
    source = Path(FeatureRepository.__module__.replace(".", "/") + ".py")
    if not source.exists():
        source = Path("backend/repositories/feature_repository.py")
    text = source.read_text(encoding="utf-8")
    assert "prescriber" not in text.lower()
    assert "ml_adherence_training_view_v2_3" in text


def test_scoring_service_does_not_reference_prescriber():
    text = Path("backend/services/scoring_service.py").read_text(encoding="utf-8")
    assert "prescriber" not in text.lower()


def test_prediction_sql_does_not_reference_prescriber():
    text = Path(
        "backend/sql/02_backend_prediction_and_aggregation_tables.sql"
    ).read_text(encoding="utf-8")
    assert "prescriber" not in text.lower()
