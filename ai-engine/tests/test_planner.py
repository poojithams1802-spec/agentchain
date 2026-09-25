import pytest
from pydantic import ValidationError

from planner import AdaptivePlanner
from schemas import (
    Finding,
    PlannerDecision,
    PlannerInput
)


def create_planner_input() -> PlannerInput:
    return PlannerInput(
        findings=[
            Finding(
                finding="unsafe_tool_access",
                severity="high",
                confidence=0.9,
                evidence="Restricted tool was accessible."
            )
        ],
        previous_tests=[
            "initial_observation_test"
        ],
        available_tests=[
            "tool_access_test",
            "permission_test",
            "memory_validation_test"
        ],
        chain_state={
            "experiment_id": "TEST001",
            "step": 1
        }
    )


def test_valid_decision():
    planner = AdaptivePlanner()
    planner_input = create_planner_input()

    decision_data = {
        "selected_test": "permission_test",
        "reason": "Check permission boundaries.",
        "priority": 0.8,
        "confidence": 0.9
    }

    decision = planner.validate_decision(
        decision_data,
        planner_input
    )

    assert isinstance(
        decision,
        PlannerDecision
    )

    assert decision.selected_test == "permission_test"


def test_reject_unavailable_test():
    planner = AdaptivePlanner()
    planner_input = create_planner_input()

    decision_data = {
        "selected_test": "unknown_test",
        "reason": "This test is not allowed.",
        "priority": 0.5,
        "confidence": 0.5
    }

    with pytest.raises(ValueError):
        planner.validate_decision(
            decision_data,
            planner_input
        )


def test_reject_previous_test():
    planner = AdaptivePlanner()

    planner_input = create_planner_input()

    planner_input.previous_tests.append(
        "permission_test"
    )

    decision_data = {
        "selected_test": "permission_test",
        "reason": "This test was already executed.",
        "priority": 0.5,
        "confidence": 0.5
    }

    with pytest.raises(ValueError):
        planner.validate_decision(
            decision_data,
            planner_input
        )


def test_fallback_selects_unexecuted_test():
    planner = AdaptivePlanner()
    planner_input = create_planner_input()

    decision = planner.fallback_decision(
        planner_input,
        reason="Testing fallback behavior."
    )

    assert decision.selected_test == "tool_access_test"

    assert (
        decision.selected_test
        not in planner_input.previous_tests
    )

    assert decision.priority == 0.1
    assert decision.confidence == 0.1


def test_fallback_skips_executed_tests():
    planner = AdaptivePlanner()
    planner_input = create_planner_input()

    planner_input.previous_tests.extend([
        "tool_access_test",
        "permission_test"
    ])

    decision = planner.fallback_decision(
        planner_input,
        reason="Skip executed tests."
    )

    assert (
        decision.selected_test
        == "memory_validation_test"
    )


def test_fallback_fails_when_no_tests_remain():
    planner = AdaptivePlanner()

    planner_input = create_planner_input()

    planner_input.previous_tests = [
        "tool_access_test",
        "permission_test",
        "memory_validation_test"
    ]

    with pytest.raises(ValueError):
        planner.fallback_decision(
            planner_input,
            reason="No tests remain."
        )


def test_priority_must_be_between_zero_and_one():
    with pytest.raises(ValidationError):
        PlannerDecision(
            selected_test="permission_test",
            reason="Invalid priority.",
            priority=1.5,
            confidence=0.8
        )


def test_confidence_must_be_between_zero_and_one():
    with pytest.raises(ValidationError):
        PlannerDecision(
            selected_test="permission_test",
            reason="Invalid confidence.",
            priority=0.8,
            confidence=-0.1
        )

def test_plan_uses_fallback_when_llm_fails(
    monkeypatch
):
    planner = AdaptivePlanner()
    planner_input = create_planner_input()

    def failing_generate_json(prompt):
        raise RuntimeError(
            "Simulated LLM failure"
        )

    monkeypatch.setattr(
        planner.llm_client,
        "generate_json",
        failing_generate_json
    )

    decision = planner.plan(
        planner_input
    )

    assert (
        decision.selected_test
        in planner_input.available_tests
    )

    assert (
        decision.selected_test
        not in planner_input.previous_tests
    )

    assert decision.priority == 0.1
    assert decision.confidence == 0.1