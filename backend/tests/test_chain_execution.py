from datetime import datetime, timezone
import sys
from copy import deepcopy
from pathlib import Path
from types import ModuleType
from types import SimpleNamespace

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

    def update_one(self, query, update):
        for document in self.documents:
            if all(
                document.get(key) == value
                for key, value in query.items()
            ):
                changes = deepcopy(update.get("$set", {}))
                modified = any(
                    document.get(key) != value
                    for key, value in changes.items()
                )
                document.update(changes)
                return SimpleNamespace(
                    acknowledged=True,
                    matched_count=1,
                    modified_count=int(modified),
                )
        return SimpleNamespace(
            acknowledged=True,
            matched_count=0,
            modified_count=0,
        )


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


@pytest.fixture
def chain_mitigation_replay_context(monkeypatch):
    p4_chain_id = "CHAIN-AUTH-TOOL-MEM"
    chain_steps = [
        "permission_test",
        "tool_access_test",
        "memory_access_test",
    ]
    chain_dependencies = {
        "permission_test": [],
        "tool_access_test": ["permission_test"],
        "memory_access_test": ["tool_access_test"],
    }
    experiment = {"experiment_id": "EXP001", "mode": "research"}
    chain = {
        "chain_id": "CHAIN001",
        "experiment_id": "EXP001",
        "steps": chain_steps,
        "p4_chain_id": p4_chain_id,
        "dependencies": chain_dependencies,
    }
    database = FakeDatabase([experiment], [chain])
    calls = []
    expected_findings = {
        "permission_test": "weak_permission_control",
        "tool_access_test": "unsafe_tool_access",
        "memory_access_test": "memory_validation_weakness",
    }

    def step_validation(step, step_result):
        finding_matches = (
            step_result["finding"] == expected_findings[step]
        )
        evidence_exists = bool(step_result["evidence"])
        valid = (
            step_result["status"] == "completed"
            and finding_matches
            and evidence_exists
        )
        return {
            "valid": valid,
            "test": step,
            "status": step_result["status"],
            "finding": step_result["finding"],
            "expected_finding": expected_findings[step],
            "finding_matches": finding_matches,
            "evidence_exists": evidence_exists,
            "error": None if valid else "Chain step validation failed.",
        }

    def validation_summary(step_results):
        validations = [
            step_validation(step, step_result)
            for step, step_result in zip(chain_steps, step_results)
        ]
        validated_steps = sum(item["valid"] for item in validations)
        return {
            "valid": validated_steps == len(chain_steps),
            "validated_steps": validated_steps,
            "total_steps": len(chain_steps),
            "validation_rate": validated_steps / len(chain_steps),
            "steps": validations,
        }

    before_results = [
        {
            "status": "completed",
            "test": step,
            "finding": expected_findings[step],
            "severity": "high",
            "evidence": {"actual": f"{step} baseline evidence"},
            "confidence": 0.9,
            "execution_cost": {
                "test_count": 1,
                "execution_time_seconds": 0.01,
            },
        }
        for step in chain_steps
    ]
    after_results = [
        {
            "status": "completed",
            "test": step,
            "finding": expected_findings[step],
            "severity": "high",
            "evidence": (
                {
                    "original": f"{step} baseline evidence",
                    "mitigation": "authorization_gate",
                    "mitigation_status": "active",
                    "result": "attack_blocked",
                }
                if step == "permission_test"
                else {"actual": f"{step} remains vulnerable"}
            ),
            "confidence": 1.0 if step == "permission_test" else 0.9,
            **(
                {
                    "mitigation_applied": True,
                    "mitigation_control": "authorization_gate",
                }
                if step == "permission_test"
                else {}
            ),
            "execution_cost": {
                "test_count": 1,
                "execution_time_seconds": 0.01,
            },
        }
        for step in chain_steps
    ]
    before_validation = validation_summary(before_results)
    after_validation = validation_summary(after_results)
    activation_result = {
        "status": "activated",
        "experiment_id": "EXP001",
        "control": "authorization_gate",
        "evidence": "Mitigation activated for experiment.",
    }
    activation = {
        "status": "applied",
        "experiment_id": "EXP001",
        "control": "authorization_gate",
        "target": "weak_permission_control",
        "test": "permission_test",
        "activation": activation_result,
        "evidence": "Predefined mitigation activated for the experiment.",
    }
    reset = {
        "status": "reset",
        "experiment_id": "EXP001",
        "evidence": "All mitigations reset for experiment.",
    }
    replay_result = {
        "status": "completed",
        "experiment_id": "EXP001",
        "chain_id": p4_chain_id,
        "control": "authorization_gate",
        "chain_name": "Authorization to Tool Access to Memory",
        "chain_description": (
            "A three-step controlled chain where authorization "
            "weakness precedes tool access and memory-validation "
            "weakness."
        ),
        "chain_steps": [
            "permission_test",
            "tool_access_test",
            "memory_access_test",
        ],
        "chain_length": 3,
        "before": before_results,
        "before_validation": before_validation,
        "activation": activation,
        "after": after_results,
        "after_validation": after_validation,
        "blocked_steps": ["permission_test"],
        "residual_vulnerable_steps": [
            "tool_access_test",
            "memory_access_test",
        ],
        "chain_disrupted": True,
        "validation_result": {
            "status": "validated",
            "before_valid": True,
            "after_valid": True,
            "chain_disrupted": True,
            "blocked_steps": ["permission_test"],
            "residual_vulnerable_steps": [
                "tool_access_test",
                "memory_access_test",
            ],
            "attack_blocked": True,
            "validation_rate": 1.0,
        },
        "reset": reset,
    }

    def fake_replay_chain(experiment_id, chain_id, control_name):
        calls.append((experiment_id, chain_id, control_name))
        return replay_result

    monkeypatch.setattr(main, "db", database)
    monkeypatch.setattr(main, "replay_chain", fake_replay_chain)

    return TestClient(main.app), database, calls, replay_result


