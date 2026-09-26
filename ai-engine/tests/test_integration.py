import pytest
from pydantic import ValidationError

from integration import (
    decision_to_sandbox_request,
    build_sandbox_execution_request,
)
from schemas import PlannerDecision


def create_decision(test_name: str) -> PlannerDecision:
    return PlannerDecision(
        selected_test=test_name,
        reason="The test may provide useful security evidence.",
        priority=0.8,
        confidence=0.9,
    )


def test_permission_test_conversion():
    decision = create_decision("permission_test")

    request = decision_to_sandbox_request(decision)

    assert request.test == "permission_test"


def test_tool_access_test_conversion():
    decision = create_decision("tool_access_test")

    request = decision_to_sandbox_request(decision)

    assert request.test == "tool_access_test"


def test_memory_access_test_conversion():
    decision = create_decision("memory_access_test")

    request = decision_to_sandbox_request(decision)

    assert request.test == "memory_access_test"


def test_invalid_test_is_rejected():
    decision = create_decision("invalid_test")

    with pytest.raises(ValueError, match="invalid sandbox test"):
        decision_to_sandbox_request(decision)


def test_planner_metadata_is_not_added_to_request():
    decision = create_decision("permission_test")

    request = decision_to_sandbox_request(decision)

    assert request.test == decision.selected_test
    assert not hasattr(request, "priority")
    assert not hasattr(request, "confidence")
    assert not hasattr(request, "reason")


def test_build_execution_request():
    decision = create_decision("permission_test")

    request = build_sandbox_execution_request(
        decision,
        "experiment-123"
    )

    assert request == {
        "experiment_id": "experiment-123",
        "test": "permission_test",
    }


def test_build_execution_request_preserves_experiment_id():
    decision = create_decision("tool_access_test")

    request = build_sandbox_execution_request(
        decision,
        "exp-456"
    )

    assert request["experiment_id"] == "exp-456"
    assert request["test"] == "tool_access_test"


def test_build_execution_request_rejects_empty_experiment_id():
    decision = create_decision("memory_access_test")

    with pytest.raises(ValueError, match="experiment_id must not be empty"):
        build_sandbox_execution_request(
            decision,
            ""
        )


def test_build_execution_request_rejects_invalid_test():
    decision = create_decision("invalid_test")

    with pytest.raises(ValueError, match="invalid sandbox test"):
        build_sandbox_execution_request(
            decision,
            "experiment-789"
        )