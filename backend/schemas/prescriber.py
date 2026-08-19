from pydantic import BaseModel, ConfigDict, Field


class PrescriberListItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    prescriber_id: str
    prescriber_display_name: str
    specialty: str
    prescriber_region: str | None = None
    prescriber_zipcode: str | None = None
    distinct_member_count: int = Field(ge=0)
    assignment_exposure_count: int = Field(ge=0)
    distinct_drug_count: int = Field(ge=0)
    plan_count: int = Field(ge=0)


class PrescriberSummary(BaseModel):
    model_config = ConfigDict(extra="ignore")

    generation_version: str
    prescriber_id: str
    prescriber_display_name: str
    specialty: str
    prescriber_region: str | None = None
    prescriber_zipcode: str | None = None
    prescriber_volume_weight: float = Field(gt=0)
    plan_count: int = Field(default=0, ge=0)
    distinct_drug_count: int = Field(default=0, ge=0)
    distinct_member_count: int = Field(default=0, ge=0)
    assignment_exposure_count: int = Field(default=0, ge=0)
    average_tier: float = Field(default=0, ge=0)
    average_synthetic_cost_burden: float = Field(default=0, ge=0, le=1)
    prior_authorization_rate: float = Field(default=0, ge=0, le=1)
    step_therapy_rate: float = Field(default=0, ge=0, le=1)
    quantity_limit_rate: float = Field(default=0, ge=0, le=1)
    disclaimer: str


class PrescriberMedicationMetric(BaseModel):
    model_config = ConfigDict(extra="ignore")

    generation_version: str
    contract_id: str
    plan_id: str
    segment_id: str
    plan_key: str
    prescriber_id: str
    prescriber_display_name: str
    specialty: str
    rxcui: str
    drug_name: str
    distinct_member_count: int = Field(ge=0)
    assignment_exposure_count: int = Field(ge=0)
    minimum_tier: float = Field(ge=0)
    maximum_tier: float = Field(ge=0)
    average_tier: float = Field(ge=0)
    average_synthetic_cost_burden: float = Field(ge=0, le=1)
    prior_authorization_rate: float = Field(ge=0, le=1)
    step_therapy_rate: float = Field(ge=0, le=1)
    quantity_limit_rate: float = Field(ge=0, le=1)
    high_tier_member_count: int = Field(ge=0)
    prescriber_drug_share: float = Field(ge=0, le=1)
    formulary_review_flag: bool
    review_reason_codes: list[str]
    review_label: str | None = None
    disclaimer: str


class PrescriberListResponse(BaseModel):
    data: list[PrescriberListItem]


class PrescriberSummaryResponse(BaseModel):
    data: PrescriberSummary


class PrescriberMedicationResponse(BaseModel):
    data: list[PrescriberMedicationMetric]
