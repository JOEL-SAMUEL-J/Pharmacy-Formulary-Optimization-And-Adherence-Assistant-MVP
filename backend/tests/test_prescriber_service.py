from types import SimpleNamespace

import pytest

from backend.core.exceptions import NotFoundError
from backend.services.prescriber_analysis_service import PrescriberAnalysisService


def make_service():
    return PrescriberAnalysisService(
        engine=object(),
        generation_version="mvp_v2.3",
        minimum_members=5,
        high_tier_threshold=4,
        cost_burden_threshold=0.50,
    )


def metric(**overrides):
    value = {
        "generation_version": "mvp_v2.3",
        "contract_id": "S4802",
        "plan_id": "138",
        "segment_id": "000",
        "plan_key": "S4802|138|000",
        "prescriber_id": "PR00001",
        "prescriber_display_name": "Synthetic Prescriber 001",
        "specialty": "Primary Care",
        "rxcui": "1048450",
        "drug_name": "Synthetic Drug",
        "distinct_member_count": 8,
        "assignment_exposure_count": 8,
        "minimum_tier": 4,
        "maximum_tier": 4,
        "average_tier": 4.0,
        "average_synthetic_cost_burden": 0.55,
        "prior_authorization_rate": 0.0,
        "step_therapy_rate": 0.0,
        "quantity_limit_rate": 0.0,
        "high_tier_member_count": 8,
        "prescriber_drug_share": 0.25,
    }
    value.update(overrides)
    return value


def test_review_flag_requires_volume_tier_and_one_burden_condition():
    service = make_service()
    flagged = service._with_review_fields(metric())
    assert flagged["formulary_review_flag"] is True
    assert flagged["review_reason_codes"] == [
        "HIGH_TIER_EXPOSURE",
        "ELEVATED_SYNTHETIC_COST_BURDEN",
    ]
    assert "Synthetic POC" in flagged["review_label"]


@pytest.mark.parametrize(
    "changes",
    [
        {"distinct_member_count": 4},
        {"maximum_tier": 3, "average_tier": 3.0, "minimum_tier": 3},
        {
            "average_synthetic_cost_burden": 0.49,
            "prior_authorization_rate": 0.0,
            "step_therapy_rate": 0.0,
            "quantity_limit_rate": 0.0,
        },
    ],
)
def test_review_flag_fails_when_a_required_condition_is_missing(changes):
    result = make_service()._with_review_fields(metric(**changes))
    assert result["formulary_review_flag"] is False
    assert result["review_reason_codes"] == []
    assert result["review_label"] is None


def test_restriction_can_satisfy_burden_condition():
    result = make_service()._with_review_fields(
        metric(average_synthetic_cost_burden=0.30, prior_authorization_rate=0.25)
    )
    assert result["formulary_review_flag"] is True
    assert "PRIOR_AUTHORIZATION_EXPOSURE" in result["review_reason_codes"]


def test_unknown_prescriber_raises_not_found():
    service = make_service()
    service.repository = SimpleNamespace(get_prescriber=lambda *_: None)
    with pytest.raises(NotFoundError, match="PR99999"):
        service.get_prescriber("PR99999", None)


def test_empty_opportunities_returns_empty_list():
    service = make_service()
    service.medications = lambda *_args, **_kwargs: []
    assert service.opportunities("PR00001", None, None, 20, 0) == []


def test_opportunity_order_and_pagination_are_deterministic():
    service = make_service()
    values = [
        service._with_review_fields(metric(rxcui="2", distinct_member_count=9)),
        service._with_review_fields(metric(rxcui="1", distinct_member_count=9)),
        service._with_review_fields(metric(rxcui="3", distinct_member_count=7)),
    ]
    service.medications = lambda *_args, **_kwargs: values
    page = service.opportunities("PR00001", None, None, limit=2, offset=0)
    assert [item["rxcui"] for item in page] == ["1", "2"]
