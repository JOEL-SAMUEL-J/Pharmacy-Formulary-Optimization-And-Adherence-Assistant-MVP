CREATE OR REPLACE VIEW prescriber_member_medications_all_v2_3 AS
SELECT m.generation_version, m.member_medication_id, m.member_id,
       m.base_profile_id, m.contract_id, m.plan_id, m.segment_id,
       CONCAT(m.contract_id, '|', m.plan_id, '|', m.segment_id) AS plan_key,
       m.prescriber_id, p.prescriber_display_name, p.specialty,
       p.prescriber_region, p.prescriber_zipcode, p.prescriber_volume_weight,
       m.rxcui, m.drug_name, m.tier_num,
       m.synthetic_cost_burden_score,
       m.prior_authorization_yn_flag, m.step_therapy_yn_flag,
       m.quantity_limit_yn_flag, m.preferred_pharmacy_yn_flag
FROM syn_member_medications_v2_3 m
JOIN syn_prescribers_v2_3 p
  ON p.generation_version=m.generation_version
 AND p.prescriber_id=m.prescriber_id
UNION ALL
SELECT m.generation_version, m.member_medication_id, m.member_id,
       m.base_profile_id, m.contract_id, m.plan_id, m.segment_id,
       CONCAT(m.contract_id, '|', m.plan_id, '|', m.segment_id),
       a.prescriber_id, p.prescriber_display_name, p.specialty,
       p.prescriber_region, p.prescriber_zipcode, p.prescriber_volume_weight,
       m.rxcui, m.drug_name, m.tier_num,
       m.synthetic_cost_burden_score,
       m.prior_authorization_yn_flag, m.step_therapy_yn_flag,
       m.quantity_limit_yn_flag, m.preferred_pharmacy_yn_flag
FROM dashboard_member_medications_v2_3 m
JOIN dashboard_base_profile_prescribers_v2_3 a
  ON a.generation_version=m.generation_version
 AND a.base_profile_id=m.base_profile_id AND a.rxcui=m.rxcui
JOIN syn_prescribers_v2_3 p
  ON p.generation_version=a.prescriber_generation_version
 AND p.prescriber_id=a.prescriber_id;

SELECT COUNT(*) AS dashboard_detail_rows
FROM prescriber_member_medications_all_v2_3
WHERE generation_version='mvp_v2.3-dashboard-01';
