"""Standalone acceptance check for the Step 1 generated CSVs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prescribers", required=True, type=Path)
    parser.add_argument("--assignments", required=True, type=Path)
    parser.add_argument("--medications", required=True, type=Path)
    args = parser.parse_args()

    prescribers = pd.read_csv(args.prescribers, dtype="string")
    assignments = pd.read_csv(args.assignments, dtype="string")
    medications = pd.read_csv(args.medications, sep=";", dtype="string")
    keys = ["generation_version", "base_profile_id", "rxcui"]

    counts = medications.groupby(keys).agg(
        rows=("member_medication_id", "size"),
        prescribers=("prescriber_id", "nunique"),
    )
    checks = {
        "prescriber_rows": len(prescribers),
        "unique_prescribers": prescribers["prescriber_id"].nunique(),
        "assignment_rows": len(assignments),
        "unique_assignments": len(assignments.drop_duplicates(keys)),
        "medication_rows": len(medications),
        "null_medication_prescribers": int(medications["prescriber_id"].isna().sum()),
        "pairs_not_repeated_three_times": int((counts["rows"] != 3).sum()),
        "pairs_with_multiple_prescribers": int((counts["prescribers"] != 1).sum()),
        "orphan_assignment_prescribers": int(
            (~assignments["prescriber_id"].isin(prescribers["prescriber_id"])).sum()
        ),
    }
    checks["status"] = "PASS" if checks == {
        "prescriber_rows": 60,
        "unique_prescribers": 60,
        "assignment_rows": 1781,
        "unique_assignments": 1781,
        "medication_rows": 5343,
        "null_medication_prescribers": 0,
        "pairs_not_repeated_three_times": 0,
        "pairs_with_multiple_prescribers": 0,
        "orphan_assignment_prescribers": 0,
    } else "FAIL"
    print(json.dumps(checks, indent=2))
    if checks["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
