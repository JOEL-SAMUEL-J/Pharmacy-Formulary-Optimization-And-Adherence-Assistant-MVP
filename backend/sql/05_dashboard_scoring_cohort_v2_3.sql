-- Separate leakage-safe dashboard cohort for MVP v2.3.
-- This table does not contain non_adherent, future PDC or generator diagnostics.

SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS ml_dashboard_scoring_features_v2_3 (
    member_id                       VARCHAR(20) NOT NULL,
    base_profile_id                 VARCHAR(20) NOT NULL,
    contract_id                     VARCHAR(10) NOT NULL,
    plan_id                         VARCHAR(10) NOT NULL,
    segment_id                      CHAR(3) NOT NULL,
    plan_key                        VARCHAR(40) NOT NULL,
    generation_version              VARCHAR(30) NOT NULL,
    age                             SMALLINT UNSIGNED NOT NULL,
    chronic_condition_count         TINYINT UNSIGNED NOT NULL,
    medication_count                TINYINT UNSIGNED NOT NULL,
    historical_member_pdc           DECIMAL(16,12) NOT NULL,
    historical_missed_fill_rate     DECIMAL(16,12) NOT NULL,
    historical_mean_delay_days      DECIMAL(16,12) NOT NULL,
    mean_tier_level                 DECIMAL(16,12) NOT NULL,
    prior_authorization_rate        DECIMAL(16,12) NOT NULL,
    step_therapy_rate               DECIMAL(16,12) NOT NULL,
    quantity_limit_rate             DECIMAL(16,12) NOT NULL,
    nonpreferred_pharmacy_rate      DECIMAL(16,12) NOT NULL,
    mean_synthetic_cost_burden      DECIMAL(16,12) NOT NULL,
    PRIMARY KEY (member_id),
    UNIQUE KEY uq_dashboard_profile_plan
        (base_profile_id, contract_id, plan_id, segment_id),
    KEY ix_dashboard_plan (plan_key),
    KEY ix_dashboard_profile (base_profile_id),
    CONSTRAINT chk_dashboard_age CHECK (age BETWEEN 50 AND 95),
    CONSTRAINT chk_dashboard_rates CHECK (
        historical_member_pdc BETWEEN 0 AND 1 AND
        historical_missed_fill_rate BETWEEN 0 AND 1 AND
        prior_authorization_rate BETWEEN 0 AND 1 AND
        step_therapy_rate BETWEEN 0 AND 1 AND
        quantity_limit_rate BETWEEN 0 AND 1 AND
        nonpreferred_pharmacy_rate BETWEEN 0 AND 1 AND
        mean_synthetic_cost_burden BETWEEN 0 AND 1
    )
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS dashboard_member_medications_v2_3 (
    member_medication_id             VARCHAR(24) NOT NULL,
    member_id                        VARCHAR(20) NOT NULL,
    base_profile_id                  VARCHAR(20) NOT NULL,
    contract_id                      VARCHAR(10) NOT NULL,
    plan_id                          VARCHAR(10) NOT NULL,
    segment_id                       CHAR(3) NOT NULL,
    rxcui                            VARCHAR(20) NOT NULL,
    drug_name                        VARCHAR(500) NOT NULL,
    medication_group                 VARCHAR(100) NOT NULL,
    assumed_days_supply              SMALLINT UNSIGNED NOT NULL,
    tier_level_value                 TINYINT UNSIGNED NOT NULL,
    prior_authorization_yn           CHAR(1) NOT NULL,
    step_therapy_yn                  CHAR(1) NOT NULL,
    quantity_limit_yn                CHAR(1) NOT NULL,
    quantity_limit_amount            DECIMAL(16,4) NULL,
    quantity_limit_days              SMALLINT UNSIGNED NULL,
    pharmacy_number                  VARCHAR(20) NOT NULL,
    pharmacy_zipcode                 CHAR(5) NOT NULL,
    preferred_pharmacy_yn            CHAR(1) NOT NULL,
    same_zip_pharmacy_yn             CHAR(1) NOT NULL,
    pharmacy_retail                  CHAR(1) NOT NULL,
    in_area_flag                     TINYINT UNSIGNED NOT NULL,
    synthetic_cost_burden_score      DECIMAL(16,12) NOT NULL,
    generation_version               VARCHAR(30) NOT NULL,
    master_seed                      INT NOT NULL,
    source_class                     VARCHAR(40) NOT NULL,
    tier_num                         TINYINT UNSIGNED NOT NULL,
    prior_authorization_yn_flag      TINYINT(1) NOT NULL,
    step_therapy_yn_flag             TINYINT(1) NOT NULL,
    quantity_limit_yn_flag           TINYINT(1) NOT NULL,
    preferred_pharmacy_yn_flag       TINYINT(1) NOT NULL,
    PRIMARY KEY (member_medication_id),
    UNIQUE KEY uq_dashboard_member_drug (member_id, rxcui),
    KEY ix_dashboard_med_member (member_id),
    KEY ix_dashboard_med_plan_drug
        (contract_id, plan_id, segment_id, rxcui),
    CONSTRAINT fk_dashboard_med_member FOREIGN KEY (member_id)
        REFERENCES ml_dashboard_scoring_features_v2_3 (member_id),
    CONSTRAINT chk_dashboard_med_tier CHECK (tier_level_value BETWEEN 1 AND 5)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE OR REPLACE VIEW ml_adherence_dashboard_scoring_view_v2_3 AS
SELECT
    member_id,
    base_profile_id,
    contract_id,
    plan_id,
    segment_id,
    plan_key,
    generation_version,
    age,
    chronic_condition_count,
    medication_count,
    historical_member_pdc,
    historical_missed_fill_rate,
    historical_mean_delay_days,
    mean_tier_level,
    prior_authorization_rate,
    step_therapy_rate,
    quantity_limit_rate,
    nonpreferred_pharmacy_rate,
    mean_synthetic_cost_burden
FROM ml_dashboard_scoring_features_v2_3
WHERE generation_version = 'mvp_v2.3-dashboard-01';

-- Expected result: 3000 rows, 1000 profiles and 3 plans.
SELECT
    COUNT(*) AS scoring_rows,
    COUNT(DISTINCT base_profile_id) AS base_profiles,
    COUNT(DISTINCT plan_key) AS plans
FROM ml_adherence_dashboard_scoring_view_v2_3;

-- Expected medication result: 5343 rows and 3000 represented members.
SELECT
    COUNT(*) AS medication_rows,
    COUNT(DISTINCT member_id) AS represented_members
FROM dashboard_member_medications_v2_3;
