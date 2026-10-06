import sys
from copy import deepcopy
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.phase2_persistence import (
    PHASE2_CONDITION_RUNNER_SOURCE,
    persist_phase2_condition_records,
)


class FakeCollection:
    def __init__(self, documents=()):
        self.documents = [deepcopy(document) for document in documents]

    def update_one(self, query, update, upsert=False):
        for document in self.documents:
            if all(document.get(key) == value for key, value in query.items()):
                document.update(deepcopy(update["$set"]))
                return

        if upsert:
            document = deepcopy(query)
            document.update(deepcopy(update["$set"]))
            self.documents.append(document)


def runner_record():
    return {
        "experiment_id": "P2-RULE-001",
        "mode": "static",
        "condition": "rule_based_fixed_mitigation",
        "test": "permission_test",
        "expected_control": "authorization_gate",
        "selected_control": "authorization_gate",
        "selection_correct": True,
        "mitigation_control": "authorization_gate",
        "mitigation_applied": True,
        "attack_success_before": True,
        "attack_success_after": False,
        "chain_disrupted": True,
        "mitigation_validation": True,
        "residual_vulnerable_steps": [],
        "llm_calls": 0,
    }


def test_persists_condition_runner_record_with_metadata():
    collection = FakeCollection()
    record = runner_record()
    original_record = deepcopy(record)

    persisted_count = persist_phase2_condition_records(
        [record],
        collection,
    )

    assert persisted_count == 1
    assert len(collection.documents) == 1
    stored_record = collection.documents[0]
    assert stored_record["evaluation_type"] == "phase2_condition"
    assert stored_record["condition"] == "rule_based_fixed_mitigation"
    assert stored_record["source"] == PHASE2_CONDITION_RUNNER_SOURCE
    assert stored_record["timestamp"]
    assert all(stored_record[key] == value for key, value in record.items())
    assert record == original_record


def test_repeated_persistence_upserts_the_same_runner_record():
    collection = FakeCollection()
    record = runner_record()

    persist_phase2_condition_records([record], collection)
    persist_phase2_condition_records([record], collection)

    assert len(collection.documents) == 1
    assert collection.documents[0]["experiment_id"] == "P2-RULE-001"
    assert collection.documents[0]["source"] == PHASE2_CONDITION_RUNNER_SOURCE


def test_persistence_leaves_unrelated_evaluation_records_untouched():
    phase1_record = {
        "experiment_id": "P2-RULE-001",
        "evaluation_type": "phase1_validation",
        "status": "validated",
    }
    mitigation_record = {
        "experiment_id": "P2-RULE-001",
        "evaluation_type": "phase2_mitigation",
        "mode": "adaptive",
        "mitigation_control": "tool_allowlist",
    }
    collection = FakeCollection([phase1_record, mitigation_record])
    original_documents = deepcopy(collection.documents)

    persist_phase2_condition_records([runner_record()], collection)

    assert collection.documents[:2] == original_documents
    assert len(collection.documents) == 3
    assert collection.documents[2]["evaluation_type"] == "phase2_condition"
    assert collection.documents[2]["source"] == PHASE2_CONDITION_RUNNER_SOURCE