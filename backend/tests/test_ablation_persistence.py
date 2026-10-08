import sys
from copy import deepcopy
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.ablation_persistence import persist_ablation_result
from app.ablation_aggregation import get_persisted_ablation_aggregation


class FakeCollection:
    def __init__(self, documents=()):
        self.documents = [deepcopy(document) for document in documents]

    def count_documents(self, query):
        return sum(
            1
            for document in self.documents
            if all(
                document.get(key) == value
                for key, value in query.items()
            )
        )

    def insert_one(self, document):
        self.documents.append(deepcopy(document))

    def find(self, query, projection=None):
        results = []

        for document in self.documents:
            if all(
                document.get(key) == value
                for key, value in query.items()
            ):
                if projection and projection.get("_id") == 0:
                    result = {
                        key: value
                        for key, value in document.items()
                        if key != "_id"
                    }
                else:
                    result = deepcopy(document)

                results.append(result)

        return results


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

from app.ablation_aggregation import aggregate_ablation_results


def test_aggregates_phase3_ablation_results_in_configuration_order():
    records = [
        {
            "evaluation_type": "phase3_ablation",
            "ablation_run_id": "ABL003",
            "experiment_id": "EXP003",
            "configuration": "llm_chain_context",
            "status": "completed",
            "tests_selected": 3,
            "llm_calls": 3,
            "selection_accuracy": 0.8,
            "chain_metrics": {
                "validation_rate": 0.75,
                "residual_vulnerable_steps": [
                    "memory_access_test",
                ],
            },
        },
        {
            "evaluation_type": "phase3_ablation",
            "ablation_run_id": "ABL001",
            "experiment_id": "EXP001",
            "configuration": "llm_only",
            "status": "completed",
            "tests_selected": 2,
            "llm_calls": 2,
            "selection_accuracy": 0.5,
        },
        {
            "evaluation_type": "phase3_ablation",
            "ablation_run_id": "ABL004",
            "experiment_id": "EXP004",
            "configuration": "llm_rag_chain_context",
            "status": "completed",
            "tests_selected": 3,
            "llm_calls": 3,
            "selection_accuracy": 1.0,
        },
        {
            "evaluation_type": "phase3_ablation",
            "ablation_run_id": "ABL002",
            "experiment_id": "EXP002",
            "configuration": "llm_rag",
            "status": "completed",
            "tests_selected": 2,
            "llm_calls": 2,
            "selection_accuracy": 0.75,
        },
    ]

    result = aggregate_ablation_results(records)

    assert result["study"] == "phase3_ablation"
    assert result["configuration_order"] == [
        "llm_only",
        "llm_rag",
        "llm_chain_context",
        "llm_rag_chain_context",
    ]

    assert result["configuration_count"] == 4

    assert [
        item["configuration"]
        for item in result["comparisons"]
    ] == [
        "llm_only",
        "llm_rag",
        "llm_chain_context",
        "llm_rag_chain_context",
    ]

    assert result["comparisons"][0]["selection_accuracy"] == 0.5
    assert result["comparisons"][1]["selection_accuracy"] == 0.75
    assert result["comparisons"][2]["validation_rate"] == 0.75
    assert result["comparisons"][2]["residual_vulnerable_steps"] == 1
    assert result["comparisons"][3]["selection_accuracy"] == 1.0


def test_aggregation_ignores_unknown_configurations():
    records = [
        {
            "evaluation_type": "phase3_ablation",
            "ablation_run_id": "ABL001",
            "experiment_id": "EXP001",
            "configuration": "llm_only",
            "selection_accuracy": 0.9,
        },
        {
            "evaluation_type": "phase3_ablation",
            "ablation_run_id": "ABL002",
            "experiment_id": "EXP002",
            "configuration": "unknown_configuration",
            "selection_accuracy": 0.1,
        },
    ]

    result = aggregate_ablation_results(records)

    assert result["configuration_count"] == 1
    assert result["comparisons"][0]["experiment_id"] == "EXP001"

def test_aggregation_preserves_missing_metrics_as_none():
    records = [
        {
            "evaluation_type": "phase3_ablation",
            "ablation_run_id": "ABL001",
            "experiment_id": "EXP001",
            "configuration": "llm_only",
            "status": "completed",
        }
    ]

    result = aggregate_ablation_results(records)

    comparison = result["comparisons"][0]

    assert comparison["selection_accuracy"] is None
    assert comparison["chain_discovery_rate"] is None
    assert comparison["mitigation_success"] is None
    assert comparison["chain_disruption"] is None
    assert comparison["validation_rate"] is None
    assert comparison["residual_vulnerable_steps"] is None

def test_get_persisted_ablation_aggregation_filters_phase3_records():
    collection = FakeCollection(
        [
            {
                "evaluation_type": "phase2_mitigation",
                "experiment_id": "EXP100",
                "configuration": "llm_only",
                "selection_accuracy": 0.1,
            },
            {
                "evaluation_type": "phase3_ablation",
                "ablation_run_id": "ABL001",
                "experiment_id": "EXP001",
                "configuration": "llm_only",
                "status": "completed",
                "selection_accuracy": 0.9,
            },
            {
                "evaluation_type": "phase3_ablation",
                "ablation_run_id": "ABL002",
                "experiment_id": "EXP002",
                "configuration": "llm_rag",
                "status": "completed",
                "selection_accuracy": 0.95,
            },
        ]
    )

    result = get_persisted_ablation_aggregation(collection)

    assert result["study"] == "phase3_ablation"
    assert result["configuration_count"] == 2

    assert [
        item["configuration"]
        for item in result["comparisons"]
    ] == [
        "llm_only",
        "llm_rag",
    ]

    assert all(
        item["experiment_id"] in {"EXP001", "EXP002"}
        for item in result["comparisons"]
    )