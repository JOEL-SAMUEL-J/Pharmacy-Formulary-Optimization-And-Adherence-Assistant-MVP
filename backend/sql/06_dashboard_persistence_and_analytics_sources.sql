-- Makes prediction persistence and existing analytics support both the
-- development generation and the separate dashboard-scoring generation.

SET NAMES utf8mb4;

ALTER TABLE ml_model_runs
    MODIFY COLUMN generation_version VARCHAR(30) NOT NULL;

CREATE TABLE IF NOT EXISTS ml_scoring_member_registry_v2_3 (
    member_id          VARCHAR(20) NOT NULL,
    base_profile_id    VARCHAR(20) NOT NULL,
    plan_key           VARCHAR(40) NOT NULL,
    generation_version VARCHAR(30) NOT NULL,
    PRIMARY KEY (member_id),
    KEY ix_scoring_registry_generation (generation_version, plan_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO ml_scoring_member_registry_v2_3
    (member_id, base_profile_id, plan_key, generation_version)
SELECT member_id, base_profile_id, plan_key, generation_version
FROM syn_members_v2_3
ON DUPLICATE KEY UPDATE
    base_profile_id=VALUES(base_profile_id),
    plan_key=VALUES(plan_key),
    generation_version=VALUES(generation_version);

INSERT INTO ml_scoring_member_registry_v2_3
    (member_id, base_profile_id, plan_key, generation_version)
SELECT member_id, base_profile_id, plan_key, generation_version
FROM ml_dashboard_scoring_features_v2_3
ON DUPLICATE KEY UPDATE
    base_profile_id=VALUES(base_profile_id),
    plan_key=VALUES(plan_key),
    generation_version=VALUES(generation_version);

SET @old_member_fk_exists := (
    SELECT COUNT(*) FROM information_schema.table_constraints
    WHERE constraint_schema=DATABASE()
      AND table_name='ml_adherence_predictions'
      AND constraint_name='fk_prediction_member'
      AND constraint_type='FOREIGN KEY'
);
SET @drop_old_member_fk := IF(
    @old_member_fk_exists > 0,
    'ALTER TABLE ml_adherence_predictions DROP FOREIGN KEY fk_prediction_member',
    'SELECT 1'
);
PREPARE drop_member_fk_stmt FROM @drop_old_member_fk;
EXECUTE drop_member_fk_stmt;
DEALLOCATE PREPARE drop_member_fk_stmt;

SET @registry_fk_exists := (
    SELECT COUNT(*) FROM information_schema.table_constraints
    WHERE constraint_schema=DATABASE()
      AND table_name='ml_adherence_predictions'
      AND constraint_name='fk_prediction_scoring_member'
      AND constraint_type='FOREIGN KEY'
);
SET @add_registry_fk := IF(
    @registry_fk_exists = 0,
    'ALTER TABLE ml_adherence_predictions ADD CONSTRAINT fk_prediction_scoring_member FOREIGN KEY (member_id) REFERENCES ml_scoring_member_registry_v2_3 (member_id)',
    'SELECT 1'
);
PREPARE add_registry_fk_stmt FROM @add_registry_fk;
EXECUTE add_registry_fk_stmt;
DEALLOCATE PREPARE add_registry_fk_stmt;

CREATE OR REPLACE VIEW analytics_member_features_v2_3 AS
SELECT member_id, base_profile_id, contract_id, plan_id, segment_id,
       plan_key, plan_name, generation_version,
       mean_synthetic_cost_burden, prior_authorization_rate,
       step_therapy_rate, quantity_limit_rate, nonpreferred_pharmacy_rate
FROM syn_member_features_v2_3
UNION ALL
SELECT d.member_id, d.base_profile_id, d.contract_id, d.plan_id, d.segment_id,
       d.plan_key, COALESCE(names.plan_name, d.plan_key), d.generation_version,
       d.mean_synthetic_cost_burden, d.prior_authorization_rate,
       d.step_therapy_rate, d.quantity_limit_rate,
       d.nonpreferred_pharmacy_rate
FROM ml_dashboard_scoring_features_v2_3 d
LEFT JOIN (
    SELECT plan_key, MIN(plan_name) AS plan_name
    FROM syn_member_features_v2_3 GROUP BY plan_key
) names ON names.plan_key=d.plan_key;

CREATE OR REPLACE VIEW analytics_member_medications_v2_3 AS
SELECT member_medication_id, member_id, base_profile_id,
       contract_id, plan_id, segment_id, rxcui, drug_name,
       tier_level_value, synthetic_cost_burden_score,
       prior_authorization_yn_flag, step_therapy_yn_flag,
       quantity_limit_yn_flag, preferred_pharmacy_yn_flag,
       generation_version
FROM syn_member_medications_v2_3
UNION ALL
SELECT member_medication_id, member_id, base_profile_id,
       contract_id, plan_id, segment_id, rxcui, drug_name,
       tier_level_value, synthetic_cost_burden_score,
       prior_authorization_yn_flag, step_therapy_yn_flag,
       quantity_limit_yn_flag, preferred_pharmacy_yn_flag,
       generation_version
FROM dashboard_member_medications_v2_3;

-- Required results after both cohorts are loaded: 6000, 6000 and 10686.
SELECT COUNT(*) AS registry_rows FROM ml_scoring_member_registry_v2_3;
SELECT COUNT(*) AS analytics_feature_rows FROM analytics_member_features_v2_3;
SELECT COUNT(*) AS analytics_medication_rows FROM analytics_member_medications_v2_3;

-- Dashboard-only reconciliation: 3000 and 5343.
SELECT COUNT(*) AS dashboard_feature_rows
FROM analytics_member_features_v2_3
WHERE generation_version='mvp_v2.3-dashboard-01';
SELECT COUNT(*) AS dashboard_medication_rows
FROM analytics_member_medications_v2_3
WHERE generation_version='mvp_v2.3-dashboard-01';
