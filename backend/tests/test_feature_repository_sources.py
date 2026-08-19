from types import SimpleNamespace

import pytest

import backend.repositories.feature_repository as module
from backend.repositories.feature_repository import FeatureRepository


class FakeConnection:
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


class FakeEngine:
    def connect(self):
        return FakeConnection()


@pytest.mark.parametrize(
    ("generation_version", "expected_view"),
    [
        ("mvp_v2.3", "ml_adherence_training_view_v2_3"),
        (
            "mvp_v2.3-dashboard-01",
            "ml_adherence_dashboard_scoring_view_v2_3",
        ),
    ],
)
def test_generation_uses_allowlisted_scoring_view(
    monkeypatch, generation_version, expected_view
):
    captured = {}

    def fake_read_sql(query, _connection, params):
        captured["query"] = str(query)
        captured["params"] = params
        return SimpleNamespace()

    monkeypatch.setattr(module.pd, "read_sql", fake_read_sql)
    FeatureRepository(FakeEngine()).scoring_frame(generation_version)

    assert expected_view in captured["query"]
    assert ":generation_version" in captured["query"]
    assert captured["params"] == {"generation_version": generation_version}


def test_unknown_generation_is_rejected_before_query(monkeypatch):
    monkeypatch.setattr(
        module.pd,
        "read_sql",
        lambda *_args, **_kwargs: pytest.fail("query should not execute"),
    )
    with pytest.raises(ValueError, match="Unsupported generation_version"):
        FeatureRepository(FakeEngine()).scoring_frame("unknown-generation")
