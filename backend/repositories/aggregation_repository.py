from sqlalchemy import text
from sqlalchemy.engine import Connection, Engine

from backend.repositories.base import row, rows


class AggregationRepository:
    def __init__(self, engine: Engine):
        self.engine = engine

    @staticmethod
    def refresh_plan_kpis(connection: Connection, run_id: str) -> None:
        connection.execute(
            text("DELETE FROM dashboard_plan_kpis WHERE run_id=:run_id"),
            {"run_id": run_id},
        )
        connection.execute(text("""
            INSERT INTO dashboard_plan_kpis
                (run_id, plan_key, plan_name, total_members_scored,
                 members_flagged_at_risk, percentage_flagged_at_risk,
                 average_predicted_risk, average_cost_burden,
                 prior_authorization_exposure, step_therapy_exposure,
                 quantity_limit_exposure, nonpreferred_pharmacy_exposure,
                 refreshed_at)
            SELECT p.run_id, f.plan_key, MIN(f.plan_name), COUNT(*),
                   SUM(p.predicted_class), 100.0 * AVG(p.predicted_class),
                   AVG(p.predicted_non_adherence_probability),
                   AVG(f.mean_synthetic_cost_burden),
                   AVG(f.prior_authorization_rate), AVG(f.step_therapy_rate),
                   AVG(f.quantity_limit_rate), AVG(f.nonpreferred_pharmacy_rate),
                   UTC_TIMESTAMP(6)
            FROM ml_adherence_predictions p
            JOIN analytics_member_features_v2_3 f ON f.member_id=p.member_id
            WHERE p.run_id=:run_id
            GROUP BY p.run_id, f.plan_key
        """), {"run_id": run_id})

    def plan_summary(self, run_id: str, plan_key: str) -> dict | None:
        return row(
            self.engine,
            "SELECT * FROM dashboard_plan_kpis WHERE run_id=:run_id AND plan_key=:plan_key",
            {"run_id": run_id, "plan_key": plan_key},
        )

    def compare_plans(self, run_id: str) -> list[dict]:
        return rows(
            self.engine,
            "SELECT * FROM dashboard_plan_kpis WHERE run_id=:run_id ORDER BY plan_key",
            {"run_id": run_id},
        )

    def risk_distribution(self, run_id: str, plan_key: str) -> list[dict]:
        return rows(self.engine, """
            SELECT CASE
                     WHEN predicted_non_adherence_probability < 0.25 THEN 'Low'
                     WHEN predicted_non_adherence_probability < 0.50 THEN 'Moderate'
                     WHEN predicted_non_adherence_probability < 0.75 THEN 'High'
                     ELSE 'Very High'
                   END AS category,
                   COUNT(*) AS member_count,
                   AVG(predicted_non_adherence_probability) AS average_risk
            FROM ml_adherence_predictions
            WHERE run_id=:run_id AND plan_key=:plan_key
            GROUP BY category
            ORDER BY FIELD(category, 'Low', 'Moderate', 'High', 'Very High')
        """, {"run_id": run_id, "plan_key": plan_key})

    def tier_summary(self, run_id: str, plan_key: str) -> list[dict]:
        return rows(self.engine, """
            SELECT m.tier_level_value AS category,
                   COUNT(DISTINCT p.member_id) AS member_count,
                   AVG(p.predicted_non_adherence_probability) AS average_risk
            FROM ml_adherence_predictions p
            JOIN analytics_member_medications_v2_3 m ON m.member_id=p.member_id
            WHERE p.run_id=:run_id AND p.plan_key=:plan_key
            GROUP BY m.tier_level_value ORDER BY m.tier_level_value
        """, {"run_id": run_id, "plan_key": plan_key})

    def restriction_summary(self, run_id: str, plan_key: str) -> list[dict]:
        return rows(self.engine, """
            SELECT restriction_type AS category,
                   COUNT(DISTINCT CASE WHEN exposed=1 THEN member_id END) AS member_count,
                   AVG(CASE WHEN exposed=1 THEN probability END) AS average_risk
            FROM (
                SELECT p.member_id, p.predicted_non_adherence_probability probability,
                       'Prior Authorization' restriction_type,
                       m.prior_authorization_yn_flag exposed
                FROM ml_adherence_predictions p
                JOIN analytics_member_medications_v2_3 m ON m.member_id=p.member_id
                WHERE p.run_id=:run_id AND p.plan_key=:plan_key
                UNION ALL
                SELECT p.member_id, p.predicted_non_adherence_probability,
                       'Step Therapy', m.step_therapy_yn_flag
                FROM ml_adherence_predictions p
                JOIN analytics_member_medications_v2_3 m ON m.member_id=p.member_id
                WHERE p.run_id=:run_id AND p.plan_key=:plan_key
                UNION ALL
                SELECT p.member_id, p.predicted_non_adherence_probability,
                       'Quantity Limit', m.quantity_limit_yn_flag
                FROM ml_adherence_predictions p
                JOIN analytics_member_medications_v2_3 m ON m.member_id=p.member_id
                WHERE p.run_id=:run_id AND p.plan_key=:plan_key
            ) restriction_rows
            GROUP BY restriction_type ORDER BY restriction_type
        """, {"run_id": run_id, "plan_key": plan_key})

    def pharmacy_summary(self, run_id: str, plan_key: str) -> list[dict]:
        return rows(self.engine, """
            SELECT CASE WHEN m.preferred_pharmacy_yn_flag=1
                        THEN 'Preferred' ELSE 'Nonpreferred' END AS category,
                   COUNT(DISTINCT p.member_id) AS member_count,
                   AVG(p.predicted_non_adherence_probability) AS average_risk
            FROM ml_adherence_predictions p
            JOIN analytics_member_medications_v2_3 m ON m.member_id=p.member_id
            WHERE p.run_id=:run_id AND p.plan_key=:plan_key
            GROUP BY category ORDER BY category
        """, {"run_id": run_id, "plan_key": plan_key})

    def cost_summary(self, run_id: str, plan_key: str) -> list[dict]:
        return rows(self.engine, """
            SELECT CASE
                     WHEN f.mean_synthetic_cost_burden < 0.25 THEN 'Low'
                     WHEN f.mean_synthetic_cost_burden < 0.50 THEN 'Moderate'
                     WHEN f.mean_synthetic_cost_burden < 0.75 THEN 'High'
                     ELSE 'Very High'
                   END AS category,
                   COUNT(*) AS member_count,
                   AVG(p.predicted_non_adherence_probability) AS average_risk
            FROM ml_adherence_predictions p
            JOIN analytics_member_features_v2_3 f ON f.member_id=p.member_id
            WHERE p.run_id=:run_id AND p.plan_key=:plan_key
            GROUP BY category
            ORDER BY FIELD(category, 'Low', 'Moderate', 'High', 'Very High')
        """, {"run_id": run_id, "plan_key": plan_key})

    def medication_summary(self, run_id: str, plan_key: str, limit: int) -> list[dict]:
        return rows(self.engine, """
            SELECT m.rxcui, MIN(m.drug_name) AS drug_name,
                   COUNT(DISTINCT p.member_id) AS exposed_members,
                   AVG(p.predicted_non_adherence_probability) AS average_risk,
                   AVG(m.synthetic_cost_burden_score) AS average_cost_burden,
                   AVG(m.prior_authorization_yn_flag) AS prior_authorization_rate,
                   AVG(m.step_therapy_yn_flag) AS step_therapy_rate,
                   AVG(m.quantity_limit_yn_flag) AS quantity_limit_rate
            FROM ml_adherence_predictions p
            JOIN analytics_member_medications_v2_3 m ON m.member_id=p.member_id
            WHERE p.run_id=:run_id AND p.plan_key=:plan_key
            GROUP BY m.rxcui
            ORDER BY average_risk DESC, exposed_members DESC LIMIT :limit
        """, {"run_id": run_id, "plan_key": plan_key, "limit": limit})

    def matched_profile_comparison(self, run_id: str, limit: int) -> list[dict]:
        return rows(self.engine, """
            SELECT base_profile_id,
                   COUNT(DISTINCT plan_key) AS plans_compared,
                   MIN(predicted_non_adherence_probability) AS minimum_risk,
                   MAX(predicted_non_adherence_probability) AS maximum_risk,
                   MAX(predicted_non_adherence_probability) -
                       MIN(predicted_non_adherence_probability) AS risk_range,
                   GROUP_CONCAT(
                       CONCAT(plan_key, ':',
                              ROUND(predicted_non_adherence_probability, 4))
                       ORDER BY plan_key SEPARATOR ', '
                   ) AS plan_risks
            FROM ml_adherence_predictions
            WHERE run_id=:run_id
            GROUP BY base_profile_id
            HAVING COUNT(DISTINCT plan_key) >= 2
            ORDER BY risk_range DESC, base_profile_id LIMIT :limit
        """, {"run_id": run_id, "limit": limit})

    def review_opportunities(self, run_id: str, plan_key: str, limit: int) -> list[dict]:
        return rows(self.engine, """
            SELECT m.rxcui, MIN(m.drug_name) AS drug_name,
                   COUNT(DISTINCT p.member_id) AS exposed_members,
                   AVG(p.predicted_non_adherence_probability) AS average_risk,
                   AVG(m.synthetic_cost_burden_score) AS average_cost_burden,
                   AVG((m.prior_authorization_yn_flag + m.step_therapy_yn_flag +
                        m.quantity_limit_yn_flag) / 3.0) AS restriction_exposure,
                   AVG(1 - m.preferred_pharmacy_yn_flag) AS nonpreferred_exposure,
                   0.45 * AVG(p.predicted_non_adherence_probability) +
                   0.25 * AVG(m.synthetic_cost_burden_score) +
                   0.20 * AVG((m.prior_authorization_yn_flag +
                               m.step_therapy_yn_flag +
                               m.quantity_limit_yn_flag) / 3.0) +
                   0.10 * AVG(1 - m.preferred_pharmacy_yn_flag) AS review_score
            FROM ml_adherence_predictions p
            JOIN analytics_member_medications_v2_3 m ON m.member_id=p.member_id
            WHERE p.run_id=:run_id AND p.plan_key=:plan_key
            GROUP BY m.rxcui
            HAVING COUNT(DISTINCT p.member_id) >= 5
            ORDER BY review_score DESC, exposed_members DESC LIMIT :limit
        """, {"run_id": run_id, "plan_key": plan_key, "limit": limit})
