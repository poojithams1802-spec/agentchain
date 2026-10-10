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

    def find(self, query=None, projection=None):
        if query is None:
            query = {}

        matching_documents = [
            document
            for document in self.documents
            if all(
                document.get(key) == value
                for key, value in query.items()
            )
        ]

        if projection:
            return deepcopy(
                [
                    {
                        key: value
                        for key, value in document.items()
                        if key not in projection or projection[key] != 0
                    }
                    for document in matching_documents
                ]
            )

        return deepcopy(matching_documents)

    def find_one(self, query, projection=None):
        for document in self.documents:
            if all(document.get(key) == value for key, value in query.items()):
                return deepcopy(document)
        return None

    def update_one(self, query, update):
        for document in self.documents:
            if document.get("experiment_id") != query.get("experiment_id"):
                continue

            status_filter = query.get("status", {})
            excluded_statuses = status_filter.get("$nin", [])

            if document.get("status") in excluded_statuses:
                continue

            changes = update.get("$set", {})
            modified = any(
                document.get(key) != value
                for key, value in changes.items()
            )

            if modified:
                document.update(deepcopy(changes))

            return type(
                "UpdateResult",
                (),
                {"matched_count": 1, "modified_count": int(modified)},
            )()

        return type(
            "UpdateResult",
            (),
            {"matched_count": 0, "modified_count": 0},
        )()


