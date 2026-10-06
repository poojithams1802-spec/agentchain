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


class FakeCollection:
    def __init__(self, documents=()):
        self.documents = [deepcopy(document) for document in documents]

    def find_one(self, query, projection=None):
        for document in self.documents:
            if all(document.get(key) == value for key, value in query.items()):
                return deepcopy(document)
        return None


class FakeDatabase:
    def __init__(self, experiments=(), chains=()):
        self.experiments = FakeCollection(experiments)
        self.attack_chains = FakeCollection(chains)


@pytest.fixture
def execution_context(monkeypatch):
    experiment = {"experiment_id": "EXP001"}
    chain = {
        "chain_id": "CHAIN001",
        "experiment_id": "EXP001",
        "steps": ["permission_test", "tool_access_test"],
    }
    database = FakeDatabase([experiment], [chain])
    calls = []

    def fake_execute_chain(experiment_id, chain_id):
        calls.append((experiment_id, chain_id))
        return {
            "status": "validated",
            "experiment_id": experiment_id,
            "chain_id": chain_id,
            "name": "Two-step chain",
            "description": "Validates a two-step chain.",
            "steps": [
                {"test": "permission_test", "status": "validated"},
                {"test": "tool_access_test", "status": "validated"},
            ],
            "chain_length": 2,
            "validated_steps": 2,
            "total_steps": 2,
            "validation_rate": 1.0,
            "all_findings_reproduced": True,
            "error": None,
        }

    monkeypatch.setattr(main, "db", database)
    monkeypatch.setattr(main, "execute_chain", fake_execute_chain)

    return TestClient(main.app), database, calls


def test_execute_registered_two_step_chain(execution_context):
    client, _, calls = execution_context

    response = client.post(
        "/experiments/EXP001/chains/execute",
        json={"chain_id": "CHAIN001"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "validated"
    assert body["experiment_id"] == "EXP001"
    assert body["chain_id"] == "CHAIN001"
    assert body["chain_length"] == 2
    assert body["validated_steps"] == 2
    assert body["total_steps"] == 2
    assert body["validation_rate"] == 1.0
    assert body["all_findings_reproduced"] is True
    assert len(body["steps"]) == 2
    assert calls == [("EXP001", "CHAIN001")]


def test_execute_chain_returns_404_when_experiment_is_missing(
    execution_context,
):
    client, database, calls = execution_context
    database.experiments = FakeCollection()

    response = client.post(
        "/experiments/MISSING/chains/execute",
        json={"chain_id": "CHAIN001"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Experiment not found"}
    assert calls == []


def test_execute_chain_returns_404_when_chain_is_missing(
    execution_context,
):
    client, database, calls = execution_context
    database.attack_chains = FakeCollection()

    response = client.post(
        "/experiments/EXP001/chains/execute",
        json={"chain_id": "MISSING"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Chain not found"}
    assert calls == []


def test_execute_chain_returns_404_when_chain_belongs_to_another_experiment(
    execution_context,
):
    client, database, calls = execution_context
    database.attack_chains = FakeCollection(
        [
            {
                "chain_id": "CHAIN001",
                "experiment_id": "EXP002",
                "steps": ["permission_test", "tool_access_test"],
            }
        ]
    )

    response = client.post(
        "/experiments/EXP001/chains/execute",
        json={"chain_id": "CHAIN001"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Chain not found"}
    assert calls == []


@pytest.mark.parametrize(
    ("error", "expected_detail"),
    [
        ("Chain definition failed validation.", "Chain definition failed validation."),
        (None, "Chain execution failed"),
    ],
)
def test_execute_chain_returns_400_for_invalid_p4_result(
    execution_context,
    monkeypatch,
    error,
    expected_detail,
):
    client, _, calls = execution_context

    def invalid_execute_chain(experiment_id, chain_id):
        calls.append((experiment_id, chain_id))
        return {
            "status": "invalid",
            "experiment_id": experiment_id,
            "chain_id": chain_id,
            "error": error,
        }

    monkeypatch.setattr(main, "execute_chain", invalid_execute_chain)

    response = client.post(
        "/experiments/EXP001/chains/execute",
        json={"chain_id": "CHAIN001"},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": expected_detail}
    assert calls == [("EXP001", "CHAIN001")]
