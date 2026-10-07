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
    def __init__(self):
        self.documents = []

    def count_documents(self, query):
        return len(self.documents)

    def insert_one(self, document):
        self.documents.append(deepcopy(document))

    def find(self, query=None):
        return deepcopy(self.documents)

    def find_one(self, query):
        for document in self.documents:
            if all(document.get(key) == value for key, value in query.items()):
                return deepcopy(document)
        return None


class FakeDatabase:
    def __init__(self):
        self.experiments = FakeCollection()


@pytest.fixture
def experiment_client(monkeypatch):
    database = FakeDatabase()
    monkeypatch.setattr(main, "db", database)
    return TestClient(main.app), database


def create_payload(**overrides):
    payload = {
        "name": "Budget test",
        "mode": "adaptive",
        "max_tests": 5,
    }
    payload.update(overrides)
    return payload


def test_create_experiment_persists_budget_and_initializes_usage(
    experiment_client,
):
    client, database = experiment_client

    response = client.post(
        "/experiments",
        json=create_payload(testing_budget=12),
    )

    assert response.status_code == 200
    assert response.json() == {
        "experiment_id": "EXP001",
        "status": "created",
    }
    assert database.experiments.documents == [
        {
            "experiment_id": "EXP001",
            "name": "Budget test",
            "mode": "adaptive",
            "max_tests": 5,
            "testing_budget": 12,
            "scenario_id": None,
            "scenario_name": None,
            "vulnerability_ids": [],
            "budget_used": 0,
            "selected_tests": [],
            "executed_tests": [],
            "status": "created",
        }
    ]


def test_create_experiment_without_budget_remains_backward_compatible(
    experiment_client,
):
    client, database = experiment_client

    response = client.post(
        "/experiments",
        json=create_payload(),
    )

    assert response.status_code == 200
    assert response.json() == {
        "experiment_id": "EXP001",
        "status": "created",
    }
    assert database.experiments.documents[0]["testing_budget"] is None
    assert database.experiments.documents[0]["budget_used"] == 0
    assert database.experiments.documents[0]["selected_tests"] == []
    assert database.experiments.documents[0]["executed_tests"] == []


def test_experiment_retrieval_exposes_stored_budget_fields(
    experiment_client,
):
    client, database = experiment_client
    database.experiments.insert_one(
        {
            "experiment_id": "EXP001",
            "name": "Budget test",
            "mode": "adaptive",
            "max_tests": 5,
            "testing_budget": 12,
            "budget_used": 3,
            "status": "created",
        }
    )

    detail_response = client.get("/experiments/EXP001")
    list_response = client.get("/experiments")

    assert detail_response.status_code == 200
    assert detail_response.json()["testing_budget"] == 12
    assert detail_response.json()["budget_used"] == 3
    assert list_response.status_code == 200
    assert list_response.json()[0]["testing_budget"] == 12
    assert list_response.json()[0]["budget_used"] == 3


def test_experiment_retrieval_defaults_missing_test_histories(
    experiment_client,
):
    client, database = experiment_client
    database.experiments.insert_one(
        {
            "experiment_id": "EXP001",
            "name": "Legacy experiment",
            "mode": "adaptive",
            "max_tests": 3,
            "status": "completed",
        }
    )

    detail_response = client.get("/experiments/EXP001")
    list_response = client.get("/experiments")

    assert detail_response.status_code == 200
    assert detail_response.json()["selected_tests"] == []
    assert detail_response.json()["executed_tests"] == []
    assert list_response.status_code == 200
    assert list_response.json()[0]["selected_tests"] == []
    assert list_response.json()[0]["executed_tests"] == []


def test_create_experiment_rejects_non_positive_testing_budget(
    experiment_client,
):
    client, database = experiment_client

    response = client.post(
        "/experiments",
        json=create_payload(testing_budget=0),
    )

    assert response.status_code == 422
    assert database.experiments.documents == []


def test_create_experiment_persists_scenario_metadata(
    experiment_client,
):
    client, database = experiment_client

    response = client.post(
        "/experiments",
        json=create_payload(
            scenario_id="SCENARIO_V04_V06",
            scenario_name="Prompt and Data Exposure Scenario",
            vulnerability_ids=["V04", "V05", "V06"],
        ),
    )

    assert response.status_code == 200

    experiment = database.experiments.documents[0]

    assert experiment["scenario_id"] == "SCENARIO_V04_V06"
    assert experiment["scenario_name"] == (
        "Prompt and Data Exposure Scenario"
    )
    assert experiment["vulnerability_ids"] == [
        "V04",
        "V05",
        "V06",
    ]

def test_experiment_retrieval_exposes_scenario_metadata(
    experiment_client,
):
    client, database = experiment_client

    database.experiments.insert_one(
        {
            "experiment_id": "EXP001",
            "name": "Scenario experiment",
            "mode": "adaptive",
            "max_tests": 5,
            "testing_budget": 10,
            "scenario_id": "SCENARIO_V04_V06",
            "scenario_name": "Prompt and Data Exposure Scenario",
            "vulnerability_ids": ["V04", "V05", "V06"],
            "budget_used": 0,
            "selected_tests": [],
            "executed_tests": [],
            "status": "created",
        }
    )

    detail_response = client.get("/experiments/EXP001")
    list_response = client.get("/experiments")

    assert detail_response.status_code == 200
    assert detail_response.json()["scenario_id"] == "SCENARIO_V04_V06"
    assert detail_response.json()["scenario_name"] == (
        "Prompt and Data Exposure Scenario"
    )
    assert detail_response.json()["vulnerability_ids"] == [
        "V04",
        "V05",
        "V06",
    ]

    assert list_response.status_code == 200
    assert list_response.json()[0]["scenario_id"] == "SCENARIO_V04_V06"
    assert list_response.json()[0]["scenario_name"] == (
        "Prompt and Data Exposure Scenario"
    )
    assert list_response.json()[0]["vulnerability_ids"] == [
        "V04",
        "V05",
        "V06",
    ]

def test_list_scenarios_returns_registered_chain_scenarios(
    experiment_client,
):
    client, _ = experiment_client

    response = client.get("/scenarios")

    assert response.status_code == 200

    body = response.json()

    assert set(body) == {"scenarios"}
    assert len(body["scenarios"]) == 2

    scenario_ids = {
        scenario["scenario_id"]
        for scenario in body["scenarios"]
    }

    assert scenario_ids == {
        "CHAIN-AUTH-TOOL",
        "CHAIN-AUTH-TOOL-MEM",
    }


def test_get_scenario_returns_registered_chain_configuration(
    experiment_client,
):
    client, _ = experiment_client

    response = client.get("/scenarios/CHAIN-AUTH-TOOL")

    assert response.status_code == 200

    assert response.json() == {
        "scenario_id": "CHAIN-AUTH-TOOL",
        "scenario_name": "Authorization to Tool Access",
        "description": (
            "A two-step controlled chain where a weak authorization "
            "condition precedes unsafe tool access."
        ),
        "chain_ids": [
            "CHAIN-AUTH-TOOL",
        ],
        "steps": [
            "permission_test",
            "tool_access_test",
        ],
    }


def test_get_unknown_scenario_returns_404(
    experiment_client,
):
    client, _ = experiment_client

    response = client.get("/scenarios/UNKNOWN-SCENARIO")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Scenario not found: UNKNOWN-SCENARIO"
    }