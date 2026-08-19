from backend.core.constants import FEATURE_COLUMNS
from backend.ml.model_loader import load_model


def main() -> None:
    model = load_model()
    print({
        "status": "PASS",
        "model_run": model.run_name,
        "threshold": model.threshold,
        "artifact_sha256": model.artifact_sha256,
        "feature_count": len(FEATURE_COLUMNS),
    })


if __name__ == "__main__":
    main()

