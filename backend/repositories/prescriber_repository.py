from sqlalchemy.engine import Engine

from backend.repositories.base import row, rows


class PrescriberRepository:
    def __init__(self, engine: Engine):
        self.engine = engine

    @staticmethod
    def _analysis_filters(generation_version, plan_key=None, prescriber_id=None, rxcui=None, specialty=None):
        clauses = ["analysis.generation_version=:generation_version"]
        params = {"generation_version": generation_version}
        for name, value in (("plan_key", plan_key), ("prescriber_id", prescriber_id),
                            ("rxcui", rxcui), ("specialty", specialty)):
            if value:
                clauses.append(f"analysis.{name}=:{name}")
                params[name] = value
        return " AND ".join(clauses), params

    def list_prescribers(self, generation_version, plan_key, rxcui, specialty, limit, offset):
        where_sql, params = self._analysis_filters(
            generation_version, plan_key=plan_key, rxcui=rxcui, specialty=specialty
        )
        params.update({"limit": limit, "offset": offset})
        return rows(self.engine, f"""
            SELECT analysis.prescriber_id,
                   MIN(analysis.prescriber_display_name) prescriber_display_name,
                   MIN(analysis.specialty) specialty,
                   MIN(analysis.prescriber_region) prescriber_region,
                   MIN(analysis.prescriber_zipcode) prescriber_zipcode,
                   COUNT(DISTINCT analysis.member_id) distinct_member_count,
                   COUNT(DISTINCT analysis.member_medication_id) assignment_exposure_count,
                   COUNT(DISTINCT analysis.rxcui) distinct_drug_count,
                   COUNT(DISTINCT analysis.plan_key) plan_count
            FROM prescriber_member_medications_all_v2_3 analysis
            WHERE {where_sql}
            GROUP BY analysis.prescriber_id
            ORDER BY assignment_exposure_count DESC, analysis.prescriber_id
            LIMIT :limit OFFSET :offset
        """, params)

    def get_prescriber(self, generation_version, prescriber_id):
        return row(self.engine, """
            SELECT generation_version, prescriber_id,
                   MIN(prescriber_display_name) prescriber_display_name,
                   MIN(specialty) specialty, MIN(prescriber_region) prescriber_region,
                   MIN(prescriber_zipcode) prescriber_zipcode,
                   MIN(prescriber_volume_weight) prescriber_volume_weight
            FROM prescriber_member_medications_all_v2_3
            WHERE generation_version=:generation_version AND prescriber_id=:prescriber_id
            GROUP BY generation_version, prescriber_id
        """, {"generation_version": generation_version, "prescriber_id": prescriber_id})

    def summary(self, generation_version, prescriber_id, plan_key):
        clauses = ["generation_version=:generation_version", "prescriber_id=:prescriber_id"]
        params = {"generation_version": generation_version, "prescriber_id": prescriber_id}
        if plan_key:
            clauses.append("plan_key=:plan_key")
            params["plan_key"] = plan_key
        return row(self.engine, f"""
            SELECT prescriber_id, MIN(prescriber_display_name) prescriber_display_name,
                   MIN(specialty) specialty, COUNT(DISTINCT plan_key) plan_count,
                   COUNT(DISTINCT rxcui) distinct_drug_count,
                   COUNT(DISTINCT member_id) distinct_member_count,
                   COUNT(DISTINCT member_medication_id) assignment_exposure_count,
                   AVG(tier_num) average_tier,
                   AVG(synthetic_cost_burden_score) average_synthetic_cost_burden,
                   AVG(prior_authorization_yn_flag) prior_authorization_rate,
                   AVG(step_therapy_yn_flag) step_therapy_rate,
                   AVG(quantity_limit_yn_flag) quantity_limit_rate
            FROM prescriber_member_medications_all_v2_3
            WHERE {' AND '.join(clauses)} GROUP BY prescriber_id
        """, params)

    def medication_breakdown(self, generation_version, prescriber_id, plan_key, rxcui, limit, offset):
        where_sql, params = self._analysis_filters(
            generation_version, plan_key=plan_key, prescriber_id=prescriber_id, rxcui=rxcui
        )
        params.update({"limit": limit, "offset": offset})
        return rows(self.engine, f"""
            SELECT analysis.* FROM prescriber_formulary_analysis_all_v2_3 analysis
            WHERE {where_sql}
            ORDER BY analysis.assignment_exposure_count DESC,
                     analysis.plan_key, analysis.rxcui
            LIMIT :limit OFFSET :offset
        """, params)
