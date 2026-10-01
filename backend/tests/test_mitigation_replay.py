import sys
from copy import deepcopy
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

from app.schemas import MitigationResultResponse


class FakeCollection:
    def __init__(self, documents=()):
        self.documents = [deepcopy(document) for document in documents]

    def find_one(self, query, projection=None):
        for document in self.documents:
            if all(document.get(key) == value for key, value in query.items()):
                return deepcopy(document)
        return None

    def update_one(self, query, update):
        for document in self.documents:
            if all(document.get(key) == value for key, value in query.items()):
                document.update(deepcopy(update.get("$set", {})))
                return

    def insert_one(self, document):
        self.documents.append(deepcopy(document))

    def find(self, query=None, projection=None):
        query = query or {}
        return [
            deepcopy(document)
            for document in self.documents
            if all(document.get(key) == value for key, value in query.items())
        ]

    def count_documents(self, query):
        return sum(
            all(document.get(key) == value for key, value in query.items())
            for document in self.documents
        )


class FakeDatabase:
    def __init__(self):
        self.experiments = FakeCollection(
            [
                {
                    "experiment_id": "EXP001",
                    "name": "test experiment",
                    "mode": "adaptive",
                    "max_tests": 1,
                    "status": "created",
                }
            ]
        )
        self.mitigation_runs = FakeCollection(
            [
                {
                    "mitigation_run_id": "MIT-1234abcd",
                    "experiment_id": "EXP001",
                    "chain_id": "CHAIN001",
                    "status": "applied",
                    "selection": {"selected_control": "tool_allowlist"},
                    "application": {"status": "applied"},
                }
            ]
        )
        self.findings = FakeCollection()
        self.attack_chains = FakeCollection()
        self.evaluation_results = FakeCollection()


def complete_p4_result(
    test="tool_access_test",
    control="tool_allowlist",
    **overrides,
):
    result = {
        "status": "completed",
        "experiment_id": "EXP001",
        "test": test,
        "control": control,
        "before": {"status": "completed", "finding": "unsafe_tool_access"},
        "after": {"status": "completed", "finding": None},
        "activation": {"status": "applied", "control": control},
        "attack_disrupted": True,
        "before_validation": {"status": "validated"},
        "after_validation": {"status": "invalid"},
        "disrupted": True,
        "residual_vulnerable_steps": ["permission_test"],
        "validation_result": {"all_findings_reproduced": False},
    }
    result.update(overrides)
    return result


@pytest.fixture
def replay_context(monkeypatch):
    fake_database = FakeDatabase()
    p4_calls = []

    def fake_replay_attack(experiment_id, test_name, control_name):
        p4_calls.append((experiment_id, test_name, control_name))
        return complete_p4_result(test_name, control_name)

    monkeypatch.setattr(main, "db", fake_database)
    monkeypatch.setattr(main.mitigation_repository, "db", fake_database)
    monkeypatch.setattr(main, "replay_attack", fake_replay_attack)

    return TestClient(main.app), fake_database, p4_calls


def replay_payload(
    mitigation_run_id="MIT-1234abcd",
    test="tool_access_test",
):
    return {"mitigation_run_id": mitigation_run_id, "test": test}


def test_successful_replay(replay_context):
    client, _, p4_calls = replay_context

    response = client.post(
        "/experiments/EXP001/mitigation/replay",
        json=replay_payload(),
    )

    assert response.status_code == 200
    assert response.json() == {
        "test": "tool_access_test",
        "before_result": {
            "status": "completed",
            "finding": "unsafe_tool_access",
        },
        "after_result": {"status": "completed", "finding": None},
        "blocked_after_mitigation": True,
    }
    assert p4_calls == [
        ("EXP001", "tool_access_test", "tool_allowlist")
    ]


@pytest.mark.parametrize(
    ("control", "test"),
    [
        ("authorization_gate", "permission_test"),
        ("tool_allowlist", "tool_access_test"),
        ("memory_validation", "memory_access_test"),
    ],
)
def test_all_valid_control_test_mappings(
    replay_context,
    control,
    test,
):
    client, fake_database, p4_calls = replay_context
    run = fake_database.mitigation_runs.documents[0]
    run["selection"]["selected_control"] = control
    run["application"] = {"status": "applied"}

    response = client.post(
        "/experiments/EXP001/mitigation/replay",
        json=replay_payload(test=test),
    )

    assert response.status_code == 200
    assert response.json()["test"] == test
    assert p4_calls == [("EXP001", test, control)]


def test_missing_experiment(replay_context):
    client, fake_database, p4_calls = replay_context
    fake_database.experiments.documents.clear()

    response = client.post(
        "/experiments/MISSING/mitigation/replay",
        json=replay_payload(),
    )

    assert response.status_code == 404
    assert p4_calls == []


def test_missing_mitigation_run(replay_context):
    client, fake_database, p4_calls = replay_context
    fake_database.mitigation_runs.documents.clear()

    response = client.post(
        "/experiments/EXP001/mitigation/replay",
        json=replay_payload(),
    )

    assert response.status_code == 404
    assert p4_calls == []


