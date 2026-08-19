import pandas as pd
import pytest

from backend.core.constants import FEATURE_COLUMNS
from backend.core.exceptions import ValidationError
from backend.ml.input_validator import validated_feature_frame


def valid_frame() -> pd.DataFrame:
    values = {name: [0.2] for name in FEATURE_COLUMNS}
    values.update({"age": [70], "chronic_condition_count": [2], "medication_count": [2]})
    return pd.DataFrame(values)


def test_contract_returns_features_in_registered_order():
    result = validated_feature_frame(valid_frame())
    assert list(result.columns) == list(FEATURE_COLUMNS)


def test_contract_rejects_missing_feature():
    with pytest.raises(ValidationError, match="Missing model features"):
        validated_feature_frame(valid_frame().drop(columns=["historical_member_pdc"]))


def test_contract_rejects_invalid_rate():
    frame = valid_frame()
    frame.loc[0, "quantity_limit_rate"] = 1.5
    with pytest.raises(ValidationError, match="between 0 and 1"):
        validated_feature_frame(frame)

