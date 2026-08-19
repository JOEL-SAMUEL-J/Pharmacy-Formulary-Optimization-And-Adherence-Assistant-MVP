import backend.repositories.prescriber_repository as module
from backend.repositories.prescriber_repository import PrescriberRepository


def test_repository_uses_bound_parameters_for_filters(monkeypatch):
    captured = {}

    def fake_rows(_engine, sql, params):
        captured["sql"] = sql
        captured["params"] = params
        return []

    monkeypatch.setattr(module, "rows", fake_rows)
    repository = PrescriberRepository(object())
    repository.list_prescribers(
        generation_version="mvp_v2.3",
        plan_key="S4802|138|000",
        rxcui="1048450",
        specialty="Primary Care",
        limit=25,
        offset=10,
    )

    assert ":generation_version" in captured["sql"]
    assert ":plan_key" in captured["sql"]
    assert ":rxcui" in captured["sql"]
    assert ":specialty" in captured["sql"]
    assert "S4802|138|000" not in captured["sql"]
    assert captured["params"] == {
        "generation_version": "mvp_v2.3",
        "plan_key": "S4802|138|000",
        "rxcui": "1048450",
        "specialty": "Primary Care",
        "limit": 25,
        "offset": 10,
    }


def test_medication_query_has_stable_order_and_pagination(monkeypatch):
    captured = {}

    def fake_rows(_engine, sql, params):
        captured["sql"] = sql
        captured["params"] = params
        return []

    monkeypatch.setattr(module, "rows", fake_rows)
    PrescriberRepository(object()).medication_breakdown(
        "mvp_v2.3", "PR00001", None, None, 20, 0
    )
    assert "ORDER BY" in captured["sql"]
    assert "LIMIT :limit OFFSET :offset" in captured["sql"]
    assert captured["params"]["prescriber_id"] == "PR00001"
