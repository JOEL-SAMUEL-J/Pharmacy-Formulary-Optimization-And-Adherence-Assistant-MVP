from sqlalchemy import inspect, text

from backend.db.session import get_engine


REQUIRED_OBJECTS = {
    "syn_base_profiles_v2_3",
    "syn_members_v2_3",
    "syn_member_medications_v2_3",
    "syn_fill_events_v2_3",
    "syn_member_features_v2_3",
    "ml_adherence_training_view_v2_3",
    "ml_model_runs",
    "ml_adherence_predictions",
    "dashboard_plan_kpis",
}


def main() -> None:
    engine = get_engine()
    inspector = inspect(engine)
    objects = set(inspector.get_table_names()) | set(inspector.get_view_names())
    missing = sorted(REQUIRED_OBJECTS - objects)
    if missing:
        raise SystemExit(f"FAIL: missing database objects: {missing}")
    with engine.connect() as connection:
        counts = connection.execute(text("""
            SELECT COUNT(*) rows_count, COUNT(DISTINCT base_profile_id) profiles,
                   COUNT(DISTINCT plan_key) plans
            FROM ml_adherence_training_view_v2_3
        """)).mappings().one()
    print({"status": "PASS", **dict(counts)})


if __name__ == "__main__":
    main()

