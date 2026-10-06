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

    def insert_one(self, document):
        self.documents.append(deepcopy(document))


class FakeDatabase:
    def __init__(self, experiments=(), chains=(), evaluation_results=()):
        self.experiments = FakeCollection(experiments)
        self.attack_chains = FakeCollection(chains)
        self.evaluation_results = FakeCollection(evaluation_results)


@pytest.fixture
def execution_context(monkeypatch):
    experiment = {"experiment_id": "EXP001", "mode": "research"}
    chain = {
        "chain_id": "CHAIN001",
        "experiment_id": "EXP001",
        "steps": ["permission_test", "tool_access_test"],
    }
    database = FakeDatabase([experiment], [chain])
    calls = []
    converter_calls = []
    chain_result = {
        "status": "validated",
        "experiment_id": "EXP001",
        "chain_id": "CHAIN001",
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
    research_result = {
        "experiment_id": "EXP001",
        "mode": "research",
        "executed_tests": ["permission_test", "tool_access_test"],
        "findings": ["unsafe_permission", "unsafe_tool_access"],
        "candidate_chains": ["CHAIN001"],
        "validated_chains": ["CHAIN001"],
        "average_chain_length": 2,
        "validation_rate": 1.0,
        "execution_count": 2,
        "llm_calls": 0,
        "fallback_used": False,
        "chain_id": "CHAIN001",
        "chain_name": "Two-step chain",
        "chain_steps": ["permission_test", "tool_access_test"],
        "chain_length": 2,
        "validated_steps": 2,
        "chain_validation_rate": 1.0,
        "all_findings_reproduced": True,
        "chain_status": "validated",
    }

    def fake_execute_chain(experiment_id, chain_id):
        calls.append((experiment_id, chain_id))
        return chain_result

    def fake_chain_result_to_research_result(
        result,
        mode="adaptive",
        llm_calls=0,
        fallback_used=False,
    ):
        converter_calls.append(
            (result, mode, llm_calls, fallback_used)
        )
        return research_result

    persist_result = main.persist_phase3_chain_result

    def fake_persist_phase3_chain_result(result):
        return persist_result(
            result,
            database.evaluation_results,
        )

    monkeypatch.setattr(main, "db", database)
    monkeypatch.setattr(main, "execute_chain", fake_execute_chain)
    monkeypatch.setattr(
        main,
        "chain_result_to_research_result",
        fake_chain_result_to_research_result,
    )
    monkeypatch.setattr(
        main,
        "persist_phase3_chain_result",
        fake_persist_phase3_chain_result,
    )

    return (
        TestClient(main.app),
        database,
        calls,
        converter_calls,
        chain_result,
        research_result,
    )


def test_execute_registered_two_step_chain(execution_context):
    (
        client,
        database,
        calls,
        converter_calls,
        chain_result,
        research_result,
    ) = execution_context

    response = client.post(
        "/experiments/EXP001/chains/execute",
        json={"chain_id": "CHAIN001"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body == chain_result
    assert body["status"] == "validated"
    assert body["experiment_id"] == "EXP001"
    assert body["chain_id"] == "CHAIN001"
    assert body["chain_length"] == 2
    assert body["validated_steps"] == 2
    assert body["total_steps"] == 2
    assert body["validation_rate"] == 1.0
    assert body["all_findings_reproduced"] is True
    assert len(body["steps"]) == 2
    assert set(body) == {
        "status",
        "experiment_id",
        "chain_id",
        "name",
        "description",
        "steps",
        "chain_length",
        "validated_steps",
        "total_steps",
        "validation_rate",
        "all_findings_reproduced",
        "error",
    }
    assert calls == [("EXP001", "CHAIN001")]
    assert len(converter_calls) == 1
    converted_result, mode, llm_calls, fallback_used = converter_calls[0]
    assert converted_result is chain_result
    assert mode == "research"
    assert llm_calls == 0
    assert fallback_used is False
    assert len(database.evaluation_results.documents) == 1
    persisted = database.evaluation_results.documents[0]
    assert persisted["evaluation_type"] == "phase3_chain"
    assert persisted["timestamp"]
    assert {
        key: value
        for key, value in persisted.items()
        if key not in {"evaluation_type", "timestamp"}
    } == research_result


def test_execute_chain_returns_404_when_experiment_is_missing(
    execution_context,
):
    client, database, calls, converter_calls, _, _ = execution_context
    database.experiments = FakeCollection()

    response = client.post(
        "/experiments/MISSING/chains/execute",
        json={"chain_id": "CHAIN001"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Experiment not found"}
    assert calls == []
    assert converter_calls == []


def test_execute_chain_returns_404_when_chain_is_missing(
    execution_context,
):
    client, database, calls, converter_calls, _, _ = execution_context
    database.attack_chains = FakeCollection()

    response = client.post(
        "/experiments/EXP001/chains/execute",
        json={"chain_id": "MISSING"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Chain not found"}
    assert calls == []
    assert converter_calls == []


def test_execute_chain_returns_404_when_chain_belongs_to_another_experiment(
    execution_context,
):
    client, database, calls, converter_calls, _, _ = execution_context
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
    assert converter_calls == []


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
    client, database, calls, converter_calls, _, _ = execution_context

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
    assert converter_calls == []
    assert database.evaluation_results.documents == []