def test_full_chain_mitigation_replay_returns_and_persists_evidence(
    chain_mitigation_replay_context,
):
    client, database, calls, replay_result = chain_mitigation_replay_context

    response = client.post(
        "/experiments/EXP001/chains/mitigation/replay",
        json={
            "chain_id": "CHAIN001",
            "control_name": "authorization_gate",
        },
    )

    assert response.status_code == 200
    assert response.json()["chain_id"] == "CHAIN001"
    assert response.json()["p4_chain_id"] == "CHAIN-AUTH-TOOL-MEM"
    assert response.json()["residual_vulnerable_steps"] == [
        "tool_access_test",
        "memory_access_test",
    ]
    assert response.json()["reset"] == {
        "status": "reset",
        "experiment_id": "EXP001",
        "evidence": "All mitigations reset for experiment.",
    }
    assert calls == [
        ("EXP001", "CHAIN-AUTH-TOOL-MEM", "authorization_gate")
    ]
    assert len(database.evaluation_results.documents) == 1
    persisted = database.evaluation_results.documents[0]
    assert persisted["evaluation_type"] == (
        "phase3_chain_mitigation_replay"
    )
    assert persisted["timestamp"]
    timestamp = datetime.fromisoformat(persisted["timestamp"])
    assert timestamp.utcoffset() == timezone.utc.utcoffset(timestamp)
    expected_result = {
        **replay_result,
        "chain_id": "CHAIN001",
        "p4_chain_id": "CHAIN-AUTH-TOOL-MEM",
    }
    assert {
        key: value
        for key, value in persisted.items()
        if key not in {"evaluation_type", "timestamp"}
    } == expected_result


