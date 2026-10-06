import sys
from pathlib import Path
from types import ModuleType

import pytest
from fastapi.testclient import TestClient

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

planner_module = ModuleType("planner")
planner_module.AdaptivePlanner = lambda: None
selector_module = ModuleType("mitigation_selector")
selector_module.MitigationSelector = object
previous_modules = {
    name: sys.modules.get(name)
    for name in ("planner", "mitigation_selector")
}
sys.modules["planner"] = planner_module
sys.modules["mitigation_selector"] = selector_module
try:
    from app import main
finally:
    for name, previous_module in previous_modules.items():
        if previous_module is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = previous_module


class FakeCollection:
    def __init__(self, documents=()):
        self.documents = documents

    def find(self, query=None, projection=None):
        query = query or {}
        records = [
            document
            for document in self.documents
            if all(document.get(key) == value for key, value in query.items())
        ]
        if projection == {"_id": 0}:
            return [
                {
                    key: value
                    for key, value in document.items()
                    if key != "_id"
                }
                for document in records
            ]
        return records

    def count_documents(self, query):
        return 0


class FakeDatabase:
    def __init__(self, evaluation_results=()):
        self.evaluation_results = FakeCollection(evaluation_results)
        self.experiments = FakeCollection()
        self.findings = FakeCollection()
        self.attack_chains = FakeCollection()


@pytest.fixture
def client():
    return TestClient(main.app)


def test_run_phase2_evaluation_calls_runner_and_persister_once(
    client,
    monkeypatch,
):
    records = [
        {"experiment_id": "P2-RULE-001", "condition": "rule_based_fixed_mitigation"},
        {"experiment_id": "P2-LLM-001", "condition": "llm_recommendation_only"},
    ]
    runner_calls = []
    persistence_calls = []

    def fake_runner():
        runner_calls.append(True)
        return records

    def fake_persist(persisted_records):
        persistence_calls.append(persisted_records)
        return 1

    monkeypatch.setattr(main, "run_all_phase2_experiments", fake_runner)
    monkeypatch.setattr(
        main,
        "persist_phase2_condition_records",
        fake_persist,
    )

    response = client.post("/phase2/evaluation/run")

    assert response.status_code == 200
    assert response.json() == {
        "status": "completed",
        "records_generated": 2,
        "records_persisted": 1,
    }
    assert len(runner_calls) == 1
    assert len(persistence_calls) == 1
    assert persistence_calls[0] is records


def test_run_phase2_evaluation_returns_500_when_runner_fails(
    client,
    monkeypatch,
):
    persistence_calls = []

    def failing_runner():
        raise RuntimeError("runner failure")

    monkeypatch.setattr(main, "run_all_phase2_experiments", failing_runner)
    monkeypatch.setattr(
        main,
        "persist_phase2_condition_records",
        lambda records: persistence_calls.append(records),
    )

    response = client.post("/phase2/evaluation/run")

    assert response.status_code == 500
    assert response.json()["detail"] == "Phase 2 evaluation run failed"
    assert persistence_calls == []


def test_run_phase2_evaluation_returns_500_when_persistence_fails(
    client,
    monkeypatch,
):
    records = [{"experiment_id": "P2-RULE-001"}]
    runner_calls = []

    def fake_runner():
        runner_calls.append(True)
        return records

    def failing_persist(persisted_records):
        assert persisted_records is records
        raise RuntimeError("persistence failure")

    monkeypatch.setattr(main, "run_all_phase2_experiments", fake_runner)
    monkeypatch.setattr(
        main,
        "persist_phase2_condition_records",
        failing_persist,
    )

    response = client.post("/phase2/evaluation/run")

    assert response.status_code == 500
    assert response.json()["detail"] == "Phase 2 evaluation persistence failed"
    assert len(runner_calls) == 1


