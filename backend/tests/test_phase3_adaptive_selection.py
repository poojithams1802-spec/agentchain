import math
import sys
from copy import deepcopy
from pathlib import Path
from types import ModuleType, SimpleNamespace

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

    def find_one(self, query):
        for document in self.documents:
            if all(document.get(key) == value for key, value in query.items()):
                return deepcopy(document)
        return None

    def count_documents(self, query):
        return len(self.documents)

    def update_one(self, query, update):
        for document in self.documents:
            matches = True

            for key, value in query.items():
                if isinstance(value, dict) and "$nin" in value:
                    if document.get(key) in value["$nin"]:
                        matches = False
                        break
                elif document.get(key) != value:
                    matches = False
                    break

            if matches:
                old_document = deepcopy(document)
                document.update(deepcopy(update["$set"]))

                modified_count = int(document != old_document)
                return SimpleNamespace(
                    matched_count=1,
                    modified_count=modified_count,
                )

        raise AssertionError(f"No document matches {query}")


    def insert_one(self, document):
        self.documents.append(deepcopy(document))


class FakeDatabase:
    def __init__(self, experiment):
        self.experiments = FakeCollection([experiment])
        self.evaluation_results = FakeCollection()
        self.adaptive_run_results = FakeCollection()
        self.experiment_logs = FakeCollection()
        self.findings = FakeCollection()
        self.attack_chains = FakeCollection()


def test_start_persists_planner_selection_and_final_execution(
    monkeypatch,
):
    experiment = {
        "experiment_id": "EXP001",
        "name": "Adaptive selection",
        "mode": "adaptive",
        "max_tests": 2,
        "status": "created",
        "budget_used": 3,
    }
    database = FakeDatabase(experiment)
    planned_tests = iter(["permission_test", "tool_access_test"])
    executed_tests = []

    class FakePlanner:
        def plan(self, planner_input):
            planner_input.budget_used.llm_calls += 1
            self.last_decision_metadata = {
                "decision_source": "gemini",
                "fallback_reason": None,
                "rag_retrieval_status": "retrieved",
                "rag_context_retrieved": True,
                "rag_context_used": True,
                "decision_recovery": None,
            }
            return SimpleNamespace(
                selected_test=next(planned_tests),
                reason="Selected for adaptive testing",
                priority=1,
                confidence=0.9,
            )

    class FakeValidator:
        def __init__(self, experiment_id):
            assert experiment_id == "EXP001"

        def validate_chain(self, chain_id, steps):
            return {
                "status": "validated",
                "validated_steps": len(steps),
                "total_steps": len(steps),
                "steps": steps,
            }

    def fake_execute_planned_test(decision, experiment_id):
        test = decision.selected_test
        executed_tests.append(test)

        return {
            "status": "completed",
            "test": test,
            "finding": f"{test}_finding",
            "severity": "low",
            "evidence": "mock evidence",
            "confidence": 0.9,
            "execution_cost": {
                "test_count": 1,
                "execution_time_seconds": 0.01,
            },
        }

    monkeypatch.setattr(main, "db", database)
    monkeypatch.setattr(main, "planner", FakePlanner())
    monkeypatch.setattr(main, "ChainValidator", FakeValidator)
    monkeypatch.setattr(
        sys.modules["adaptive_loop"],
        "execute_planned_test",
        fake_execute_planned_test,
    )
    monkeypatch.setattr(main, "add_experiment_log", lambda *args: None)
    monkeypatch.setattr(main, "add_experiment_finding", lambda **kwargs: None)
    monkeypatch.setattr(main, "add_attack_chain", lambda **kwargs: "CHAIN001")

    response = TestClient(main.app).post("/experiments/EXP001/start")

    print("STATUS:", response.status_code)
    print("RESPONSE:", response.json())
    print("EXECUTED TESTS:", executed_tests)

    assert response.status_code == 200
    assert executed_tests == ["permission_test", "tool_access_test"]
    persisted = database.experiments.find_one(
        {"experiment_id": "EXP001"}
    )
    assert persisted["status"] == "completed"
    assert persisted["selected_tests"] == [
        "permission_test",
        "tool_access_test",
    ]

    assert persisted["executed_tests"] == [
        "permission_test",
        "tool_access_test",
    ]

    assert persisted["selected_tests"] == persisted["executed_tests"]

    assert persisted["budget_used"] == 5
    persisted_budget = persisted["adaptive_budget_used"]
    assert {
        key: value
        for key, value in persisted_budget.items()
        if key != "time_seconds"
    } == {
        "tests": 2,
        "llm_calls": 2,
    }
    persisted_elapsed = persisted_budget["time_seconds"]
    assert isinstance(persisted_elapsed, (int, float))
    assert not isinstance(persisted_elapsed, bool)
    assert math.isfinite(persisted_elapsed)
    assert persisted_elapsed >= 0

    adaptive_run = database.adaptive_run_results.documents[0]
    assert adaptive_run["llm_calls"] == 2
    assert adaptive_run["fallback_used"] is False
    adaptive_run_budget = adaptive_run["budget_used"]
    assert {
        key: value
        for key, value in adaptive_run_budget.items()
        if key != "time_seconds"
    } == {
        "tests": 2,
        "llm_calls": 2,
    }
    adaptive_run_elapsed = adaptive_run_budget["time_seconds"]
    assert isinstance(adaptive_run_elapsed, (int, float))
    assert not isinstance(adaptive_run_elapsed, bool)
    assert math.isfinite(adaptive_run_elapsed)
    assert adaptive_run_elapsed >= 0
    assert response.json()["llm_calls"] == 2
    assert response.json()["fallback_used"] is False
    assert response.json()["budget_used"] == adaptive_run["budget_used"]
    assert response.json()["decision_metadata"] == adaptive_run[
        "decision_metadata"
    ]
    assert adaptive_run["execution_results"] == response.json()[
        "execution_results"
    ]
    assert [
        finding["finding"]
        for finding in adaptive_run["findings"]
    ] == [
        "permission_test_finding",
        "tool_access_test_finding",
    ]

    assert adaptive_run["decision_metadata"] == [
        {
            "decision_source": "gemini",
            "fallback_reason": None,
            "rag_retrieval_status": "retrieved",
            "rag_context_retrieved": True,
            "rag_context_used": True,
            "decision_recovery": None,
        },
        {
            "decision_source": "gemini",
            "fallback_reason": None,
            "rag_retrieval_status": "retrieved",
            "rag_context_retrieved": True,
            "rag_context_used": True,
            "decision_recovery": None,
        },
    ]
    assert "llm_calls_used" not in response.json()
    assert "budget_used_delta" not in response.json()


