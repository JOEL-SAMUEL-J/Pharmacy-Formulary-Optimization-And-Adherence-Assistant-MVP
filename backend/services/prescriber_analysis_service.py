from decimal import Decimal

from sqlalchemy.engine import Engine

from backend.core.constants import POC_DISCLAIMER
from backend.core.exceptions import NotFoundError
from backend.repositories.prescriber_repository import PrescriberRepository


PRESCRIBER_REVIEW_LABEL = "Potential Formulary Review Opportunity - Synthetic POC"


def _number(value, default=0.0) -> float:
    if value is None:
        return float(default)
    if isinstance(value, Decimal):
        return float(value)
    return float(value)


class PrescriberAnalysisService:
    def __init__(
        self,
        engine: Engine,
        generation_version: str,
        minimum_members: int,
        high_tier_threshold: int,
        cost_burden_threshold: float,
    ):
        self.repository = PrescriberRepository(engine)
        self.generation_version = generation_version
        self.minimum_members = minimum_members
        self.high_tier_threshold = high_tier_threshold
        self.cost_burden_threshold = cost_burden_threshold

    def list_prescribers(
        self,
        plan_key: str | None,
        rxcui: str | None,
        specialty: str | None,
        limit: int,
        offset: int,
    ) -> list[dict]:
        return self.repository.list_prescribers(
            self.generation_version, plan_key, rxcui, specialty, limit, offset
        )

    def get_prescriber(self, prescriber_id: str, plan_key: str | None) -> dict:
        master = self.repository.get_prescriber(self.generation_version, prescriber_id)
        if not master:
            raise NotFoundError(f"Prescriber not found: {prescriber_id}")
        summary = self.repository.summary(self.generation_version, prescriber_id, plan_key)
        return {
            **master,
            **(summary or {}),
            "disclaimer": POC_DISCLAIMER,
        }

    def medications(
        self,
        prescriber_id: str,
        plan_key: str | None,
        rxcui: str | None,
        limit: int,
        offset: int,
    ) -> list[dict]:
        self._require_prescriber(prescriber_id)
        values = self.repository.medication_breakdown(
            self.generation_version, prescriber_id, plan_key, rxcui, limit, offset
        )
        return [self._with_review_fields(item) for item in values]

    def opportunities(
        self,
        prescriber_id: str,
        plan_key: str | None,
        rxcui: str | None,
        limit: int,
        offset: int,
    ) -> list[dict]:
        # Fetch enough raw rows before filtering; final pagination remains stable.
        values = self.medications(prescriber_id, plan_key, rxcui, 500, 0)
        flagged = [item for item in values if item["formulary_review_flag"]]
        flagged.sort(
            key=lambda item: (
                -item["distinct_member_count"],
                -item["average_synthetic_cost_burden"],
                item["plan_key"],
                item["rxcui"],
            )
        )
        return flagged[offset : offset + limit]

    def _require_prescriber(self, prescriber_id: str) -> None:
        if not self.repository.get_prescriber(self.generation_version, prescriber_id):
            raise NotFoundError(f"Prescriber not found: {prescriber_id}")

    def _with_review_fields(self, item: dict) -> dict:
        member_count = int(item.get("distinct_member_count") or 0)
        maximum_tier = _number(item.get("maximum_tier"))
        cost_burden = _number(item.get("average_synthetic_cost_burden"))
        pa_rate = _number(item.get("prior_authorization_rate"))
        st_rate = _number(item.get("step_therapy_rate"))
        ql_rate = _number(item.get("quantity_limit_rate"))

        reasons: list[str] = []
        if maximum_tier >= self.high_tier_threshold:
            reasons.append("HIGH_TIER_EXPOSURE")
        if cost_burden >= self.cost_burden_threshold:
            reasons.append("ELEVATED_SYNTHETIC_COST_BURDEN")
        if pa_rate > 0:
            reasons.append("PRIOR_AUTHORIZATION_EXPOSURE")
        if st_rate > 0:
            reasons.append("STEP_THERAPY_EXPOSURE")
        if ql_rate > 0:
            reasons.append("QUANTITY_LIMIT_EXPOSURE")

        flag = (
            member_count >= self.minimum_members
            and maximum_tier >= self.high_tier_threshold
            and any(
                reason != "HIGH_TIER_EXPOSURE"
                for reason in reasons
            )
        )
        return {
            **item,
            "formulary_review_flag": flag,
            "review_reason_codes": reasons if flag else [],
            "review_label": PRESCRIBER_REVIEW_LABEL if flag else None,
            "disclaimer": POC_DISCLAIMER,
        }
