import numpy as np

from backend.ml.model_loader import LoadedModel
from backend.ml.predictor import predict
from backend.tests.test_feature_contract import valid_frame


class FakePipeline:
    def predict_proba(self, frame):
        assert len(frame) == 1
        return np.array([[0.30, 0.70]])


def test_predictor_uses_registered_threshold():
    model = LoadedModel(FakePipeline(), 0.405, "test", "0" * 64, {})
    result = predict(valid_frame(), model)
    assert result.probabilities.tolist() == [0.7]
    assert result.classes.tolist() == [1]

