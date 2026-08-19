from dataclasses import dataclass

import numpy as np
import pandas as pd

from backend.ml.input_validator import validated_feature_frame
from backend.ml.model_loader import LoadedModel


@dataclass(frozen=True)
class PredictionBatch:
    probabilities: np.ndarray
    classes: np.ndarray
    threshold: float


def predict(frame: pd.DataFrame, model: LoadedModel) -> PredictionBatch:
    features = validated_feature_frame(frame)
    probabilities = np.asarray(model.pipeline.predict_proba(features)[:, 1], dtype=float)
    if ((probabilities < 0) | (probabilities > 1)).any():
        raise ValueError("Model returned probability outside [0, 1]")
    classes = (probabilities >= model.threshold).astype(int)
    return PredictionBatch(probabilities, classes, model.threshold)

