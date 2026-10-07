import sys
from copy import deepcopy
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.ablation_persistence import persist_ablation_result


class FakeCollection:
    def __init__(self, documents=()):
        self.documents = [deepcopy(document) for document in documents]

    def count_documents(self, query):
        return sum(
            1
            for document in self.documents
            if all(document.get(key) == value for key, value in query.items())
        )

    def insert_one(self, document):
        self.documents.append(deepcopy(document))


def test_persists_phase3_ablation_result():
    existing_record = {
        "evaluation_type": "phase2_mitigation",
        "experiment_id": "EXP001",
    }

    collection = FakeCollection([existing_record])
    original_records = deepcopy(collection.documents)

    result = {
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

    persisted = persist_ablation_result(result, collection)

    assert collection.documents[:1] == original_records
    assert len(collection.documents) == 2

    assert persisted["ablation_run_id"] == "ABL001"
    assert persisted["evaluation_type"] == "phase3_ablation"
    assert persisted["timestamp"]

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


def test_ablation_run_id_increments():
    collection = FakeCollection(
        [
            {
                "evaluation_type": "phase3_ablation",
                "ablation_run_id": "ABL001",
            }
        ]
    )

    result = {
        "experiment_id": "EXP011",
        "configuration": "llm_only",
        "status": "completed",
        "selected_tests": ["permission_test"],
        "tests_used": 1,
        "findings": [],
        "finding_count": 0,
        "llm_calls": 1,
        "llm_calls_used": 1,
        "fallback_used": False,
        "budget_used": 1,
        "budget_remaining": 2,
        "execution_success": True,
        "execution_time_seconds": 0.5,
        "planner_decisions": [],
        "selection_accuracy": 1.0,
        "chain_discovery_rate": 1.0,
        "mitigation_success": 1.0,
        "chain_disruption": 1.0,
        "tests_required": 1,
        "latency": 0.5,
        "validation_rate": 1.0,
        "residual_vulnerable_steps": 0,
    }

    persisted = persist_ablation_result(result, collection)

    assert persisted["ablation_run_id"] == "ABL002"

def test_rejects_invalid_ablation_configuration():
    collection = FakeCollection()

    result = {
        "experiment_id": "EXP012",
        "configuration": "static_rule_based",
        "status": "completed",
    }

    try:
        persist_ablation_result(result, collection)
    except ValueError as exc:
        assert str(exc) == (
            "Unsupported ablation configuration: static_rule_based"
        )
    else:
        raise AssertionError(
            "Expected ValueError for unsupported ablation configuration"
        )

    assert collection.documents == []