def test_cross_experiment_mitigation_run(replay_context):
    client, fake_database, p4_calls = replay_context
    fake_database.mitigation_runs.documents[0]["experiment_id"] = "EXP999"

    response = client.post(
        "/experiments/EXP001/mitigation/replay",
        json=replay_payload(),
    )

    assert response.status_code == 404
    assert p4_calls == []


def test_missing_mitigation_selection(replay_context):
    client, fake_database, p4_calls = replay_context
    fake_database.mitigation_runs.documents[0].pop("selection")

    response = client.post(
        "/experiments/EXP001/mitigation/replay",
        json=replay_payload(),
    )

    assert response.status_code == 409
    assert p4_calls == []


def test_control_not_applied(replay_context):
    client, fake_database, p4_calls = replay_context
    fake_database.mitigation_runs.documents[0]["status"] = "selected"
    fake_database.mitigation_runs.documents[0]["application"] = {
        "status": "failed"
    }

    response = client.post(
        "/experiments/EXP001/mitigation/replay",
        json=replay_payload(),
    )

    assert response.status_code == 409
    assert p4_calls == []


def test_invalid_stored_control(replay_context):
    client, fake_database, p4_calls = replay_context
    fake_database.mitigation_runs.documents[0]["selection"][
        "selected_control"
    ] = "arbitrary_patch"

    response = client.post(
        "/experiments/EXP001/mitigation/replay",
        json=replay_payload(),
    )

    assert response.status_code == 409
    assert p4_calls == []


def test_invalid_control_test_combination(replay_context):
    client, _, p4_calls = replay_context

    response = client.post(
        "/experiments/EXP001/mitigation/replay",
        json=replay_payload(test="permission_test"),
    )

    assert response.status_code == 409
    assert p4_calls == []


def test_p4_replay_exception_does_not_persist(replay_context, monkeypatch):
    client, fake_database, p4_calls = replay_context

    def failed_replay(experiment_id, test_name, control_name):
        p4_calls.append((experiment_id, test_name, control_name))
        raise RuntimeError("replay failed")

    monkeypatch.setattr(main, "replay_attack", failed_replay)

    response = client.post(
        "/experiments/EXP001/mitigation/replay",
        json=replay_payload(),
    )

    assert response.status_code == 502
    run = fake_database.mitigation_runs.documents[0]
    assert run["status"] == "applied"
    assert "replay" not in run
    assert "disruption" not in run


def test_invalid_p4_response_does_not_persist(replay_context, monkeypatch):
    client, fake_database, _ = replay_context
    monkeypatch.setattr(
        main,
        "replay_attack",
        lambda experiment_id, test_name, control_name: {
            "status": "completed",
            "before": {},
            "after": {},
            "attack_disrupted": True,
        },
    )

    response = client.post(
        "/experiments/EXP001/mitigation/replay",
        json=replay_payload(),
    )

    assert response.status_code == 502
    run = fake_database.mitigation_runs.documents[0]
    assert run["status"] == "applied"
    assert "replay" not in run
    assert "disruption" not in run


def test_non_completed_p4_response_does_not_persist(
    replay_context,
    monkeypatch,
):
    client, fake_database, _ = replay_context
    monkeypatch.setattr(
        main,
        "replay_attack",
        lambda experiment_id, test_name, control_name: {
            "status": "failed",
            "before": {},
            "after": {},
            "before_validation": {},
            "after_validation": {},
            "disrupted": False,
            "residual_vulnerable_steps": [],
            "validation_result": {},
        },
    )

    response = client.post(
        "/experiments/EXP001/mitigation/replay",
        json=replay_payload(),
    )

    assert response.status_code == 502
    run = fake_database.mitigation_runs.documents[0]
    assert run["status"] == "applied"
    assert "replay" not in run
    assert "disruption" not in run


def test_replay_and_disruption_persistence(replay_context):
    client, fake_database, _ = replay_context

    response = client.post(
        "/experiments/EXP001/mitigation/replay",
        json=replay_payload(),
    )

    assert response.status_code == 200
    run = fake_database.mitigation_runs.documents[0]
    assert run["status"] == "completed"
    assert run["replay"]["test"] == "tool_access_test"
    assert run["replay"]["before_result"]["finding"] == "unsafe_tool_access"
    assert run["replay"]["after_result"]["finding"] is None
    assert run["replay"]["blocked_after_mitigation"] is True
    assert run["replay"]["replayed_at"]
    assert run["disruption"] == {
        "chain_id": "CHAIN001",
        "before_validation": {"status": "validated"},
        "after_validation": {"status": "invalid"},
        "disrupted": True,
        "residual_vulnerable_steps": ["permission_test"],
        "validation_result": {"all_findings_reproduced": False},
    }


