-- Run after the v2.3 synthetic-member schema and ML views have been loaded.
-- These tables store model-run provenance, member-level predictions and stable
-- plan-level dashboard KPIs. They do not alter the source synthetic tables.

SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS ml_model_runs (
    run_id                    CHAR(36) NOT NULL,
    model_name               VARCHAR(80) NOT NULL,
    model_version            VARCHAR(100) NOT NULL,
    generation_version       VARCHAR(20) NOT NULL,
    artifact_sha256          CHAR(64) NOT NULL,
    decision_threshold       DECIMAL(16,12) NOT NULL,
    feature_contract_json    JSON NOT NULL,
    row_count                INT UNSIGNED NOT NULL DEFAULT 0,
    status                   ENUM('running','completed','failed') NOT NULL,
    is_active                TINYINT(1) NOT NULL DEFAULT 0,
    started_at               DATETIME(6) NOT NULL,
    completed_at             DATETIME(6) NULL,
    PRIMARY KEY (run_id),
    KEY ix_model_runs_active (is_active, status, completed_at),
    CONSTRAINT chk_model_run_threshold CHECK (decision_threshold BETWEEN 0 AND 1)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS ml_adherence_predictions (
    run_id                              CHAR(36) NOT NULL,
    member_id                           VARCHAR(20) NOT NULL,
    base_profile_id                     VARCHAR(20) NOT NULL,
    plan_key                            VARCHAR(40) NOT NULL,
    predicted_non_adherence_probability DECIMAL(16,12) NOT NULL,
    predicted_class                     TINYINT(1) NOT NULL,
    decision_threshold                  DECIMAL(16,12) NOT NULL,
    scored_at                           DATETIME(6) NOT NULL,
    PRIMARY KEY (run_id, member_id),
    KEY ix_prediction_plan (run_id, plan_key),
    KEY ix_prediction_profile (run_id, base_profile_id),
    CONSTRAINT fk_prediction_run FOREIGN KEY (run_id)
        REFERENCES ml_model_runs (run_id) ON DELETE CASCADE,
    CONSTRAINT fk_prediction_member FOREIGN KEY (member_id)
        REFERENCES syn_members_v2_3 (member_id),
    CONSTRAINT chk_prediction_probability CHECK
        (predicted_non_adherence_probability BETWEEN 0 AND 1),
    CONSTRAINT chk_prediction_class CHECK (predicted_class IN (0,1))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS dashboard_plan_kpis (
    run_id                          CHAR(36) NOT NULL,
    plan_key                        VARCHAR(40) NOT NULL,
    plan_name                       VARCHAR(255) NOT NULL,
    total_members_scored            INT UNSIGNED NOT NULL,
    members_flagged_at_risk         INT UNSIGNED NOT NULL,
    percentage_flagged_at_risk      DECIMAL(16,8) NOT NULL,
    average_predicted_risk          DECIMAL(16,12) NOT NULL,
    average_cost_burden             DECIMAL(16,12) NOT NULL,
    prior_authorization_exposure    DECIMAL(16,12) NOT NULL,
    step_therapy_exposure           DECIMAL(16,12) NOT NULL,
    quantity_limit_exposure         DECIMAL(16,12) NOT NULL,
    nonpreferred_pharmacy_exposure  DECIMAL(16,12) NOT NULL,
    refreshed_at                    DATETIME(6) NOT NULL,
    PRIMARY KEY (run_id, plan_key),
    CONSTRAINT fk_dashboard_kpi_run FOREIGN KEY (run_id)
        REFERENCES ml_model_runs (run_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

