import hashlib
import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import joblib

from backend.core.config import get_settings
from backend.core.exceptions import ModelUnavailableError


@dataclass(frozen=True)
class LoadedModel:
    pipeline: Any
    threshold: float
    run_name: str
    artifact_sha256: str
    metadata: dict


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


@lru_cache
def load_model() -> LoadedModel:
    settings = get_settings()
    if not settings.model_path.is_file():
        raise ModelUnavailableError(f"Model artifact not found: {settings.model_path}")
    metadata = {}
    if settings.model_metadata_path.is_file():
        metadata = json.loads(settings.model_metadata_path.read_text(encoding="utf-8"))
    selected = metadata.get("primary_model_a_selected", {})
    threshold = float(selected.get("selected_threshold", settings.model_threshold))
    pipeline = joblib.load(settings.model_path)
    if not hasattr(pipeline, "predict_proba"):
        raise ModelUnavailableError("Configured artifact does not support predict_proba")
    return LoadedModel(
        pipeline=pipeline,
        threshold=threshold,
        run_name=settings.model_run_name,
        artifact_sha256=sha256_file(settings.model_path),
        metadata=metadata,
    )

