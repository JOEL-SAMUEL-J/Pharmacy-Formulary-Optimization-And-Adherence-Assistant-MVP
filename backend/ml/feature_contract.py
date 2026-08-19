from backend.core.constants import FEATURE_COLUMNS, LEAKAGE_COLUMNS, TRACE_COLUMNS
from backend.core.exceptions import ValidationError


def validate_feature_names(columns) -> None:
    columns = list(columns)
    missing = [name for name in FEATURE_COLUMNS if name not in columns]
    leakage = sorted(LEAKAGE_COLUMNS.intersection(columns))
    if missing:
        raise ValidationError(f"Missing model features: {missing}")
    if leakage:
        raise ValidationError(f"Leakage fields cannot be model inputs: {leakage}")


def model_columns() -> list[str]:
    return list(FEATURE_COLUMNS)


def trace_columns() -> list[str]:
    return list(TRACE_COLUMNS)

