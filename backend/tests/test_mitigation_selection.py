import re
import sys
from copy import deepcopy
from pathlib import Path
from types import ModuleType, SimpleNamespace

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

    def insert_one(self, document):
        self.documents.append(deepcopy(document))

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
        self.attack_chains = FakeCollection(
            [
                {
                    "chain_id": "CHAIN001",
                    "experiment_id": "EXP001",
                    "steps": ["permission_test"],
                }
            ]
        )
        self.mitigation_runs = FakeCollection()


class FakeSelector:
    def __init__(self, decision=None, error=None, retrieved_knowledge=None):
        self.decision = decision or SimpleNamespace(
            selected_control="tool_allowlist",
            reason="Tool access should be restricted.",
            confidence=0.92,
            priority=0.8,
        )
        self.error = error
        self.retrieved_knowledge = retrieved_knowledge or [
            "Retrieved mitigation guidance."
        ]
        self.requests = []

    def select(self, request):
        self.requests.append(request)
        if self.error is not None:
            raise self.error
        request.retrieved_knowledge = list(self.retrieved_knowledge)
        return self.decision


@pytest.fixture
def mitigation_context(monkeypatch):
    fake_database = FakeDatabase()
    selector = FakeSelector()

    monkeypatch.setattr(main, "db", fake_database)
    monkeypatch.setattr(main.mitigation_repository, "db", fake_database)
    monkeypatch.setattr(main, "MitigationSelector", lambda: selector)

    return TestClient(main.app), fake_database, selector


def selection_payload():
    return {
        "chain_id": "CHAIN001",
        "finding": "unsafe tool access",
        "severity": "high",
        "evidence": {"tool": "file"},
        "attack_chain": ["permission_test"],
        "chain_context": {"step": 1},
    }


def test_valid_mitigation_selection(mitigation_context):
    client, _, selector = mitigation_context

    response = client.post(
        "/experiments/EXP001/mitigation/select",
        json=selection_payload(),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["mitigation_run_id"]
    assert body["selected_control"] == "tool_allowlist"
    assert body["reason"]
    assert body["confidence"] == 0.92
    assert len(selector.requests) == 1


@pytest.mark.parametrize(
    "selected_control",
    ["authorization_gate", "tool_allowlist", "memory_validation"],
)
def test_each_approved_control(mitigation_context, selected_control):
    client, _, selector = mitigation_context
    selector.decision = SimpleNamespace(
        selected_control=selected_control,
        reason="Approved control.",
        confidence=0.8,
        priority=0.7,
    )

    response = client.post(
        "/experiments/EXP001/mitigation/select",
        json=selection_payload(),
    )

    assert response.status_code == 200
    assert response.json()["selected_control"] == selected_control
    assert len(selector.requests) == 1


def test_missing_experiment(mitigation_context):
    client, fake_database, selector = mitigation_context
    fake_database.experiments.documents.clear()

    response = client.post(
        "/experiments/MISSING/mitigation/select",
        json=selection_payload(),
    )

    assert response.status_code == 404
    assert selector.requests == []


def test_cross_experiment_chain(mitigation_context):
    client, fake_database, selector = mitigation_context
    fake_database.attack_chains.documents[0]["experiment_id"] = "EXP999"

    response = client.post(
        "/experiments/EXP001/mitigation/select",
        json=selection_payload(),
    )

    assert response.status_code == 404
    assert selector.requests == []


def test_mismatched_attack_chain_is_rejected(mitigation_context):
    client, fake_database, selector = mitigation_context
    payload = selection_payload()
    payload["attack_chain"] = ["tool_access_test"]

    response = client.post(
        "/experiments/EXP001/mitigation/select",
        json=payload,
    )

    assert response.status_code == 409
    assert selector.requests == []
    assert fake_database.mitigation_runs.documents == []


def test_invalid_control_from_p3(mitigation_context):
    client, fake_database, selector = mitigation_context
    selector.decision = SimpleNamespace(
        selected_control="arbitrary_patch",
        reason="Invalid control.",
        confidence=0.5,
        priority=0.5,
    )

    response = client.post(
        "/experiments/EXP001/mitigation/select",
        json=selection_payload(),
    )

    assert response.status_code == 502
    assert len(fake_database.mitigation_runs.documents) == 1
    mitigation_run = fake_database.mitigation_runs.documents[0]
    assert mitigation_run["status"] == "created"
    assert "selection" not in mitigation_run


def test_p3_selector_failure(mitigation_context):
    client, fake_database, selector = mitigation_context
    selector.error = RuntimeError("selector unavailable")

    response = client.post(
        "/experiments/EXP001/mitigation/select",
        json=selection_payload(),
    )

    assert response.status_code == 502
    assert len(selector.requests) == 1
    assert len(fake_database.mitigation_runs.documents) == 1
    mitigation_run = fake_database.mitigation_runs.documents[0]
    assert mitigation_run["status"] == "created"
    assert "selection" not in mitigation_run


def test_p2_generates_mitigation_run_id(mitigation_context):
    client, fake_database, selector = mitigation_context

    response = client.post(
        "/experiments/EXP001/mitigation/select",
        json=selection_payload(),
    )

    assert response.status_code == 200
    mitigation_run_id = response.json()["mitigation_run_id"]
    assert re.fullmatch(r"MIT-[0-9a-f]{8}", mitigation_run_id)
    assert fake_database.mitigation_runs.documents[0]["mitigation_run_id"] == (
        mitigation_run_id
    )
    assert not hasattr(selector.decision, "mitigation_run_id")
    assert not hasattr(selector.requests[0], "mitigation_run_id")


def test_selection_persistence(mitigation_context):
    client, fake_database, selector = mitigation_context
    selector.decision = SimpleNamespace(
        selected_control="tool_allowlist",
        reason="test reason",
        confidence=0.92,
        priority=0.8,
    )
    selector.retrieved_knowledge = ["deterministic retrieved knowledge"]

    response = client.post(
        "/experiments/EXP001/mitigation/select",
        json=selection_payload(),
    )

    assert response.status_code == 200
    mitigation_run = fake_database.mitigation_runs.documents[0]
    assert mitigation_run["status"] == "selected"
    assert mitigation_run["selection"] == {
        "selected_control": "tool_allowlist",
        "reason": "test reason",
        "confidence": 0.92,
        "priority": 0.8,
        "retrieved_knowledge": ["deterministic retrieved knowledge"],
    }


def test_phase1_route_smoke_regression(mitigation_context):
    client, _, _ = mitigation_context

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert any(
        route.path == "/experiments/{experiment_id}"
        and "GET" in route.methods
        for route in main.app.routes
    )