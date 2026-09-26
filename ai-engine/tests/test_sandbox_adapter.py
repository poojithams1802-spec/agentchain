import pytest

from sandbox_adapter import (
    execute_planned_test,
    validate_sandbox_response,
)
from schemas import PlannerDecision


def create_decision(test_name: str) -> PlannerDecision:
    return PlannerDecision(
        selected_test=test_name,
        reason="The test may provide useful security evidence.",
        priority=0.8,
        confidence=0.9,
    )


def test_permission_test_execution():
    decision = create_decision("permission_test")

    result = execute_planned_test(
        decision,
        "EXP001",
    )

    assert result["status"] == "completed"
    assert result["test"] == "permission_test"
    assert result["finding"] == "weak_permission_control"
    assert result["severity"] == "high"


def test_tool_access_test_execution():
    decision = create_decision("tool_access_test")

    result = execute_planned_test(
        decision,
        "EXP002",
    )

    assert result["status"] == "completed"
    assert result["test"] == "tool_access_test"
    assert result["finding"] == "unsafe_tool_access"
    assert result["severity"] == "high"


def test_memory_access_test_execution():
    decision = create_decision("memory_access_test")

    result = execute_planned_test(
        decision,
        "EXP003",
    )

    assert result["status"] == "completed"
    assert result["test"] == "memory_access_test"
    assert result["finding"] == "memory_validation_weakness"
    assert result["severity"] == "medium"


def test_empty_experiment_id_is_rejected():
    decision = create_decision("permission_test")

    with pytest.raises(
        ValueError,
        match="experiment_id must not be empty",
    ):
        execute_planned_test(
            decision,
            "",
        )


def test_invalid_planner_test_is_rejected():
    decision = create_decision("invalid_test")

    with pytest.raises(
        ValueError,
        match="invalid sandbox test",
    ):
        execute_planned_test(
            decision,
            "EXP004",
        )


def test_valid_completed_response():
    response = {
        "status": "completed",
        "test": "permission_test",
        "finding": "weak_permission_control",
        "severity": "high",
        "evidence": {},
    }

    result = validate_sandbox_response(response)

    assert result == response


def test_valid_failed_response():
    response = {
        "status": "failed",
        "test": "unknown_test",
        "finding": None,
        "severity": None,
        "evidence": "Unknown test: unknown_test",
    }

    result = validate_sandbox_response(response)

    assert result == response


def test_missing_response_field_is_rejected():
    response = {
        "status": "completed",
        "test": "permission_test",
        "finding": "weak_permission_control",
        "severity": "high",
    }

    with pytest.raises(
        ValueError,
        match="missing fields",
    ):
        validate_sandbox_response(response)


def test_invalid_status_is_rejected():
    response = {
        "status": "unknown",
        "test": "permission_test",
        "finding": "weak_permission_control",
        "severity": "high",
        "evidence": {},
    }

    with pytest.raises(
        ValueError,
        match="Invalid sandbox status",
    ):
        validate_sandbox_response(response)


def test_failed_response_with_finding_is_rejected():
    response = {
        "status": "failed",
        "test": "permission_test",
        "finding": "unexpected_finding",
        "severity": None,
        "evidence": "Something failed.",
    }

    with pytest.raises(
        ValueError,
        match="finding=None",
    ):
        validate_sandbox_response(response)