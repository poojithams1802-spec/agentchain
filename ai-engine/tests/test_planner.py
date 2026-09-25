import pytest
from pydantic import ValidationError

from planner import AdaptivePlanner
from schemas import (
    Finding,
    PlannerDecision,
    PlannerInput
)

def create_planner_input(
    available_tests=None,
    previous_tests=None
):
    if available_tests is None:
        available_tests = [
            "tool_access_test",
            "permission_test",
            "memory_validation_test"
        ]

    if previous_tests is None:
        previous_tests = []

    return PlannerInput(
        findings=[],
        previous_tests=previous_tests,
        available_tests=available_tests,
        retrieved_knowledge=[],
        chain_state={}
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

def test_prompt_includes_retrieved_knowledge():
    planner = AdaptivePlanner()

    planner_input = PlannerInput(
        findings=[],
        previous_tests=[],
        available_tests=[
            "check_tool_permissions"
        ],
        retrieved_knowledge=[
            "Sensitive tools must be checked "
            "against authorization policies."
        ],
        chain_state={}
    )

    prompt = planner.create_prompt(
        planner_input
    )

    assert (
        "authorization policies"
        in prompt
    )


def test_plan_includes_retrieved_knowledge_in_llm_prompt(
    monkeypatch
):
    planner = AdaptivePlanner()

    planner_input = PlannerInput(
        findings=[],
        previous_tests=[],
        available_tests=[
            "check_tool_permissions"
        ],
        retrieved_knowledge=[],
        chain_state={}
    )

    retrieved_knowledge = [
        "Tool access must follow authorization policies."
    ]

    captured_prompt = {}

    def fake_retrieve(query):
        return retrieved_knowledge

    def fake_generate_json(prompt):
        captured_prompt["value"] = prompt

        return {
            "selected_test": "check_tool_permissions",
            "reason": "Permission checks are relevant.",
            "priority": 0.8,
            "confidence": 0.9
        }

    monkeypatch.setattr(
        planner.retriever,
        "retrieve",
        fake_retrieve
    )

    monkeypatch.setattr(
        planner.llm_client,
        "generate_json",
        fake_generate_json
    )

    decision = planner.plan(
        planner_input
    )

    assert (
        "authorization policies"
        in captured_prompt["value"]
    )

    assert (
        decision.selected_test
        == "check_tool_permissions"
    )

import pytest

from planner import AdaptivePlanner
from schemas import PlannerInput


def test_validate_rejects_unavailable_test():
    planner = AdaptivePlanner()

    planner_input = create_planner_input()

    decision_data = {
        "selected_test": "unauthorized_test",
        "reason": "Invalid test",
        "priority": 0.5,
        "confidence": 0.8
    }

    with pytest.raises(
        ValueError,
        match="not in available_tests"
    ):
        planner.validate_decision(
            decision_data,
            planner_input
        )


def test_validate_rejects_previously_executed_test():
    planner = AdaptivePlanner()

    planner_input = create_planner_input(
        available_tests=[
            "check_tool_permissions"
        ],
        previous_tests=[
            "check_tool_permissions"
        ]
    )

    decision_data = {
        "selected_test": "check_tool_permissions",
        "reason": "Already executed",
        "priority": 0.5,
        "confidence": 0.8
    }

    with pytest.raises(
        ValueError,
        match="already executed"
    ):
        planner.validate_decision(
            decision_data,
            planner_input
        )


def test_fallback_rejects_when_no_tests_remain():
    planner = AdaptivePlanner()

    planner_input = create_planner_input(
        available_tests=[
            "check_tool_permissions"
        ],
        previous_tests=[
            "check_tool_permissions"
        ]
    )

    with pytest.raises(
        ValueError,
        match="No unexecuted sandbox tests"
    ):
        planner.fallback_decision(
            planner_input,
            reason="No valid LLM response"
        )


def test_validate_rejects_priority_above_one():
    planner = AdaptivePlanner()

    planner_input = create_planner_input(
    available_tests=[
        "check_tool_permissions",
        "inspect_input_validation"
    ])

    decision_data = {
        "selected_test": "check_tool_permissions",
        "reason": "Invalid priority",
        "priority": 1.5,
        "confidence": 0.8
    }

    with pytest.raises(ValueError):
        planner.validate_decision(
            decision_data,
            planner_input
        )


def test_validate_rejects_negative_confidence():
    planner = AdaptivePlanner()

    planner_input = create_planner_input()

    decision_data = {
        "selected_test": "check_tool_permissions",
        "reason": "Invalid confidence",
        "priority": 0.8,
        "confidence": -0.1
    }

    with pytest.raises(ValueError):
        planner.validate_decision(
            decision_data,
            planner_input
        )

def test_plan_returns_valid_decision_with_mocked_llm(
    monkeypatch
):
    planner = AdaptivePlanner()

    planner_input = create_planner_input(
        available_tests=[
            "check_tool_permissions",
            "inspect_input_validation"
        ]
    )

    def fake_retrieve(query):
        return [
            "Tool access must follow authorization policies."
        ]

    def fake_generate_json(prompt):
        return {
            "selected_test": "check_tool_permissions",
            "reason": (
                "Check whether tool permissions "
                "follow authorization policies."
            ),
            "priority": 0.9,
            "confidence": 0.95
        }

    monkeypatch.setattr(
        planner.retriever,
        "retrieve",
        fake_retrieve
    )

    monkeypatch.setattr(
        planner.llm_client,
        "generate_json",
        fake_generate_json
    )

    decision = planner.plan(planner_input)

    assert (
        decision.selected_test
        in planner_input.available_tests
    )

    assert (
        decision.selected_test
        not in planner_input.previous_tests
    )

    assert 0 <= decision.priority <= 1
    assert 0 <= decision.confidence <= 1

    assert len(
        planner_input.retrieved_knowledge
    ) > 0