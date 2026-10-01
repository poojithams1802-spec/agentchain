import sys
from copy import deepcopy
from datetime import datetime
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


class FakeDatabase:
    def __init__(self):
        self.experiments = FakeCollection(
            [
                {
                    "experiment_id": "EXP001",
                    "name": "test experiment",
                    "mode": "test",
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
                    "status": "selected",
                    "selection": {
                        "selected_control": "tool_allowlist",
                        "reason": "test selection",
                        "confidence": 0.92,
                    },
                }
            ]
        )


@pytest.fixture
def apply_context(monkeypatch):
    fake_database = FakeDatabase()
    p4_calls = []

    def fake_apply_mitigation(experiment_id, *, control_name):
        p4_calls.append((experiment_id, control_name))
        return {
            "status": "applied",
            "experiment_id": experiment_id,
            "control": control_name,
            "target": "test target",
            "evidence": {"result": "deterministic"},
        }

    monkeypatch.setattr(main, "db", fake_database)
    monkeypatch.setattr(main.mitigation_repository, "db", fake_database)
    monkeypatch.setattr(main, "apply_mitigation", fake_apply_mitigation)

    return TestClient(main.app), fake_database, p4_calls


def apply_payload(
    mitigation_run_id="MIT-1234abcd",
    selected_control="tool_allowlist",
):
    return {
        "mitigation_run_id": mitigation_run_id,
        "selected_control": selected_control,
    }


def test_valid_apply(apply_context):
    client, _, p4_calls = apply_context

    response = client.post(
        "/experiments/EXP001/mitigation/apply",
        json=apply_payload(),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["selected_control"] == "tool_allowlist"
    assert body["status"] == "applied"
    assert body["execution_info"]["target"] == "test target"
    assert p4_calls == [("EXP001", "tool_allowlist")]


@pytest.mark.parametrize(
    "selected_control",
    ["authorization_gate", "tool_allowlist", "memory_validation"],
)
def test_each_approved_control(apply_context, selected_control):
    client, fake_database, p4_calls = apply_context
    fake_database.mitigation_runs.documents[0]["selection"][
        "selected_control"
    ] = selected_control

    response = client.post(
        "/experiments/EXP001/mitigation/apply",
        json=apply_payload(selected_control=selected_control),
    )

    assert response.status_code == 200
    assert response.json()["selected_control"] == selected_control
    assert p4_calls == [("EXP001", selected_control)]


def test_missing_experiment(apply_context):
    client, fake_database, p4_calls = apply_context
    fake_database.experiments.documents.clear()

    response = client.post(
        "/experiments/MISSING/mitigation/apply",
        json=apply_payload(),
    )

    assert response.status_code == 404
    assert p4_calls == []


def test_missing_mitigation_run(apply_context):
    client, fake_database, p4_calls = apply_context
    fake_database.mitigation_runs.documents.clear()

    response = client.post(
        "/experiments/EXP001/mitigation/apply",
        json=apply_payload(),
    )

    assert response.status_code == 404
    assert p4_calls == []


def test_cross_experiment_mitigation_run(apply_context):
    client, fake_database, p4_calls = apply_context
    fake_database.mitigation_runs.documents[0]["experiment_id"] = "EXP999"

    response = client.post(
        "/experiments/EXP001/mitigation/apply",
        json=apply_payload(),
    )

    assert response.status_code == 404
    assert p4_calls == []


def test_no_selected_control(apply_context):
    client, fake_database, p4_calls = apply_context
    fake_database.mitigation_runs.documents[0].pop("selection")

    response = client.post(
        "/experiments/EXP001/mitigation/apply",
        json=apply_payload(),
    )

    assert response.status_code == 409
    assert p4_calls == []


def test_selected_control_mismatch(apply_context):
    client, _, p4_calls = apply_context

    response = client.post(
        "/experiments/EXP001/mitigation/apply",
        json=apply_payload(selected_control="authorization_gate"),
    )

    assert response.status_code == 409
    assert p4_calls == []


def test_p4_failure_does_not_mark_run_applied(apply_context, monkeypatch):
    client, fake_database, p4_calls = apply_context

    def failed_apply(experiment_id, *, control_name):
        p4_calls.append((experiment_id, control_name))
        return {
            "status": "failed",
            "experiment_id": experiment_id,
            "control": control_name,
            "evidence": "application rejected",
        }

    monkeypatch.setattr(main, "apply_mitigation", failed_apply)

    response = client.post(
        "/experiments/EXP001/mitigation/apply",
        json=apply_payload(),
    )

    assert response.status_code == 502
    mitigation_run = fake_database.mitigation_runs.documents[0]
    assert mitigation_run["status"] == "selected"
    assert "application" not in mitigation_run


def test_p4_exception_does_not_mark_run_applied(apply_context, monkeypatch):
    client, fake_database, p4_calls = apply_context

    def failed_apply(experiment_id, *, control_name):
        p4_calls.append((experiment_id, control_name))
        raise RuntimeError("application failed")

    monkeypatch.setattr(main, "apply_mitigation", failed_apply)

    response = client.post(
        "/experiments/EXP001/mitigation/apply",
        json=apply_payload(),
    )

    assert response.status_code == 502
    assert p4_calls == [("EXP001", "tool_allowlist")]
    mitigation_run = fake_database.mitigation_runs.documents[0]
    assert mitigation_run["status"] == "selected"
    assert "application" not in mitigation_run


def test_corrupt_persisted_control_is_rejected(apply_context):
    client, fake_database, p4_calls = apply_context
    fake_database.mitigation_runs.documents[0]["selection"][
        "selected_control"
    ] = "arbitrary_patch"

    response = client.post(
        "/experiments/EXP001/mitigation/apply",
        json=apply_payload(),
    )

    assert response.status_code == 409
    assert p4_calls == []


def test_application_persistence(apply_context):
    client, fake_database, _ = apply_context

    response = client.post(
        "/experiments/EXP001/mitigation/apply",
        json=apply_payload(),
    )

    assert response.status_code == 200
    mitigation_run = fake_database.mitigation_runs.documents[0]
    application = mitigation_run["application"]
    assert mitigation_run["status"] == "applied"
    assert application["selected_control"] == "tool_allowlist"
    assert application["status"] == "applied"
    assert application["execution_info"]["target"] == "test target"
    assert datetime.fromisoformat(application["applied_at"])


def test_phase1_route_smoke_regression(apply_context):
    client, _, _ = apply_context

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert any(
        route.path == "/experiments/{experiment_id}"
        and "GET" in route.methods
        for route in main.app.routes
    )