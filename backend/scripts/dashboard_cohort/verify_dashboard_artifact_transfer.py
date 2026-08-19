"""Evaluate the saved selected artifact against the isolated dashboard audit.

This script is an offline verification tool. The audit outcome is never passed
to the model and should not be loaded into the production scoring view.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd
from sklearn.metrics import accuracy_score, balanced_accuracy_score, confusion_matrix

from backend.ml.model_loader import load_model
from backend.ml.predictor import predict


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scoring-csv", required=True, type=Path)
    parser.add_argument("--audit-csv", required=True, type=Path)
    parser.add_argument("--output-json", type=Path)
    return parser.parse_args()


def main() -> None:
    args = arguments()
    scoring = pd.read_csv(
        args.scoring_csv.resolve(),
        dtype={
            "member_id": "string",
            "base_profile_id": "string",
            "contract_id": "string",
            "plan_id": "string",
            "segment_id": "string",
            "plan_key": "string",
            "generation_version": "string",
        },
    )
    audit = pd.read_csv(
        args.audit_csv.resolve(),
        dtype={"member_id": "string", "plan_key": "string"},
    )
    if "non_adherent" not in audit.columns:
        raise ValueError("Audit CSV must contain non_adherent")
    if "non_adherent" in scoring.columns or "future_member_pdc" in scoring.columns:
        raise ValueError("Scoring CSV contains a prohibited outcome field")
    if scoring["member_id"].duplicated().any() or audit["member_id"].duplicated().any():
        raise ValueError("member_id must be unique in both files")

    result = predict(scoring, load_model())
    predictions = scoring[["member_id", "plan_key"]].copy()
    predictions["predicted_class"] = result.classes.astype(int)
    predictions["predicted_probability"] = result.probabilities.astype(float)
    joined = predictions.merge(
        audit[["member_id", "non_adherent"]],
        on="member_id",
        how="inner",
        validate="one_to_one",
    )
    if len(joined) != len(scoring):
        raise ValueError("Scoring and audit member sets do not match")

    actual = joined["non_adherent"].astype(int)
    predicted = joined["predicted_class"].astype(int)
    tn, fp, fn, tp = confusion_matrix(actual, predicted, labels=[0, 1]).ravel()

    per_plan = {}
    for plan_key, frame in joined.groupby("plan_key", sort=True):
        plan_actual = frame["non_adherent"].astype(int)
        plan_predicted = frame["predicted_class"].astype(int)
        ptn, pfp, pfn, ptp = confusion_matrix(
            plan_actual, plan_predicted, labels=[0, 1]
        ).ravel()
        per_plan[str(plan_key)] = {
            "rows": int(len(frame)),
            "flagged_count": int(plan_predicted.sum()),
            "accuracy": float(accuracy_score(plan_actual, plan_predicted)),
            "balanced_accuracy": float(
                balanced_accuracy_score(plan_actual, plan_predicted)
            ),
            "tn": int(ptn),
            "fp": int(pfp),
            "fn": int(pfn),
            "tp": int(ptp),
        }

    report = {
        "status": "PASS",
        "purpose": "selected saved artifact transfer verification",
        "rows": int(len(joined)),
        "threshold": float(result.threshold),
        "flagged_count": int(predicted.sum()),
        "accuracy": float(accuracy_score(actual, predicted)),
        "balanced_accuracy": float(balanced_accuracy_score(actual, predicted)),
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "tp": int(tp),
        "per_plan": per_plan,
    }
    rendered = json.dumps(report, indent=2)
    print(rendered)
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(rendered + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
