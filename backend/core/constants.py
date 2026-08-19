FEATURE_COLUMNS = (
    "age",
    "chronic_condition_count",
    "medication_count",
    "historical_member_pdc",
    "historical_missed_fill_rate",
    "historical_mean_delay_days",
    "mean_tier_level",
    "prior_authorization_rate",
    "step_therapy_rate",
    "quantity_limit_rate",
    "nonpreferred_pharmacy_rate",
    "mean_synthetic_cost_burden",
)

TRACE_COLUMNS = (
    "member_id",
    "base_profile_id",
    "contract_id",
    "plan_id",
    "segment_id",
    "plan_key",
    "generation_version",
)

LEAKAGE_COLUMNS = frozenset(
    {
        "non_adherent",
        "future_member_pdc",
        "mean_risk",
        "mean_miss_probability",
        "baseline_adherence_tendency",
        "master_seed",
        "source_class",
    }
)

RISK_BANDS = (
    ("Low", 0.00, 0.25),
    ("Moderate", 0.25, 0.50),
    ("High", 0.50, 0.75),
    ("Very High", 0.75, 1.01),
)

POC_DISCLAIMER = (
    "This prototype combines public CMS-derived plan, formulary and pharmacy "
    "attributes with synthetic member, utilization, adherence and prediction "
    "data. Results are proof-of-concept review signals, not real plan "
    "performance, causal findings, clinical advice or formulary recommendations."
)