def test_frontend_create_start_flow_uses_real_planner_and_sandbox(
    monkeypatch,
):
    import planner as planner_module

    monkeypatch.setattr(
        planner_module,
        "HybridKnowledgeRetriever",
        lambda: object(),
    )
    planner = planner_module.AdaptivePlanner()
    database = FakeDatabase({})
    llm_responses = iter(
        [
            {
                "selected_test": "permission_test",
                "reason": "Check the permission boundary first.",
                "priority": 0.9,
                "confidence": 0.9,
            },
            {
                "selected_test": "tool_access_test",
                "reason": "Follow up on the permission finding.",
                "priority": 0.9,
                "confidence": 0.9,
            },
        ]
    )

    monkeypatch.setattr(main, "db", database)
    monkeypatch.setattr(main, "planner", planner)
    monkeypatch.setattr(
        planner,
        "retrieve_knowledge",
        lambda planner_input: [],
    )
    monkeypatch.setattr(
        planner.llm_client,
        "generate_json_with_timeout",
        lambda prompt, timeout_ms: next(llm_responses),
    )
    client = TestClient(main.app)
    create_response = client.post(
        "/experiments",
        json={
            "name": "Frontend contract adaptive run",
            "mode": "adaptive",
            "max_tests": 2,
        },
    )

    assert create_response.status_code == 200
    experiment_id = create_response.json()["experiment_id"]

    start_response = client.post(
        f"/experiments/{experiment_id}/start"
    )

    assert start_response.status_code == 200
    result = start_response.json()
    assert result["selected_tests"] == [
        "permission_test",
        "tool_access_test",
    ]
    assert [item["status"] for item in result["execution_results"]] == [
        "completed",
        "completed",
    ]
    assert result["findings_created"] == 2
    assert [item["finding"] for item in result["sandbox_results"]] == [
        "weak_permission_control",
        "unsafe_tool_access",
    ]
    assert result["validation_result"]["status"] == "validated"
    assert result["llm_calls"] == 2
    assert result["fallback_used"] is False

    persisted_experiment = database.experiments.find_one(
        {"experiment_id": experiment_id}
    )
    assert persisted_experiment["status"] == "completed"
    assert persisted_experiment["selected_tests"] == result["selected_tests"]
    assert persisted_experiment["executed_tests"] == result["executed_tests"]

    adaptive_run = database.adaptive_run_results.documents[0]
    assert adaptive_run["experiment_id"] == experiment_id
    assert adaptive_run["execution_results"] == result["execution_results"]
    assert adaptive_run["llm_calls"] == result["llm_calls"]

    assert [item["finding"] for item in database.findings.documents] == [
        "weak_permission_control",
        "unsafe_tool_access",
    ]
    assert database.attack_chains.documents[0]["steps"] == result["executed_tests"]
    assert database.evaluation_results.documents[0]["status"] == "validated"
    assert database.experiment_logs.documents

def test_adaptive_loop_exception_marks_experiment_failed(
    monkeypatch,
):
    experiment = {
        "experiment_id": "EXP-EXCEPTION",
        "name": "Adaptive exception test",
        "mode": "adaptive",
        "max_tests": 2,
        "status": "created",
    }
    database = FakeDatabase(experiment)

    class FakeAdaptiveLoop:
        def __init__(self, planner):
            pass

        def run_detailed(self, **kwargs):
            raise RuntimeError("Simulated adaptive-loop failure")

    monkeypatch.setattr(main, "db", database)
    monkeypatch.setattr(main, "AdaptiveLoop", FakeAdaptiveLoop)

    response = TestClient(main.app).post(
        "/experiments/EXP-EXCEPTION/start"
    )

    persisted = database.experiments.find_one(
        {"experiment_id": "EXP-EXCEPTION"}
    )

    assert response.status_code == 500
    assert response.json()["detail"] == (
        "Adaptive experiment execution failed."
    )
    assert persisted["status"] == "failed"
    assert persisted["error"] == "Simulated adaptive-loop failure"
