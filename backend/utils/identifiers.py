import re

from backend.core.exceptions import ValidationError


PLAN_KEY_PATTERN = re.compile(r"^[A-Za-z0-9]+\|[A-Za-z0-9]+\|[0-9]{3}$")


def validate_plan_key(plan_key: str) -> str:
    if not PLAN_KEY_PATTERN.fullmatch(plan_key):
        raise ValidationError("plan_key must use contract_id|plan_id|three-digit-segment_id")
    return plan_key