def test_existing_analytics_routes_do_not_run_phase2_batch(
    client,
    monkeypatch,
):
    monkeypatch.setattr(main, "db", FakeDatabase())

    def unexpected_runner_call():
        pytest.fail("analytics routes must not run Phase 2 experiments")

    monkeypatch.setattr(
        main,
        "run_all_phase2_experiments",
        unexpected_runner_call,
    )

    analytics_response = client.get("/analytics")
    phase2_analytics_response = client.get("/phase2/analytics")

    assert analytics_response.status_code == 200
    assert phase2_analytics_response.status_code == 200
    assert analytics_response.json()["total_evaluation_results"] == 0
    assert phase2_analytics_response.json()["records"] == []
    existing_routes = {
        (route.path, method)
        for route in main.app.routes
        for method in route.methods
    }
    assert (
        "/experiments/{experiment_id}/mitigation/apply",
        "POST",
    ) in existing_routes
    assert (
        "/experiments/{experiment_id}/mitigation/replay",
        "POST",
    ) in existing_routes
    assert (
        "/experiments/{experiment_id}/mitigation/result",
        "GET",
    ) in existing_routes


def test_phase2_analytics_returns_metrics_for_all_four_conditions(
    client,
    monkeypatch,
):
    conditions = [
        "rule_based_fixed_mitigation",
        "llm_recommendation_only",
        "level3_proposed",
        "wrong_control",
    ]
    records = [
        {
            "experiment_id": f"P2-{index}",
            "evaluation_type": "phase2_condition",
            "source": "phase2_condition_runner",
            "timestamp": "2026-10-06T00:00:00+00:00",
            "condition": condition,
            "selection_correct": True,
            "mitigation_control": "authorization_gate",
            "mitigation_applied": condition != "llm_recommendation_only",
            "attack_success_before": (
                None if condition == "llm_recommendation_only" else True
            ),
            "attack_success_after": (
                None if condition == "llm_recommendation_only" else False
            ),
            "chain_disrupted": condition != "llm_recommendation_only",
            "mitigation_validation": condition != "llm_recommendation_only",
            "residual_vulnerable_steps": [],
            "llm_calls": 0 if index == 0 else 1,
        }
        for index, condition in enumerate(conditions)
    ]
    monkeypatch.setattr(main, "db", FakeDatabase(records))

    response = client.get("/phase2/analytics")

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"metrics", "records"}
    assert set(body["metrics"]) == set(conditions)
    assert body["records"] == records


def test_phase2_analytics_returns_empty_metrics_and_records(
    client,
    monkeypatch,
):
    monkeypatch.setattr(main, "db", FakeDatabase())

    response = client.get("/phase2/analytics")

    assert response.status_code == 200
    assert response.json() == {"metrics": {}, "records": []}


def test_phase2_analytics_excludes_unrelated_and_legacy_records(
    client,
    monkeypatch,
):
    phase2_condition_record = {
        "experiment_id": "P2-RULE-001",
        "evaluation_type": "phase2_condition",
        "source": "phase2_condition_runner",
        "timestamp": "2026-10-06T00:00:00+00:00",
        "condition": "rule_based_fixed_mitigation",
        "selection_correct": True,
        "mitigation_control": "authorization_gate",
        "mitigation_applied": True,
        "attack_success_before": True,
        "attack_success_after": False,
        "chain_disrupted": True,
        "mitigation_validation": True,
        "residual_vulnerable_steps": [],
        "llm_calls": 0,
    }
    records = [
        phase2_condition_record,
        {
            "experiment_id": "LEGACY",
            "evaluation_type": "phase2_mitigation",
            "source": "legacy",
            "condition": "rule_based_fixed_mitigation",
        },
        {
            "experiment_id": "OTHER",
            "evaluation_type": "phase1_validation",
            "source": "phase2_condition_runner",
        },
        {
            "experiment_id": "OTHER-SOURCE",
            "evaluation_type": "phase2_condition",
            "source": "other_runner",
        },
    ]
    monkeypatch.setattr(main, "db", FakeDatabase(records))

    response = client.get("/phase2/analytics")

    assert response.status_code == 200
    assert response.json()["records"] == [phase2_condition_record]
    assert list(response.json()["metrics"]) == ["rule_based_fixed_mitigation"]