class FakeDatabase:
    def __init__(self):
        self.experiments = FakeCollection()
        self.evaluation_results = FakeCollection()
        self.agent_states = FakeCollection()
        self.multi_agent_results = FakeCollection()


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
    assert len(body["scenarios"]) >= 2

    scenario_ids = {
        scenario["scenario_id"]
        for scenario in body["scenarios"]
    }

    assert scenario_ids >= {
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

def test_create_phase3_ablation_result_persists_correct_configuration_and_metrics(
    experiment_client,
):
    client, database = experiment_client

    payload = {
        "experiment_id": "EXP010",
        "configuration": "llm_rag_chain_context",
        "status": "completed",
        "selected_tests": [
            "permission_test",
            "tool_access_test",
        ],
        "tests_used": 2,
        "findings": [
            "unsafe_permission",
        ],
        "finding_count": 1,
        "llm_calls": 2,
        "llm_calls_used": 2,
        "fallback_used": False,
        "budget_used": 2,
        "budget_remaining": 1,
        "execution_success": True,
        "execution_time_seconds": 1.25,
        "planner_decisions": [
            {
                "test": "permission_test",
                "decision": "selected",
            }
        ],
        "selection_accuracy": 1.0,
        "chain_discovery_rate": 1.0,
        "mitigation_success": 1.0,
        "chain_disruption": 1.0,
        "tests_required": 2,
        "latency": 1.25,
        "validation_rate": 1.0,
        "residual_vulnerable_steps": 0,
    }

    response = client.post(
        "/phase3/ablation/results",
        json=payload,
    )

    assert response.status_code == 200
    assert response.json() == {
        "ablation_run_id": "ABL001",
        "experiment_id": "EXP010",
        "configuration": "llm_rag_chain_context",
        "status": "completed",
    }

    assert len(database.evaluation_results.documents) == 1

    persisted = database.evaluation_results.documents[0]

    assert persisted["ablation_run_id"] == "ABL001"
    assert persisted["evaluation_type"] == "phase3_ablation"
    assert persisted["experiment_id"] == "EXP010"
    assert persisted["configuration"] == "llm_rag_chain_context"

    assert persisted["selection_accuracy"] == 1.0
    assert persisted["chain_discovery_rate"] == 1.0
    assert persisted["mitigation_success"] == 1.0
    assert persisted["chain_disruption"] == 1.0
    assert persisted["tests_required"] == 2
    assert persisted["latency"] == 1.25
    assert persisted["validation_rate"] == 1.0
    assert persisted["residual_vulnerable_steps"] == 0


def test_get_phase3_ablation_results_returns_only_ablation_records(
    experiment_client,
):
    client, database = experiment_client

    database.evaluation_results.insert_one(
        {
            "evaluation_type": "phase2_mitigation",
            "experiment_id": "EXP001",
        }
    )

    database.evaluation_results.insert_one(
        {
            "evaluation_type": "phase3_ablation",
            "ablation_run_id": "ABL001",
            "experiment_id": "EXP010",
            "configuration": "llm_only",
            "status": "completed",
        }
    )

    response = client.get("/phase3/ablation/results")

    assert response.status_code == 200
    assert response.json() == {
        "results": [
            {
                "evaluation_type": "phase3_ablation",
                "ablation_run_id": "ABL001",
                "experiment_id": "EXP010",
                "configuration": "llm_only",
                "status": "completed",
            }
        ]
    }

def test_create_agent_state(experiment_client):
    client, database = experiment_client

    payload = {
        "experiment_id": "EXP001",
        "agents": [
            {
                "agent_id": "agent_a",
                "role": "research",
                "tools": ["knowledge_search"],
                "permissions": ["read"],
            },
            {
                "agent_id": "agent_b",
                "role": "planning",
                "tools": ["planner"],
                "permissions": ["read"],
            },
        ],
        "interactions": [
            {
                "from_agent": "agent_a",
                "to_agent": "agent_b",
                "type": "research_handoff",
            }
        ],
        "trust_context": {
            "untrusted_agents": [],
            "cross_agent_trust": False,
        },
        "shared_memory_context": {
            "shared_memory_enabled": True,
            "cross_agent_memory": True,
        },
        "current_agent": "agent_b",
        "current_task": "planning",
    }

    response = client.post(
        "/experiments/EXP001/agents/state",
        json=payload,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert response.json()["experiment_id"] == "EXP001"


def test_get_agent_state(experiment_client):
    client, database = experiment_client

    database.agent_states.insert_one(
        {
            "experiment_id": "EXP001",
            "agents": [
                {
                    "agent_id": "agent_a",
                    "role": "research",
                }
            ],
            "interactions": [],
            "trust_context": {
                "untrusted_agents": [],
                "cross_agent_trust": False,
            },
            "shared_memory_context": {
                "shared_memory_enabled": True,
                "cross_agent_memory": True,
            },
            "current_agent": "agent_a",
            "current_task": "research",
        }
    )

    response = client.get("/experiments/EXP001/agents/state")

    assert response.status_code == 200
    assert response.json()["experiment_id"] == "EXP001"
    assert response.json()["current_agent"] == "agent_a"


def test_create_multi_agent_security_result(experiment_client):
    client, _ = experiment_client

    response = client.post(
        "/experiments/EXP-DAY14/agents/security-result",
        json={
            "experiment_id": "EXP-DAY14",
            "agents": [
                {
                    "agent_id": "agent_a",
                    "role": "research",
                    "trust_level": "trusted",
                },
                {
                    "agent_id": "agent_b",
                    "role": "execution",
                    "trust_level": "low",
                },
            ],
            "interactions": [
                {
                    "from_agent": "agent_a",
                    "to_agent": "agent_b",
                    "action": "delegation",
                    "allowed": True,
                }
            ],
            "trust_context": {
                "untrusted_agents": ["agent_b"],
                "cross_agent_trust": True,
            },
            "shared_memory_context": {
                "shared_memory_enabled": True,
                "cross_agent_memory": True,
            },
            "assessment": {
                "enabled": True,
                "interaction_assessments": [
                    {
                        "from_agent": "agent_a",
                        "to_agent": "agent_b",
                        "action": "delegation",
                        "is_delegation": True,
                        "allowed": True,
                        "source_trust": "trusted",
                        "target_trust": "low",
                        "risks": ["delegation_to_low_trust_agent"],
                    }
                ],
                "trust_risks": ["untrusted_agent_context"],
                "delegation_risks": ["delegation_to_low_trust_agent"],
                "security_signals": ["privilege_propagation"],
                "recommended_checks": ["permission_test"],
            },
            "status": "completed",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert response.json()["experiment_id"] == "EXP-DAY14"


def test_get_multi_agent_security_result(experiment_client):
    client, fake_db = experiment_client

    fake_db.multi_agent_results.insert_one(
        {
            "experiment_id": "EXP-DAY14",
            "agents": [
                {
                    "agent_id": "agent_a",
                    "role": "research",
                    "trust_level": "trusted",
                },
                {
                    "agent_id": "agent_b",
                    "role": "execution",
                    "trust_level": "low",
                },
            ],
            "interactions": [
                {
                    "from_agent": "agent_a",
                    "to_agent": "agent_b",
                    "action": "delegation",
                    "allowed": True,
                }
            ],
            "trust_context": {
                "untrusted_agents": ["agent_b"],
                "cross_agent_trust": True,
            },
            "shared_memory_context": {
                "shared_memory_enabled": True,
                "cross_agent_memory": True,
            },
            "assessment": {
                "enabled": True,
                "interaction_assessments": [
                    {
                        "from_agent": "agent_a",
                        "to_agent": "agent_b",
                        "action": "delegation",
                        "is_delegation": True,
                        "allowed": True,
                        "source_trust": "trusted",
                        "target_trust": "low",
                        "risks": ["delegation_to_low_trust_agent"],
                    }
                ],
                "trust_risks": ["untrusted_agent_context"],
                "delegation_risks": ["delegation_to_low_trust_agent"],
                "security_signals": ["privilege_propagation"],
                "recommended_checks": ["permission_test"],
            },
            "status": "completed",
        }
    )

    response = client.get(
        "/experiments/EXP-DAY14/agents/security-result"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["experiment_id"] == "EXP-DAY14"
    assert data["status"] == "completed"
    assert data["assessment"]["enabled"] is True
    assert data["assessment"]["delegation_risks"] == [
        "delegation_to_low_trust_agent"
    ]


def test_run_multi_agent_security_result(experiment_client, monkeypatch):
    client, fake_db = experiment_client

    scenario_result = {
        "status": "completed",
        "chain_id": "MULTI-AGENT-CHAIN-V11-V10",
        "agents": [{"agent_id": "AGENT_UNTRUSTED"}],
        "communication": {"status": "delivered"},
        "vulnerabilities": {
            "V11": {"vulnerable": True},
            "V10": {"vulnerable": True},
        },
        "chain_steps": [
            {"step": 1, "vulnerability_id": "V11"},
            {"step": 2, "vulnerability_id": "V10"},
        ],
        "chain_triggered": True,
        "expected_chain": ["V11", "V10"],
        "validation": {
            "valid": True,
            "errors": [],
            "chain_id": "MULTI-AGENT-CHAIN-V11-V10",
            "chain_length": 2,
            "validated_chain": True,
        },
    }

    monkeypatch.setattr(
        main,
        "run_and_validate_multi_agent_security_scenario",
        lambda: scenario_result,
    )

    response = client.post(
        "/experiments/EXP-DAY14/agents/security-result/run"
    )

    assert response.status_code == 200
    assert response.json()["chain_triggered"] is True
    assert response.json()["validation"]["valid"] is True

    saved = fake_db.multi_agent_results.find_one(
        {"experiment_id": "EXP-DAY14"},
        {"_id": 0},
    )

    assert saved is not None
    assert saved["chain_id"] == "MULTI-AGENT-CHAIN-V11-V10"
    assert saved["chain_steps"] == scenario_result["chain_steps"]
    assert saved["validation"]["validated_chain"] is True
def test_get_agent_state_not_found(experiment_client):
    client, database = experiment_client

    response = client.get("/experiments/DOES-NOT-EXIST/agents/state")

    assert response.status_code == 404


def test_completed_experiment_cannot_be_started_twice(
    experiment_client,
):
    client, database = experiment_client

    database.experiments.insert_one(
        {
            "experiment_id": "EXP-DUPLICATE",
            "name": "Duplicate protection test",
            "mode": "adaptive",
            "max_tests": 3,
            "status": "completed",
            "selected_tests": ["permission_test"],
            "executed_tests": ["permission_test"],
            "budget_used": 1,
        }
    )

    response = client.post("/experiments/EXP-DUPLICATE/start")

    assert response.status_code == 409
    assert "already running or has completed" in response.json()["detail"]

    saved = database.experiments.find_one(
        {"experiment_id": "EXP-DUPLICATE"}
    )
    assert saved["status"] == "completed"
    assert saved["selected_tests"] == ["permission_test"]
    assert saved["executed_tests"] == ["permission_test"]
    assert saved["budget_used"] == 1
