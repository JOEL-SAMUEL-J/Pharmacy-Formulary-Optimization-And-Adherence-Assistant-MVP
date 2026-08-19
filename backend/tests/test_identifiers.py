import pytest

from backend.core.exceptions import ValidationError
from backend.utils.identifiers import validate_plan_key


def test_valid_plan_key_preserves_segment_width():
    assert validate_plan_key("S4802|138|000") == "S4802|138|000"


def test_invalid_plan_key_is_rejected():
    with pytest.raises(ValidationError):
        validate_plan_key("S4802-138-0")