def test_successful_replay_persists_phase2_record_without_overwriting_phase1(
    replay_context,
):
    client, fake_database, _ = replay_context
    phase1_record = {
        "experiment_id": "EXP000",
        "chain_id": "CHAIN-PHASE1",
        "status": "validated",
        "validated_steps": 1,
        "total_steps": 1,
        "steps": [],
        "timestamp": "2026-10-01T11:00:00+00:00",
    }
    fake_database.evaluation_results.insert_one(phase1_record)

    response = client.post(
        "/experiments/EXP001/mitigation/replay",
        json=replay_payload(),
    )

    assert response.status_code == 200
    assert fake_database.evaluation_results.documents[0] == phase1_record
    phase2_records = fake_database.evaluation_results.find(
        {"evaluation_type": "phase2_mitigation"}
    )
    assert len(phase2_records) == 1
    assert phase2_records[0]["evaluation_type"] == "phase2_mitigation"
    assert phase2_records[0]["experiment_id"] == "EXP001"
    assert phase2_records[0]["timestamp"]
    assert phase2_records[0]["mitigation_control"] == "tool_allowlist"


def test_analytics_aggregates_only_phase2_mitigation_records(replay_context):
    client, fake_database, _ = replay_context
    phase1_record = {
        "experiment_id": "EXP000",
        "chain_id": "CHAIN-PHASE1",
        "status": "validated",
        "validated_steps": 1,
        "total_steps": 1,
        "steps": [],
        "timestamp": "2026-10-01T11:00:00+00:00",
    }
    fake_database.evaluation_results.insert_one(phase1_record)

    replay_response = client.post(
        "/experiments/EXP001/mitigation/replay",
        json=replay_payload(),
    )
    assert replay_response.status_code == 200

    response = client.get("/analytics")

    assert response.status_code == 200
    body = response.json()
    assert body["total_evaluation_results"] == 2
    assert "mitigation_metrics" in body
    adaptive_metrics = body["mitigation_metrics"]["adaptive"]
    assert adaptive_metrics["mitigation_selections"] == 1
    assert adaptive_metrics["successful_mitigation_applications"] == 1
    assert adaptive_metrics["disrupted_chains"] == 1
    assert fake_database.evaluation_results.documents[0] == phase1_record


def test_phase1_route_smoke_regression(replay_context):
    client, _, _ = replay_context

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert any(
        route.path == "/experiments/{experiment_id}"
        and "GET" in route.methods
        for route in main.app.routes
    )


def test_get_mitigation_result_returns_completed_run(replay_context):
    client, fake_database, _ = replay_context
    run = fake_database.mitigation_runs.documents[0]
    run.update(
        {
            "status": "completed",
            "created_at": "2026-10-01T12:00:00+00:00",
            "updated_at": "2026-10-01T12:05:00+00:00",
            "selection": {
                "selected_control": "tool_allowlist",
                "reason": "Restrict tool access.",
                "confidence": 0.92,
            },
            "application": {
                "selected_control": "tool_allowlist",
                "status": "applied",
                "execution_info": {},
            },
            "replay": {
                "test": "tool_access_test",
                "before_result": {},
                "after_result": {},
                "blocked_after_mitigation": True,
            },
            "disruption": {
                "chain_id": "CHAIN001",
                "before_validation": {},
                "after_validation": {},
                "disrupted": True,
                "residual_vulnerable_steps": [],
                "validation_result": {},
            },
        }
    )

    response = client.get(
        "/experiments/EXP001/mitigation/result",
        params={"mitigation_run_id": "MIT-1234abcd"},
    )

    assert response.status_code == 200
    body = response.json()
    result = MitigationResultResponse.model_validate(body)
    assert body["mitigation_run_id"] == "MIT-1234abcd"
    assert body["experiment_id"] == "EXP001"
    assert body["status"] == "completed"
    assert result.selection.mitigation_run_id == "MIT-1234abcd"
    assert result.selection.selected_control == "tool_allowlist"
    assert result.selection.reason == "Restrict tool access."
    assert result.selection.confidence == 0.92


def test_get_mitigation_result_rejects_incomplete_run(replay_context):
    client, _, _ = replay_context

    response = client.get(
        "/experiments/EXP001/mitigation/result",
        params={"mitigation_run_id": "MIT-1234abcd"},
    )

    assert response.status_code == 409


def test_get_mitigation_result_missing_run_returns_404(replay_context):
    client, _, _ = replay_context

    response = client.get(
        "/experiments/EXP001/mitigation/result",
        params={"mitigation_run_id": "MIT-missing"},
    )

    assert response.status_code == 404


def test_get_mitigation_result_cross_experiment_returns_404(replay_context):
    client, fake_database, _ = replay_context
    fake_database.mitigation_runs.documents[0]["experiment_id"] = "EXP999"

    response = client.get(
        "/experiments/EXP001/mitigation/result",
        params={"mitigation_run_id": "MIT-1234abcd"},
    )

    assert response.status_code == 404


def test_get_mitigation_result_missing_experiment_returns_404(replay_context):
    client, fake_database, _ = replay_context
    fake_database.experiments.documents.clear()

    response = client.get(
        "/experiments/MISSING/mitigation/result",
        params={"mitigation_run_id": "MIT-1234abcd"},
    )

    assert response.status_code == 404