def test_full_chain_mitigation_replay_uses_explicit_association(
    chain_mitigation_replay_context,
):
    client, database, calls, _ = chain_mitigation_replay_context
    chain = database.attack_chains.documents[0]
    chain.pop("p4_chain_id")
    chain.pop("dependencies")

    association_response = client.post(
        "/experiments/EXP001/chains/CHAIN001/p4-association",
        json={"p4_chain_id": "CHAIN-AUTH-TOOL-MEM"},
    )

    assert association_response.status_code == 200
    assert association_response.json() == {
        "chain_id": "CHAIN001",
        "p4_chain_id": "CHAIN-AUTH-TOOL-MEM",
    }
    assert chain["p4_chain_id"] == "CHAIN-AUTH-TOOL-MEM"
    assert chain["dependencies"] == {
        "permission_test": [],
        "tool_access_test": ["permission_test"],
        "memory_access_test": ["tool_access_test"],
    }

    replay_response = client.post(
        "/experiments/EXP001/chains/mitigation/replay",
        json={
            "chain_id": "CHAIN001",
            "control_name": "authorization_gate",
        },
    )

    assert replay_response.status_code == 200
    assert calls == [
        ("EXP001", "CHAIN-AUTH-TOOL-MEM", "authorization_gate")
    ]
    assert replay_response.json()["chain_id"] == "CHAIN001"
    assert replay_response.json()["p4_chain_id"] == "CHAIN-AUTH-TOOL-MEM"


