import sys
from copy import deepcopy
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.phase3_persistence import persist_phase3_chain_result


class FakeCollection:
    def __init__(self, documents=()):
        self.documents = [deepcopy(document) for document in documents]

    def insert_one(self, document):
        self.documents.append(deepcopy(document))


def test_persists_phase3_chain_result_without_changing_existing_records():
    phase1_record = {
        "evaluation_type": "phase1_validation",
        "experiment_id": "EXP001",
        "status": "validated",
    }
    phase2_record = {
        "evaluation_type": "phase2_condition",
        "source": "phase2_condition_runner",
        "experiment_id": "EXP001",
    }
    collection = FakeCollection([phase1_record, phase2_record])
    original_records = deepcopy(collection.documents)
    result = {
        "experiment_id": "EXP001",
        "mode": "adaptive",
        "executed_tests": ["permission_test", "tool_access_test"],
        "findings": ["unsafe_permission"],
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

    persist_phase3_chain_result(result, collection)

    assert collection.documents[:2] == original_records
    assert len(collection.documents) == 3
    persisted = collection.documents[2]
    assert persisted["evaluation_type"] == "phase3_chain"
    assert persisted["timestamp"]
    assert all(persisted[key] == value for key, value in result.items())
