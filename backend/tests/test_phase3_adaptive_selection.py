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

    def update_one(self, query, update):
        for document in self.documents:
            if all(document.get(key) == value for key, value in query.items()):
                document.update(deepcopy(update["$set"]))
                return
        raise AssertionError(f"No document matches {query}")

    def insert_one(self, document):
        self.documents.append(deepcopy(document))


class FakeDatabase:
    def __init__(self, experiment):
        self.experiments = FakeCollection([experiment])
        self.evaluation_results = FakeCollection()


def test_start_persists_planner_selection_and_final_execution(
    monkeypatch,
):
    experiment = {
        "experiment_id": "EXP001",
        "name": "Adaptive selection",
        "mode": "adaptive",
        "max_tests": 2,
        "status": "created",
    }
    database = FakeDatabase(experiment)
    planned_tests = iter(["permission_test", "permission_test"])
    executed_tests = []

    class FakePlanner:
        def plan(self, planner_input):
            return SimpleNamespace(selected_test=next(planned_tests))

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

    def fake_execute_selected_test(experiment_id, test):
        executed_tests.append(test)
        return {
            "status": "completed",
            "experiment_id": experiment_id,
            "selected_test": test,
            "validation": {
                "valid": True,
                "selected_test": test,
                "error": None,
            },
            "executed": True,
            "result": {
                "test": test,
                "finding": f"{test}_finding",
                "severity": "low",
                "evidence": "mock evidence",
                "confidence": 0.9,
            },
            "execution_cost": {
                "test_count": 1,
                "execution_time_seconds": 0.01,
            },
        }

    monkeypatch.setattr(main, "db", database)
    monkeypatch.setattr(main, "planner", FakePlanner())
    monkeypatch.setattr(main, "ChainValidator", FakeValidator)
    monkeypatch.setattr(
        main,
        "execute_selected_test",
        fake_execute_selected_test,
    )
    monkeypatch.setattr(main, "add_experiment_log", lambda *args: None)
    monkeypatch.setattr(main, "add_experiment_finding", lambda **kwargs: None)
    monkeypatch.setattr(main, "add_attack_chain", lambda **kwargs: "CHAIN001")

    response = TestClient(main.app).post("/experiments/EXP001/start")

    assert response.status_code == 200
    assert executed_tests == ["permission_test", "tool_access_test"]
    persisted = database.experiments.find_one(
        {"experiment_id": "EXP001"}
    )
    assert persisted["status"] == "completed"
    assert persisted["selected_tests"] == [
        "permission_test",
        "permission_test",
    ]
    assert persisted["executed_tests"] == [
        "permission_test",
        "tool_access_test",
    ]
    assert persisted["selected_tests"] != persisted["executed_tests"]
