import numpy as np
import pandas as pd

from backend.core.constants import FEATURE_COLUMNS
from backend.core.exceptions import ValidationError


RATE_COLUMNS = (
    "historical_member_pdc",
    "historical_missed_fill_rate",
    "prior_authorization_rate",
    "step_therapy_rate",
    "quantity_limit_rate",
    "nonpreferred_pharmacy_rate",
)


def validated_feature_frame(frame: pd.DataFrame) -> pd.DataFrame:
    missing = [column for column in FEATURE_COLUMNS if column not in frame.columns]
    if missing:
        raise ValidationError(f"Missing model features: {missing}")
    result = frame.loc[:, FEATURE_COLUMNS].copy()
    for column in FEATURE_COLUMNS:
        result[column] = pd.to_numeric(result[column], errors="coerce")
    if result.isna().any().any():
        bad = result.columns[result.isna().any()].tolist()
        raise ValidationError(f"Null or non-numeric values found in: {bad}")
    if not np.isfinite(result.to_numpy(dtype=float)).all():
        raise ValidationError("Model features contain infinite values")
    if not result.loc[:, RATE_COLUMNS].apply(lambda s: s.between(0, 1)).all().all():
        raise ValidationError("PDC and rate features must be between 0 and 1")
    if not result["age"].between(50, 95).all():
        raise ValidationError("age must be between 50 and 95 for this POC contract")
    if (result["medication_count"] < 1).any():
        raise ValidationError("medication_count must be positive")
    return result

