from __future__ import annotations

import argparse
import getpass
from pathlib import Path

import pandas as pd
import pymysql


TRACE = [
    "member_id", "base_profile_id", "contract_id", "plan_id", "segment_id",
    "plan_key", "generation_version",
]
FEATURES = [
    "age", "chronic_condition_count", "medication_count",
    "historical_member_pdc", "historical_missed_fill_rate",
    "historical_mean_delay_days", "mean_tier_level",
    "prior_authorization_rate", "step_therapy_rate", "quantity_limit_rate",
    "nonpreferred_pharmacy_rate", "mean_synthetic_cost_burden",
]
COLUMNS = TRACE + FEATURES
MEDICATION_COLUMNS = [
    "member_medication_id", "member_id", "base_profile_id", "contract_id",
    "plan_id", "segment_id", "rxcui", "drug_name", "medication_group",
    "assumed_days_supply", "tier_level_value", "prior_authorization_yn",
    "step_therapy_yn", "quantity_limit_yn", "quantity_limit_amount",
    "quantity_limit_days", "pharmacy_number", "pharmacy_zipcode",
    "preferred_pharmacy_yn", "same_zip_pharmacy_yn", "pharmacy_retail",
    "in_area_flag", "synthetic_cost_burden_score", "generation_version",
    "master_seed", "source_class", "tier_num", "prior_authorization_yn_flag",
    "step_therapy_yn_flag", "quantity_limit_yn_flag",
    "preferred_pharmacy_yn_flag",
]
VERSION = "mvp_v2.3-dashboard-01"


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Load the complete dashboard cohort")
    parser.add_argument("--csv", type=Path, required=True)
    parser.add_argument("--medications-csv", type=Path, required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=3306)
    parser.add_argument("--database", required=True)
    parser.add_argument("--user", required=True)
    parser.add_argument("--password")
    return parser.parse_args()


def validate(frame: pd.DataFrame, medications: pd.DataFrame) -> None:
    if list(frame.columns) != COLUMNS:
        raise ValueError(f"Unexpected columns. Expected: {COLUMNS}")
    if len(frame) != 3000 or frame.base_profile_id.nunique() != 1000:
        raise ValueError("Expected 3,000 rows and 1,000 profiles")
    if frame.plan_key.nunique() != 3:
        raise ValueError("Expected three plans")
    if not frame.groupby("base_profile_id").plan_key.nunique().eq(3).all():
        raise ValueError("Every profile must occur under exactly three plans")
    if frame.member_id.duplicated().any():
        raise ValueError("Duplicate member_id")
    if frame.duplicated(["base_profile_id", "plan_key"]).any():
        raise ValueError("Duplicate base_profile_id/plan_key")
    if frame[FEATURES].isna().any().any():
        raise ValueError("Null model feature")
    if set(frame.generation_version) != {VERSION}:
        raise ValueError("Unexpected generation_version")
    if list(medications.columns) != MEDICATION_COLUMNS:
        raise ValueError("Unexpected medication columns")
    if len(medications) != 5343 or medications.member_id.nunique() != 3000:
        raise ValueError("Expected 5,343 medication rows covering 3,000 members")
    if set(medications.member_id) != set(frame.member_id):
        raise ValueError("Medication member identifiers do not match scoring cohort")
    if medications.member_medication_id.duplicated().any():
        raise ValueError("Duplicate member_medication_id")


def records(frame: pd.DataFrame, columns: list[str]) -> list[tuple]:
    safe = frame[columns].astype(object).where(frame[columns].notna(), None)
    return list(safe.itertuples(index=False, name=None))


def main() -> None:
    args = arguments()
    frame = pd.read_csv(
        args.csv.resolve(), dtype={column: "string" for column in TRACE}
    )
    medication_ids = [
        "member_medication_id", "member_id", "base_profile_id", "contract_id",
        "plan_id", "segment_id", "rxcui", "pharmacy_number",
        "pharmacy_zipcode", "generation_version",
    ]
    medications = pd.read_csv(
        args.medications_csv.resolve(),
        dtype={column: "string" for column in medication_ids},
    )
    validate(frame, medications)
    password = args.password or getpass.getpass("MySQL password: ")
    connection = pymysql.connect(
        host=args.host, port=args.port, user=args.user, password=password,
        database=args.database, charset="utf8mb4", autocommit=False,
    )
    feature_sql = (
        f"INSERT INTO ml_dashboard_scoring_features_v2_3 ({', '.join(COLUMNS)}) "
        f"VALUES ({', '.join(['%s'] * len(COLUMNS))})"
    )
    medication_sql = (
        "INSERT INTO dashboard_member_medications_v2_3 "
        f"({', '.join(MEDICATION_COLUMNS)}) "
        f"VALUES ({', '.join(['%s'] * len(MEDICATION_COLUMNS))})"
    )
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "DELETE FROM dashboard_member_medications_v2_3 "
                "WHERE generation_version=%s", (VERSION,)
            )
            cursor.execute(
                "DELETE FROM ml_dashboard_scoring_features_v2_3 "
                "WHERE generation_version=%s", (VERSION,)
            )
            feature_records = records(frame, COLUMNS)
            for start in range(0, len(feature_records), 500):
                cursor.executemany(feature_sql, feature_records[start:start + 500])
            medication_records = records(medications, MEDICATION_COLUMNS)
            for start in range(0, len(medication_records), 500):
                cursor.executemany(
                    medication_sql, medication_records[start:start + 500]
                )
            cursor.execute("""
                SELECT COUNT(*), COUNT(DISTINCT base_profile_id),
                       COUNT(DISTINCT plan_key)
                FROM ml_adherence_dashboard_scoring_view_v2_3
            """)
            counts = cursor.fetchone()
            if counts != (3000, 1000, 3):
                raise RuntimeError(f"Post-load validation failed: {counts}")
            cursor.execute("""
                SELECT COUNT(*), COUNT(DISTINCT member_id)
                FROM dashboard_member_medications_v2_3
                WHERE generation_version=%s
            """, (VERSION,))
            medication_counts = cursor.fetchone()
            if medication_counts != (5343, 3000):
                raise RuntimeError(
                    f"Medication post-load validation failed: {medication_counts}"
                )
        connection.commit()
        print({
            "status": "PASS", "rows": counts[0], "profiles": counts[1],
            "plans": counts[2], "medication_rows": medication_counts[0],
        })
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


if __name__ == "__main__":
    main()