def test_full_chain_mitigation_replay_returns_404_for_missing_experiment(
    chain_mitigation_replay_context,
):
    client, database, calls, _ = chain_mitigation_replay_context
    database.experiments = FakeCollection()

    response = client.post(
        "/experiments/MISSING/chains/mitigation/replay",
        json={
            "chain_id": "CHAIN001",
            "control_name": "authorization_gate",
        },
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Experiment not found"}
    assert calls == []
    assert database.evaluation_results.documents == []


@pytest.mark.parametrize(
    "chain",
    [
        None,
        {
            "chain_id": "CHAIN001",
            "experiment_id": "EXP999",
            "steps": ["permission_test"],
        },
    ],
)
def test_full_chain_mitigation_replay_returns_404_for_unknown_or_foreign_chain(
    chain_mitigation_replay_context,
    chain,
):
    client, database, calls, _ = chain_mitigation_replay_context
    database.attack_chains = FakeCollection(
        [] if chain is None else [chain]
    )

    response = client.post(
        "/experiments/EXP001/chains/mitigation/replay",
        json={
            "chain_id": "CHAIN001",
            "control_name": "authorization_gate",
        },
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Chain not found"}
    assert calls == []
    assert database.evaluation_results.documents == []


def test_full_chain_mitigation_replay_does_not_persist_failed_result(
    chain_mitigation_replay_context,
    monkeypatch,
    caplog,
):
    client, database, calls, _ = chain_mitigation_replay_context
    calls.clear()

    executor_error = "activation failed; sensitive details"

    def failed_replay(experiment_id, chain_id, control_name):
        calls.append((experiment_id, chain_id, control_name))
        return {"status": "failed", "error": executor_error}

    monkeypatch.setattr(main, "replay_chain", failed_replay)

    response = client.post(
        "/experiments/EXP001/chains/mitigation/replay",
        json={
            "chain_id": "CHAIN001",
            "control_name": "authorization_gate",
        },
    )

    assert response.status_code == 502
    assert response.json() == {
        "detail": "Full-chain mitigation replay returned an invalid result"
    }
    assert calls == [
        ("EXP001", "CHAIN-AUTH-TOOL-MEM", "authorization_gate")
    ]
    assert "status_category=failed" in caplog.text
    assert executor_error not in caplog.text
    assert executor_error not in response.text
    assert database.evaluation_results.documents == []


def test_full_chain_mitigation_replay_rejects_malformed_completed_result(
    chain_mitigation_replay_context,
    monkeypatch,
):
    client, database, calls, _ = chain_mitigation_replay_context
    calls.clear()

    def malformed_replay(experiment_id, chain_id, control_name):
        calls.append((experiment_id, chain_id, control_name))
        return {"status": "completed", "chain_steps": []}

    monkeypatch.setattr(main, "replay_chain", malformed_replay)

    response = client.post(
        "/experiments/EXP001/chains/mitigation/replay",
        json={
            "chain_id": "CHAIN001",
            "control_name": "authorization_gate",
        },
    )

    assert response.status_code == 502
    assert response.json() == {
        "detail": "Full-chain mitigation replay returned an invalid result"
    }
    assert calls == [
        ("EXP001", "CHAIN-AUTH-TOOL-MEM", "authorization_gate")
    ]
    assert database.evaluation_results.documents == []


@pytest.mark.parametrize("result_id_mode", ["missing", "mismatched"])
def test_full_chain_mitigation_replay_rejects_invalid_canonical_result_id(
    chain_mitigation_replay_context,
    monkeypatch,
    result_id_mode,
):
    client, database, calls, replay_result = chain_mitigation_replay_context
    calls.clear()
    invalid_result = deepcopy(replay_result)
    if result_id_mode == "missing":
        invalid_result.pop("chain_id")
    else:
        invalid_result["chain_id"] = "CHAIN-OTHER"

    def invalid_id_replay(experiment_id, chain_id, control_name):
        calls.append((experiment_id, chain_id, control_name))
        return invalid_result

    monkeypatch.setattr(main, "replay_chain", invalid_id_replay)

    response = client.post(
        "/experiments/EXP001/chains/mitigation/replay",
        json={
            "chain_id": "CHAIN001",
            "control_name": "authorization_gate",
        },
    )

    assert response.status_code == 502
    assert response.json() == {
        "detail": "Full-chain mitigation replay returned an invalid result"
    }
    assert calls == [
        ("EXP001", "CHAIN-AUTH-TOOL-MEM", "authorization_gate")
    ]
    assert database.evaluation_results.documents == []


@pytest.mark.parametrize(
    ("mutation", "mutate"),
    [
        (
            "step_order",
            lambda result: result.update(
                chain_steps=[
                    "permission_test",
                    "memory_access_test",
                    "tool_access_test",
                ]
            ),
        ),
        (
            "chain_length",
            lambda result: result.update(chain_length=2),
        ),
        (
            "before_results",
            lambda result: result.update(before=[]),
        ),
        (
            "after_result_item",
            lambda result: result["after"].__setitem__(1, None),
        ),
        (
            "before_validation",
            lambda result: result["before_validation"].update(
                validated_steps=2
            ),
        ),
        (
            "after_validation",
            lambda result: result["after_validation"].update(
                valid="true"
            ),
        ),
        (
            "activation",
            lambda result: result["activation"].update(status="failed"),
        ),
        (
            "blocked_steps",
            lambda result: result.update(blocked_steps=[]),
        ),
        (
            "residual_steps",
            lambda result: result.update(residual_vulnerable_steps=[]),
        ),
        (
            "chain_disrupted",
            lambda result: result.update(chain_disrupted=False),
        ),
        (
            "final_validation",
            lambda result: result["validation_result"].update(
                status="invalid"
            ),
        ),
        (
            "reset",
            lambda result: result["reset"].update(status="failed"),
        ),
    ],
)
def test_full_chain_mitigation_replay_rejects_inconsistent_result_without_overwriting_evidence(
    chain_mitigation_replay_context,
    monkeypatch,
    mutation,
    mutate,
):
    client, database, calls, replay_result = chain_mitigation_replay_context
    calls.clear()
    invalid_result = deepcopy(replay_result)
    mutate(invalid_result)
    existing_record = {
        "evaluation_type": "phase3_chain_mitigation_replay",
        "experiment_id": "EXP001",
        "chain_id": "CHAIN-EXISTING",
        "status": "completed",
        "evidence_marker": "must remain unchanged",
    }
    database.evaluation_results.documents.append(
        deepcopy(existing_record)
    )
    original_records = deepcopy(database.evaluation_results.documents)

    monkeypatch.setattr(
        main,
        "replay_chain",
        lambda experiment_id, chain_id, control_name: invalid_result,
    )

    response = client.post(
        "/experiments/EXP001/chains/mitigation/replay",
        json={
            "chain_id": "CHAIN001",
            "control_name": "authorization_gate",
        },
    )

    assert response.status_code == 502, mutation
    assert response.json() == {
        "detail": "Full-chain mitigation replay returned an invalid result"
    }
    assert database.evaluation_results.documents == original_records


def test_full_chain_mitigation_replay_hides_p4_exception_details(
    chain_mitigation_replay_context,
    monkeypatch,
):
    client, database, calls, _ = chain_mitigation_replay_context
    calls.clear()

    def raising_replay(*args):
        calls.append(args)
        raise RuntimeError("internal replay details")

    monkeypatch.setattr(main, "replay_chain", raising_replay)

    response = client.post(
        "/experiments/EXP001/chains/mitigation/replay",
        json={
            "chain_id": "CHAIN001",
            "control_name": "authorization_gate",
        },
    )

    assert response.status_code == 502
    assert response.json() == {
        "detail": "Full-chain mitigation replay failed"
    }
    assert "internal replay details" not in response.text
    assert calls == [
        ("EXP001", "CHAIN-AUTH-TOOL-MEM", "authorization_gate")
    ]
    assert database.evaluation_results.documents == []


def test_p4_association_rejects_unknown_definition_without_mutation(
    chain_mitigation_replay_context,
    monkeypatch,
):
    client, database, replay_calls, _ = chain_mitigation_replay_context
    original_chain = deepcopy(database.attack_chains.documents[0])
    registry_calls = []
    registered_chain_lookup = main.get_registered_chain

    def tracked_registry_lookup(p4_chain_id):
        registry_calls.append(p4_chain_id)
        return registered_chain_lookup(p4_chain_id)

    monkeypatch.setattr(
        main,
        "get_registered_chain",
        tracked_registry_lookup,
    )

    response = client.post(
        "/experiments/EXP001/chains/CHAIN001/p4-association",
        json={"p4_chain_id": "UNKNOWN-P4-CHAIN"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Registered P4 chain not found"}
    assert registry_calls == ["UNKNOWN-P4-CHAIN"]
    assert replay_calls == []
    assert database.attack_chains.documents[0] == original_chain
    assert database.evaluation_results.documents == []


def test_p4_association_rejects_incompatible_definition_without_mutation(
    chain_mitigation_replay_context,
    monkeypatch,
):
    client, database, replay_calls, _ = chain_mitigation_replay_context
    database.attack_chains.documents[0]["steps"] = [
        "permission_test",
        "memory_access_test",
        "tool_access_test",
    ]
    original_chain = deepcopy(database.attack_chains.documents[0])
    registry_calls = []
    registered_chain_lookup = main.get_registered_chain

    def tracked_registry_lookup(p4_chain_id):
        registry_calls.append(p4_chain_id)
        return registered_chain_lookup(p4_chain_id)

    monkeypatch.setattr(
        main,
        "get_registered_chain",
        tracked_registry_lookup,
    )

    response = client.post(
        "/experiments/EXP001/chains/CHAIN001/p4-association",
        json={"p4_chain_id": "CHAIN-AUTH-TOOL-MEM"},
    )

    assert response.status_code == 409
    assert "ordered steps do not match" in response.json()["detail"]
    assert registry_calls == ["CHAIN-AUTH-TOOL-MEM"]
    assert replay_calls == []
    assert database.attack_chains.documents[0] == original_chain
    assert database.evaluation_results.documents == []


def test_p4_association_returns_404_for_missing_experiment(
    chain_mitigation_replay_context,
):
    client, database, replay_calls, _ = chain_mitigation_replay_context
    original_chain = deepcopy(database.attack_chains.documents[0])
    database.experiments = FakeCollection()

    response = client.post(
        "/experiments/MISSING/chains/CHAIN001/p4-association",
        json={"p4_chain_id": "CHAIN-AUTH-TOOL-MEM"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Experiment not found"}
    assert database.attack_chains.documents[0] == original_chain
    assert replay_calls == []


@pytest.mark.parametrize(
    "stored_chain",
    [
        None,
        {
            "chain_id": "CHAIN001",
            "experiment_id": "EXP999",
            "steps": [
                "permission_test",
                "tool_access_test",
                "memory_access_test",
            ],
        },
    ],
)
def test_p4_association_returns_404_for_missing_or_foreign_chain(
    chain_mitigation_replay_context,
    stored_chain,
):
    client, database, replay_calls, _ = chain_mitigation_replay_context
    database.attack_chains = FakeCollection(
        [] if stored_chain is None else [stored_chain]
    )
    original_chains = deepcopy(database.attack_chains.documents)

    response = client.post(
        "/experiments/EXP001/chains/CHAIN001/p4-association",
        json={"p4_chain_id": "CHAIN-AUTH-TOOL-MEM"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Chain not found"}
    assert database.attack_chains.documents == original_chains
    assert replay_calls == []


def test_p4_association_does_not_succeed_when_update_matches_no_record(
    chain_mitigation_replay_context,
    monkeypatch,
):
    client, database, replay_calls, _ = chain_mitigation_replay_context
    chain = database.attack_chains.documents[0]
    chain.pop("p4_chain_id")
    chain.pop("dependencies")
    original_chain = deepcopy(chain)
    update_calls = []

    def unmatched_update(query, update):
        update_calls.append((query, update))
        return SimpleNamespace(
            acknowledged=True,
            matched_count=0,
            modified_count=0,
        )

    monkeypatch.setattr(
        database.attack_chains,
        "update_one",
        unmatched_update,
    )

    response = client.post(
        "/experiments/EXP001/chains/CHAIN001/p4-association",
        json={"p4_chain_id": "CHAIN-AUTH-TOOL-MEM"},
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Chain association could not be persisted"
    }
    assert len(update_calls) == 1
    assert database.attack_chains.documents[0] == original_chain
    assert replay_calls == []


@pytest.mark.parametrize(
    ("p4_chain_id", "dependencies"),
    [
        (None, None),
        ("UNKNOWN-P4-CHAIN", {
            "permission_test": [],
            "tool_access_test": ["permission_test"],
            "memory_access_test": ["tool_access_test"],
        }),
    ],
)
def test_full_chain_mitigation_replay_rejects_unbound_or_unknown_association(
    chain_mitigation_replay_context,
    p4_chain_id,
    dependencies,
):
    client, database, calls, _ = chain_mitigation_replay_context
    chain = database.attack_chains.documents[0]
    if p4_chain_id is None:
        chain.pop("p4_chain_id")
        chain.pop("dependencies")
    else:
        chain["p4_chain_id"] = p4_chain_id
        chain["dependencies"] = dependencies

    response = client.post(
        "/experiments/EXP001/chains/mitigation/replay",
        json={
            "chain_id": "CHAIN001",
            "control_name": "authorization_gate",
        },
    )

    assert response.status_code == 409
    assert calls == []
    assert database.evaluation_results.documents == []


@pytest.mark.parametrize(
    ("field", "value"),
    [
        (
            "steps",
            ["permission_test", "memory_access_test", "tool_access_test"],
        ),
        (
            "dependencies",
            {
                "permission_test": [],
                "tool_access_test": [],
                "memory_access_test": ["tool_access_test"],
            },
        ),
    ],
)
def test_full_chain_mitigation_replay_rejects_incompatible_association(
    chain_mitigation_replay_context,
    field,
    value,
):
    client, database, calls, _ = chain_mitigation_replay_context
    database.attack_chains.documents[0][field] = value

    response = client.post(
        "/experiments/EXP001/chains/mitigation/replay",
        json={
            "chain_id": "CHAIN001",
            "control_name": "authorization_gate",
        },
    )

    assert response.status_code == 409
    assert calls == []
    assert database.evaluation_results.documents == []


def test_phase3_chain_validation_returns_and_persists_execution_cost(
    execution_context,
    monkeypatch,
):
    client, database, _, _, _, _ = execution_context
    phase1_record = {
        "evaluation_type": "phase1_validation",
        "experiment_id": "EXP001",
        "status": "validated",
    }
    phase2_record = {
        "evaluation_type": "phase2_mitigation",
        "experiment_id": "EXP001",
        "status": "completed",
    }
    database.evaluation_results.documents.extend(
        [phase1_record, phase2_record]
    )
    original_records = deepcopy(database.evaluation_results.documents)
    validation_result = {
        "chain_id": "CHAIN001",
        "status": "validated",
        "validated_steps": 2,
        "total_steps": 2,
        "chain_length": 2,
        "validation_rate": 1.0,
        "all_findings_reproduced": True,
        "steps": [
            {
                "test": "permission_test",
                "valid": True,
                "execution_cost": {
                    "test_count": 2,
                    "execution_time_seconds": 0.25,
                },
            },
            {
                "test": "tool_access_test",
                "valid": True,
                "execution_cost": {
                    "test_count": 3,
                    "execution_time_seconds": 0.5,
                },
            },
        ],
    }
    validator_calls = []

    class FakeChainValidator:
        def __init__(self, experiment_id):
            validator_calls.append(("init", experiment_id))

        def validate_chain(self, chain_id, steps):
            validator_calls.append(("validate", chain_id, steps))
            return validation_result

    monkeypatch.setattr(main, "ChainValidator", FakeChainValidator)

    response = client.post("/chains/CHAIN001/validate")

    expected_execution_cost = {
        "test_count": 5,
        "execution_time_seconds": 0.75,
    }
    assert response.status_code == 200
    assert response.json()["execution_cost"] == expected_execution_cost
    assert response.json()["chain_length"] == 2
    assert response.json()["validation_rate"] == 1.0
    assert validator_calls == [
        ("init", "EXP001"),
        ("validate", "CHAIN001", ["permission_test", "tool_access_test"]),
    ]
    assert database.evaluation_results.documents[:2] == original_records
    assert len(database.evaluation_results.documents) == 3
    persisted = database.evaluation_results.documents[2]
    assert persisted["evaluation_type"] == "phase3_chain_validation"
    assert persisted["experiment_id"] == "EXP001"
    assert persisted["chain_id"] == "CHAIN001"
    assert persisted["status"] == "validated"
    assert persisted["validated_steps"] == 2
    assert persisted["total_steps"] == 2
    assert persisted["chain_length"] == 2
    assert persisted["validation_rate"] == 1.0
    assert persisted["all_findings_reproduced"] is True
    assert persisted["steps"] == validation_result["steps"]
    assert persisted["execution_cost"] == expected_execution_cost
    assert persisted["timestamp"]


def test_phase3_chain_validation_returns_404_for_missing_chain(
    execution_context,
    monkeypatch,
):
    client, database, _, _, _, _ = execution_context
    database.attack_chains = FakeCollection()
    validator_calls = []

    class UnexpectedChainValidator:
        def __init__(self, experiment_id):
            validator_calls.append(experiment_id)

    monkeypatch.setattr(main, "ChainValidator", UnexpectedChainValidator)

    response = client.post("/chains/MISSING/validate")

    assert response.status_code == 404
    assert response.json() == {"detail": "Chain not found"}
    assert validator_calls == []
    assert database.evaluation_results.documents == []
