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
    assert result["confidence"] == 1.0


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
    assert result["confidence"] == 1.0


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
    assert result["confidence"] == 1.0


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
        "confidence": 1.0,
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
        "confidence": 0.0,
    }

    result = validate_sandbox_response(response)

    assert result == response


def test_missing_response_field_is_rejected():
    response = {
        "status": "completed",
        "test": "permission_test",
        "finding": "weak_permission_control",
        "severity": "high",
        "evidence": {},
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
        "confidence": 1.0,
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
        "confidence": 0.0,
    }

    with pytest.raises(
        ValueError,
        match="finding=None",
    ):
        validate_sandbox_response(response)


def test_confidence_zero_is_valid():
    response = {
        "status": "completed",
        "test": "permission_test",
        "finding": "some_finding",
        "severity": "low",
        "evidence": {},
        "confidence": 0.0,
    }

    result = validate_sandbox_response(response)

    assert result["confidence"] == 0.0


def test_confidence_one_is_valid():
    response = {
        "status": "completed",
        "test": "permission_test",
        "finding": "some_finding",
        "severity": "high",
        "evidence": {},
        "confidence": 1.0,
    }

    result = validate_sandbox_response(response)

    assert result["confidence"] == 1.0


def test_negative_confidence_is_rejected():
    response = {
        "status": "completed",
        "test": "permission_test",
        "finding": "some_finding",
        "severity": "high",
        "evidence": {},
        "confidence": -0.1,
    }

    with pytest.raises(
        ValueError,
        match="between 0.0 and 1.0",
    ):
        validate_sandbox_response(response)


def test_confidence_above_one_is_rejected():
    response = {
        "status": "completed",
        "test": "permission_test",
        "finding": "some_finding",
        "severity": "high",
        "evidence": {},
        "confidence": 1.1,
    }

    with pytest.raises(
        ValueError,
        match="between 0.0 and 1.0",
    ):
        validate_sandbox_response(response)


def test_non_numeric_confidence_is_rejected():
    response = {
        "status": "completed",
        "test": "permission_test",
        "finding": "some_finding",
        "severity": "high",
        "evidence": {},
        "confidence": "high",
    }

    with pytest.raises(
        ValueError,
        match="must be numeric",
    ):
        validate_sandbox_response(response)


def test_failed_response_with_nonzero_confidence_is_rejected():
    response = {
        "status": "failed",
        "test": "permission_test",
        "finding": None,
        "severity": None,
        "evidence": "Test failed.",
        "confidence": 1.0,
    }

    with pytest.raises(
        ValueError,
        match="confidence=0.0",
    ):
        validate_sandbox_response(response)