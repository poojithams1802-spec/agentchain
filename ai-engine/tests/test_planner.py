import pytest
from pydantic import ValidationError

from planner import AdaptivePlanner
from schemas import (
    Finding,
    PlannerDecision,
    PlannerInput
)

from planner import AdaptivePlanner
from adaptive_loop import AdaptiveLoop
from schemas import Finding, PlannerInput
from scoring import CandidateMetadata


def test_fallback_decision_uses_highest_ranked_candidate():
    planner = AdaptivePlanner()

    planner_input = PlannerInput(
        findings=[
            Finding(
                finding="weak_permission_control",
                severity="high",
                confidence=1.0,
                evidence="Unauthorized permission access.",
            )
        ],
        previous_tests=[
            "permission_test"
        ],
        available_tests=[
            "permission_test",
            "tool_access_test",
            "memory_access_test",
        ],
    )

    decision = planner.fallback_decision(
        planner_input,
        reason="LLM unavailable.",
    )

    assert decision.selected_test == "tool_access_test"
    assert decision.priority > 0.0
    assert decision.confidence == 0.1
    assert "highest-ranked" in decision.reason

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

    assert decision.selected_test in planner_input.available_tests
    assert decision.selected_test not in planner_input.previous_tests

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

    assert (
        decision.selected_test
        in planner_input.available_tests
    )

    assert (
        decision.selected_test
        not in planner_input.previous_tests
    )

    assert decision.priority > 0.0
    assert decision.confidence == 0.1
    assert (
        decision.selected_test
        not in planner_input.previous_tests
    )

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
    assert decision.priority > 0.0
    assert decision.confidence == 0.1
    assert (
        "highest-ranked"
        in decision.reason
    )
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


# ============================================================
# Additional tests for RAG and planner integration
# ============================================================


def test_build_query_includes_finding_details():
    planner = AdaptivePlanner()

    planner_input = PlannerInput(
        findings=[
            Finding(
                finding="Possible unsafe tool access",
                severity="high",
                confidence=0.9,
                evidence="Tool permission was not checked."
            )
        ],
        previous_tests=[
            "initial_scan"
        ],
        available_tests=[
            "permission_test"
        ],
        retrieved_knowledge=[],
        chain_state={
            "stage": "initial",
            "attempt": 1
        }
    )

    query = planner.build_query(
        planner_input
    )

    assert (
        "Possible unsafe tool access"
        in query
    )

    assert "high" in query

    assert (
        "Tool permission was not checked."
        in query
    )

    assert "initial_scan" in query

    assert "permission_test" in query

    assert "stage" in query

    assert "initial" in query


def test_build_query_returns_empty_for_empty_input():
    planner = AdaptivePlanner()

    planner_input = PlannerInput(
        findings=[],
        previous_tests=[],
        available_tests=[
            "permission_test"
        ],
        retrieved_knowledge=[],
        chain_state={}
    )

    query = planner.build_query(
        planner_input
    )

    # The available test is part of the query,
    # so the query should not be empty.
    assert "permission_test" in query


def test_retrieve_knowledge_uses_retriever(
    monkeypatch
):
    planner = AdaptivePlanner()

    planner_input = PlannerInput(
        findings=[
            Finding(
                finding="Unsafe tool access",
                severity="high",
                confidence=0.9,
                evidence="Permission validation missing."
            )
        ],
        previous_tests=[],
        available_tests=[
            "permission_test"
        ],
        retrieved_knowledge=[],
        chain_state={}
    )

    captured_query = {}

    def fake_retrieve(
        query,
        top_k=3
    ):
        captured_query["query"] = query
        captured_query["top_k"] = top_k

        return [
            "Tool access requires authorization."
        ]

    monkeypatch.setattr(
        planner.retriever,
        "retrieve",
        fake_retrieve
    )

    results = planner.retrieve_knowledge(
        planner_input
    )

    assert results == [
        "Tool access requires authorization."
    ]

    assert (
        "Unsafe tool access"
        in captured_query["query"]
    )

    assert captured_query["top_k"] == 3


def test_retrieve_knowledge_handles_failure(
    monkeypatch
):
    planner = AdaptivePlanner()

    planner_input = PlannerInput(
        findings=[],
        previous_tests=[],
        available_tests=[
            "permission_test"
        ],
        retrieved_knowledge=[],
        chain_state={}
    )

    def failing_retrieve(
        query,
        top_k=3
    ):
        raise RuntimeError(
            "Simulated retrieval failure"
        )

    monkeypatch.setattr(
        planner.retriever,
        "retrieve",
        failing_retrieve
    )

    results = planner.retrieve_knowledge(
        planner_input
    )

    assert results == []


def test_prompt_contains_available_tests():
    planner = AdaptivePlanner()

    planner_input = PlannerInput(
        findings=[],
        previous_tests=[],
        available_tests=[
            "permission_test",
            "memory_validation_test"
        ],
        retrieved_knowledge=[],
        chain_state={}
    )

    prompt = planner.create_prompt(
        planner_input
    )

    assert "permission_test" in prompt

    assert (
        "memory_validation_test"
        in prompt
    )


def test_prompt_contains_previous_tests():
    planner = AdaptivePlanner()

    planner_input = PlannerInput(
        findings=[],
        previous_tests=[
            "permission_test"
        ],
        available_tests=[
            "memory_validation_test"
        ],
        retrieved_knowledge=[],
        chain_state={}
    )

    prompt = planner.create_prompt(
        planner_input
    )

    assert "permission_test" in prompt

    assert (
        "previous_tests"
        in prompt
    )


def test_prompt_contains_chain_state():
    planner = AdaptivePlanner()

    planner_input = PlannerInput(
        findings=[],
        previous_tests=[],
        available_tests=[
            "permission_test"
        ],
        retrieved_knowledge=[],
        chain_state={
            "current_stage": "validation",
            "attempt_number": 2
        }
    )

    prompt = planner.create_prompt(
        planner_input
    )

    assert (
        "current_stage"
        in prompt
    )

    assert (
        "validation"
        in prompt
    )

    assert (
        "attempt_number"
        in prompt
    )


def test_prompt_contains_safety_rules():
    planner = AdaptivePlanner()

    planner_input = PlannerInput(
        findings=[],
        previous_tests=[],
        available_tests=[
            "permission_test"
        ],
        retrieved_knowledge=[],
        chain_state={}
    )

    prompt = planner.create_prompt(
        planner_input
    )

    assert (
        "Do not target external systems"
        in prompt
    )

    assert (
        "Do not invent a test"
        in prompt
    )

    assert (
        "previous_tests"
        in prompt
    )


def test_prompt_contains_retrieved_knowledge_section():
    planner = AdaptivePlanner()

    planner_input = PlannerInput(
        findings=[],
        previous_tests=[],
        available_tests=[
            "permission_test"
        ],
        retrieved_knowledge=[
            (
                "Sensitive tools must be checked "
                "against authorization policies."
            )
        ],
        chain_state={}
    )

    prompt = planner.create_prompt(
        planner_input
    )

    assert (
        "retrieved_knowledge"
        in prompt
    )

    assert (
        "authorization policies"
        in prompt
    )


def test_plan_stores_retrieved_knowledge(
    monkeypatch
):
    planner = AdaptivePlanner()

    planner_input = PlannerInput(
        findings=[],
        previous_tests=[],
        available_tests=[
            "permission_test",
            "memory_validation_test"
        ],
        retrieved_knowledge=[],
        chain_state={}
    )

    expected_knowledge = [
        "Tool access requires authorization."
    ]

    def fake_retrieve(
        query,
        top_k=3
    ):
        return expected_knowledge

    def fake_generate_json(prompt):
        return {
            "selected_test": "permission_test",
            "reason": (
                "Permission validation is relevant."
            ),
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
        decision.selected_test
        == "permission_test"
    )

    assert (
        planner_input.retrieved_knowledge
        == expected_knowledge
    )


def test_plan_falls_back_when_retrieval_fails(
    monkeypatch
):
    planner = AdaptivePlanner()

    planner_input = PlannerInput(
        findings=[],
        previous_tests=[],
        available_tests=[
            "permission_test",
            "memory_validation_test"
        ],
        retrieved_knowledge=[],
        chain_state={}
    )

    def failing_retrieve(
        query,
        top_k=3
    ):
        raise RuntimeError(
            "Retrieval unavailable"
        )

    def fake_generate_json(prompt):
        return {
            "selected_test": "permission_test",
            "reason": (
                "Permission validation is relevant."
            ),
            "priority": 0.8,
            "confidence": 0.9
        }

    monkeypatch.setattr(
        planner.retriever,
        "retrieve",
        failing_retrieve
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
        decision.selected_test
        == "permission_test"
    )

    assert (
        planner_input.retrieved_knowledge
        == []
    )


def test_plan_rejects_llm_previous_test_and_falls_back(
    monkeypatch
):
    planner = AdaptivePlanner()

    planner_input = PlannerInput(
        findings=[],
        previous_tests=[
            "permission_test"
        ],
        available_tests=[
            "permission_test",
            "memory_validation_test"
        ],
        retrieved_knowledge=[],
        chain_state={}
    )

    def fake_retrieve(
        query,
        top_k=3
    ):
        return [
            "Permission validation is required."
        ]

    def fake_generate_json(prompt):
        return {
            "selected_test": "permission_test",
            "reason": (
                "This test appears relevant."
            ),
            "priority": 0.9,
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
        decision.selected_test
        == "memory_validation_test"
    )

    assert (
        decision.selected_test
        not in planner_input.previous_tests
    )


    assert decision.priority > 0.0
    assert decision.confidence == 0.1
    assert (
        "highest-ranked"
        in decision.reason
    )
    assert decision.confidence == 0.1


def test_plan_rejects_unavailable_llm_test(
    monkeypatch
):
    planner = AdaptivePlanner()

    planner_input = PlannerInput(
        findings=[],
        previous_tests=[],
        available_tests=[
            "permission_test",
            "memory_validation_test"
        ],
        retrieved_knowledge=[],
        chain_state={}
    )

    def fake_retrieve(
        query,
        top_k=3
    ):
        return []

    def fake_generate_json(prompt):
        return {
            "selected_test": "invented_test",
            "reason": (
                "This test was invented by the model."
            ),
            "priority": 0.9,
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
        decision.selected_test
        == "permission_test"
    )

    assert decision.priority > 0.0
    assert decision.confidence == 0.1
    assert (
        "highest-ranked"
        in decision.reason
    )
    assert decision.confidence == 0.1


def test_plan_does_not_call_llm_when_all_tests_executed(
    monkeypatch
):
    planner = AdaptivePlanner()

    planner_input = PlannerInput(
        findings=[],
        previous_tests=[
            "permission_test"
        ],
        available_tests=[
            "permission_test"
        ],
        retrieved_knowledge=[],
        chain_state={}
    )

    llm_called = {
        "value": False
    }

    def fake_generate_json(prompt):
        llm_called["value"] = True

        return {
            "selected_test": "permission_test",
            "reason": "Should not be called.",
            "priority": 0.8,
            "confidence": 0.9
        }

    monkeypatch.setattr(
        planner.llm_client,
        "generate_json",
        fake_generate_json
    )

    with pytest.raises(
        ValueError,
        match="No unexecuted sandbox tests"
    ):
        planner.plan(
            planner_input
        )

    assert (
        llm_called["value"]
        is False
    )

def test_fallback_decision_uses_highest_ranked_candidate(monkeypatch):
    planner = AdaptivePlanner()

    planner_input = PlannerInput(
        findings=[
            Finding(
                finding="weak_permission_control",
                severity="high",
                confidence=1.0,
                evidence="Unauthorized permission access.",
            )
        ],
        previous_tests=[
            "permission_test"
        ],
        available_tests=[
            "permission_test",
            "tool_access_test",
            "memory_access_test",
        ],
    )

    decision = planner.fallback_decision(
        planner_input,
        reason="LLM unavailable.",
    )

    assert decision.selected_test == "tool_access_test"
    assert decision.priority > 0.0
    assert decision.confidence == 0.1
    assert "highest-ranked" in decision.reason

def test_rag_relevance_for_permission_test():
    planner = AdaptivePlanner()

    relevance = planner.calculate_rag_relevance(
        "permission_test",
        [
            "Every sensitive tool request should be checked "
            "against the current user or agent permissions."
        ],
    )

    assert relevance > 0.0
    assert relevance <= 1.0

def test_rag_relevance_for_tool_access_test():
    planner = AdaptivePlanner()

    relevance = planner.calculate_rag_relevance(
        "tool_access_test",
        [
            "An agent should only invoke tools explicitly "
            "permitted by its authorization policy."
        ],
    )

    assert relevance > 0.0
    assert relevance <= 1.0

def test_rag_relevance_for_memory_access_test():
    planner = AdaptivePlanner()

    relevance = planner.calculate_rag_relevance(
        "memory_access_test",
        [
            "Information written to agent memory should be "
            "validated and should not automatically be "
            "treated as trusted instructions."
        ],
    )

    assert relevance > 0.0
    assert relevance <= 1.0


def test_rag_relevance_unrelated_knowledge():
    planner = AdaptivePlanner()

    relevance = planner.calculate_rag_relevance(
        "memory_access_test",
        [
            "An agent should only invoke tools explicitly "
            "permitted by its authorization policy."
        ],
    )

    assert relevance == 0.0


def test_rag_increases_permission_candidate_relevance():
    planner = AdaptivePlanner()

    planner_input = PlannerInput(
        findings=[],
        previous_tests=[],
        available_tests=[
            "permission_test",
            "tool_access_test",
            "memory_access_test",
        ],
        retrieved_knowledge=[
            "Sensitive requests must be checked "
            "against current permissions and authorization."
        ],
        chain_state={},
    )

    candidates = planner.build_candidates(
        planner_input
    )

    permission_candidate = next(
        candidate
        for candidate in candidates
        if candidate.test_name == "permission_test"
    )

    assert permission_candidate.relevance > 0.5

def test_rag_increases_tool_candidate_relevance():
    planner = AdaptivePlanner()

    planner_input = PlannerInput(
        findings=[],
        previous_tests=[
            "permission_test"
        ],
        available_tests=[
            "permission_test",
            "tool_access_test",
            "memory_access_test",
        ],
        retrieved_knowledge=[
            "Agents should not receive "
            "unsafe tool access without authorization."
        ],
        chain_state={},
    )

    candidates = planner.build_candidates(
        planner_input
    )

    tool_candidate = next(
        candidate
        for candidate in candidates
        if candidate.test_name == "tool_access_test"
    )

    assert tool_candidate.relevance >= 0.85

def test_rag_increases_memory_candidate_relevance():
    planner = AdaptivePlanner()

    planner_input = PlannerInput(
        findings=[],
        previous_tests=[
            "permission_test",
            "tool_access_test"
        ],
        available_tests=[
            "permission_test",
            "tool_access_test",
            "memory_access_test",
        ],
        retrieved_knowledge=[
            "Information written to agent memory "
            "must be validated before being trusted."
        ],
        chain_state={},
    )

    candidates = planner.build_candidates(
        planner_input
    )

    memory_candidate = next(
        candidate
        for candidate in candidates
        if candidate.test_name == "memory_access_test"
    )

    assert memory_candidate.relevance >= 0.85


def test_rag_influences_eligible_candidate_scoring():
    planner = AdaptivePlanner()

    planner_input = PlannerInput(
        findings=[],
        previous_tests=[
            "permission_test"
        ],
        available_tests=[
            "permission_test",
            "tool_access_test",
            "memory_access_test",
        ],
        retrieved_knowledge=[
            "Sensitive tools must be checked "
            "against authorization policies."
        ],
        chain_state={},
    )

    ranked_candidates = planner.rank_candidates(
        planner_input
    )

    assert ranked_candidates

    # Because permission_test has already been executed
    # and memory_access_test depends on tool_access_test,
    # tool_access_test is the only eligible candidate.
    ranked_names = [
        candidate.test_name
        for candidate, score in ranked_candidates
    ]

    assert ranked_names == [
        "tool_access_test"
    ]

    selected_candidate = ranked_candidates[0][0]

    assert selected_candidate.test_name == "tool_access_test"

    # RAG knowledge about tool authorization must
    # increase the candidate's relevance.
    assert selected_candidate.relevance >= 0.85

    # The candidate must have a valid positive score.
    selected_score = ranked_candidates[0][1]

    assert selected_score > 0.0


def test_finding_and_rag_together_influence_ranking():
    planner = AdaptivePlanner()

    planner_input = PlannerInput(
        findings=[
            Finding(
                finding="unsafe_tool_access",
                severity="high",
                confidence=1.0,
                evidence=(
                    "A sensitive tool was accessed "
                    "without sufficient authorization."
                ),
            )
        ],
        previous_tests=[
            "permission_test"
        ],
        available_tests=[
            "permission_test",
            "tool_access_test",
            "memory_access_test",
        ],
        retrieved_knowledge=[
            "Sensitive tools must be protected "
            "by authorization checks."
        ],
        chain_state={},
    )

    ranked_candidates = planner.rank_candidates(
        planner_input
    )

    assert ranked_candidates

    selected_candidate = ranked_candidates[0][0]

    assert (
        selected_candidate.test_name
        == "tool_access_test"
    )

    assert selected_candidate.relevance >= 0.95


def test_planner_selects_rag_relevant_candidate(
    monkeypatch
):
    planner = AdaptivePlanner()

    planner_input = PlannerInput(
        findings=[
            Finding(
                finding="unsafe_tool_access",
                severity="high",
                confidence=1.0,
                evidence=(
                    "Sensitive tool access was allowed "
                    "without sufficient authorization."
                ),
            )
        ],
        previous_tests=[
            "permission_test"
        ],
        available_tests=[
            "permission_test",
            "tool_access_test",
            "memory_access_test",
        ],
        retrieved_knowledge=[],
        chain_state={},
    )

    def fake_retrieve(
        query,
        top_k=3,
    ):
        return [
            "Sensitive tools must be checked "
            "against authorization policies."
        ]

    def fake_generate_json(prompt):
        return {
            "selected_test": "tool_access_test",
            "reason": (
                "Tool access is relevant to the "
                "current security finding."
            ),
            "priority": 0.9,
            "confidence": 0.9,
        }

    monkeypatch.setattr(
        planner.retriever,
        "retrieve",
        fake_retrieve,
    )

    monkeypatch.setattr(
        planner.llm_client,
        "generate_json",
        fake_generate_json,
    )

    decision = planner.plan(
        planner_input
    )

    assert (
        decision.selected_test
        == "tool_access_test"
    )

    assert decision.priority > 0.0
    assert decision.confidence > 0.0

    assert (
        "Tool access"
        in decision.reason
    )

    assert (
        planner_input.retrieved_knowledge
    )

def test_day9_permission_scenario():
    planner = AdaptivePlanner()

    planner_input = PlannerInput(
        findings=[
            Finding(
                finding="weak_permission_control",
                severity="high",
                confidence=1.0,
                evidence="Unauthorized permission access was reproduced.",
            )
        ],
        previous_tests=[
            "permission_test"
        ],
        available_tests=[
            "permission_test",
            "tool_access_test",
            "memory_access_test",
        ],
        retrieved_knowledge=[
            "Sensitive tool requests should be checked "
            "against current permissions and authorization."
        ],
        chain_state={
            "step": 2,
        },
    )

    ranked = planner.rank_candidates(
        planner_input
    )

    assert ranked

    selected = ranked[0][0]

    assert selected.test_name == "tool_access_test"


def test_day9_tool_access_scenario():
    planner = AdaptivePlanner()

    planner_input = PlannerInput(
        findings=[
            Finding(
                finding="unsafe_tool_access",
                severity="high",
                confidence=1.0,
                evidence="Sensitive tool access bypassed authorization.",
            )
        ],
        previous_tests=[
            "permission_test",
            "tool_access_test",
        ],
        available_tests=[
            "permission_test",
            "tool_access_test",
            "memory_access_test",
        ],
        retrieved_knowledge=[
            "Information written to agent memory should be "
            "validated before being treated as trusted instructions."
        ],
        chain_state={
            "step": 3,
        },
    )

    ranked = planner.rank_candidates(
        planner_input
    )

    assert ranked

    selected = ranked[0][0]

    assert selected.test_name == "memory_access_test"

def test_day9_memory_security_scenario():
    planner = AdaptivePlanner()

    planner_input = PlannerInput(
        findings=[
            Finding(
                finding="memory_validation_weakness",
                severity="high",
                confidence=1.0,
                evidence="Untrusted information entered agent memory.",
            )
        ],
        previous_tests=[
            "permission_test",
            "tool_access_test",
        ],
        available_tests=[
            "permission_test",
            "tool_access_test",
            "memory_access_test",
        ],
        retrieved_knowledge=[
            "Information written to agent memory should be "
            "validated and should not automatically be "
            "treated as trusted instructions."
        ],
        chain_state={
            "step": 3,
        },
    )

    ranked = planner.rank_candidates(
        planner_input
    )

    assert ranked

    selected = ranked[0][0]

    assert selected.test_name == "memory_access_test"


def test_day9_memory_security_scenario():
    planner = AdaptivePlanner()

    planner_input = PlannerInput(
        findings=[
            Finding(
                finding="memory_validation_weakness",
                severity="high",
                confidence=1.0,
                evidence="Untrusted information entered agent memory.",
            )
        ],
        previous_tests=[
            "permission_test",
            "tool_access_test",
        ],
        available_tests=[
            "permission_test",
            "tool_access_test",
            "memory_access_test",
        ],
        retrieved_knowledge=[
            "Information written to agent memory should be "
            "validated and should not automatically be "
            "treated as trusted instructions."
        ],
        chain_state={
            "step": 3,
        },
    )

    ranked = planner.rank_candidates(
        planner_input
    )

    assert ranked

    selected = ranked[0][0]

    assert selected.test_name == "memory_access_test"


def test_day9_planner_never_reselects_previous_test():
    planner = AdaptivePlanner()

    planner_input = PlannerInput(
        findings=[
            Finding(
                finding="unsafe_tool_access",
                severity="high",
                confidence=1.0,
                evidence="Unsafe tool access reproduced.",
            )
        ],
        previous_tests=[
            "permission_test",
            "tool_access_test",
        ],
        available_tests=[
            "permission_test",
            "tool_access_test",
            "memory_access_test",
        ],
        retrieved_knowledge=[
            "Sensitive tools require authorization."
        ],
        chain_state={},
    )

    ranked = planner.rank_candidates(
        planner_input
    )

    assert ranked

    selected_names = [
        candidate.test_name
        for candidate, score in ranked
    ]

    assert (
        "permission_test"
        not in selected_names
    )

    assert (
        "tool_access_test"
        not in selected_names
    )

    assert (
        "memory_access_test"
        in selected_names
    )

def test_day9_complete_planner_scenario(
    monkeypatch,
):
    planner = AdaptivePlanner()

    planner_input = PlannerInput(
        findings=[
            Finding(
                finding="weak_permission_control",
                severity="high",
                confidence=1.0,
                evidence="Unauthorized permission access reproduced.",
            )
        ],
        previous_tests=[
            "permission_test",
        ],
        available_tests=[
            "permission_test",
            "tool_access_test",
            "memory_access_test",
        ],
        retrieved_knowledge=[],
        chain_state={
            "step": 2,
            "experiment_id": "DAY9_EXP_001",
        },
    )

    def fake_retrieve(
        query,
        top_k=3,
    ):
        return [
            "Sensitive tool requests should be checked "
            "against current permissions and authorization."
        ]

    def fake_generate_json(prompt):
        return {
            "selected_test": "tool_access_test",
            "reason": (
                "The permission finding and retrieved "
                "authorization knowledge indicate that "
                "tool access should be tested next."
            ),
            "priority": 0.9,
            "confidence": 0.9,
        }

    monkeypatch.setattr(
        planner.retriever,
        "retrieve",
        fake_retrieve,
    )

    monkeypatch.setattr(
        planner.llm_client,
        "generate_json",
        fake_generate_json,
    )

    decision = planner.plan(
        planner_input
    )

    assert (
        decision.selected_test
        == "tool_access_test"
    )

    assert decision.priority > 0.0
    assert decision.confidence > 0.0

    assert (
        "permission"
        in decision.reason.lower()
    )

    assert (
        "authorization"
        in decision.reason.lower()
    )

    assert planner_input.retrieved_knowledge


def test_day10_adaptive_permission_to_tool():
    planner = AdaptivePlanner()

    planner_input = PlannerInput(
        findings=[
            Finding(
                finding="weak_permission_control",
                severity="high",
                confidence=1.0,
                evidence="Unauthorized permission access reproduced.",
            )
        ],
        previous_tests=["permission_test"],
        available_tests=[
            "permission_test",
            "tool_access_test",
            "memory_access_test",
        ],
        retrieved_knowledge=[
            "Sensitive tools require proper permission and authorization."
        ],
        chain_state={
            "step": 2,
            "experiment_id": "DAY10_PERMISSION",
        },
    )

    ranked = planner.rank_candidates(planner_input)

    assert ranked

    next_test = ranked[0][0].test_name

    assert next_test == "tool_access_test"


def test_day10_adaptive_tool_to_memory():
    planner = AdaptivePlanner()

    planner_input = PlannerInput(
        findings=[
            Finding(
                finding="unsafe_tool_access",
                severity="high",
                confidence=1.0,
                evidence="Sensitive tool access bypassed authorization.",
            )
        ],
        previous_tests=[
            "permission_test",
            "tool_access_test",
        ],
        available_tests=[
            "permission_test",
            "tool_access_test",
            "memory_access_test",
        ],
        retrieved_knowledge=[
            "Untrusted information entering memory "
            "must be validated before being trusted."
        ],
        chain_state={
            "step": 3,
            "experiment_id": "DAY10_TOOL",
        },
    )

    ranked = planner.rank_candidates(planner_input)

    assert ranked

    next_test = ranked[0][0].test_name

    assert next_test == "memory_access_test"


def test_day10_adaptive_loop_changes_next_test():
    planner = AdaptivePlanner()

    planner_input = PlannerInput(
        findings=[],
        previous_tests=[],
        available_tests=[
            "permission_test",
            "tool_access_test",
            "memory_access_test",
        ],
        retrieved_knowledge=[],
        chain_state={
            "experiment_id": "DAY10_LOOP",
            "step": 1,
        },
    )

    decisions = [
        PlannerDecision(
            selected_test="permission_test",
            reason="Start with permission testing.",
            priority=0.9,
            confidence=0.9,
        ),
        PlannerDecision(
            selected_test="tool_access_test",
            reason="Permission weakness requires tool access testing.",
            priority=0.9,
            confidence=0.9,
        ),
    ]

    class FakePlanner:
        def __init__(self):
            self.calls = 0

        def plan(self, planner_input):
            decision = decisions[self.calls]
            self.calls += 1
            return decision

    fake_planner = FakePlanner()

    loop = AdaptiveLoop(planner=fake_planner)

    findings = loop.run(
        planner_input=planner_input,
        experiment_id="DAY10_LOOP",
        max_tests=2,
    )

    assert len(findings) == 2

    assert planner_input.previous_tests == [
        "permission_test",
        "tool_access_test",
    ]

    assert (
        findings[0].finding
        == "weak_permission_control"
    )

    assert (
        findings[1].finding
        == "unsafe_tool_access"
    )


def test_day10_finding_feedback_reaches_next_planner_call():
    planner_input = PlannerInput(
        findings=[],
        previous_tests=[],
        available_tests=[
            "permission_test",
            "tool_access_test",
            "memory_access_test",
        ],
        retrieved_knowledge=[],
        chain_state={
            "experiment_id": "DAY10_FEEDBACK",
        },
    )

    class InspectingPlanner:
        def __init__(self):
            self.calls = 0
            self.second_call_findings = None

        def plan(self, planner_input):
            self.calls += 1

            if self.calls == 1:
                return PlannerDecision(
                    selected_test="permission_test",
                    reason="Initial permission test.",
                    priority=0.9,
                    confidence=0.9,
                )

            self.second_call_findings = list(
                planner_input.findings
            )

            return PlannerDecision(
                selected_test="tool_access_test",
                reason="Follow up on permission finding.",
                priority=0.9,
                confidence=0.9,
            )

    inspecting_planner = InspectingPlanner()

    loop = AdaptiveLoop(
        planner=inspecting_planner
    )

    findings = loop.run(
        planner_input=planner_input,
        experiment_id="DAY10_FEEDBACK",
        max_tests=2,
    )

    assert len(findings) == 2

    assert (
        inspecting_planner.second_call_findings
    )

    assert (
        inspecting_planner.second_call_findings[0].finding
        == "weak_permission_control"
    )

def test_day10_comparison_static_chain_follows_fixed_order():
    static_chain = [
        "permission_test",
        "tool_access_test",
        "memory_access_test",
    ]

    assert static_chain[0] == "permission_test"
    assert static_chain[1] == "tool_access_test"
    assert static_chain[2] == "memory_access_test"


def test_day10_comparison_adaptive_chain_uses_finding():
    planner = AdaptivePlanner()

    planner_input = PlannerInput(
        findings=[
            Finding(
                finding="weak_permission_control",
                severity="high",
                confidence=1.0,
                evidence="Unauthorized permission access reproduced.",
            )
        ],
        previous_tests=[
            "permission_test",
        ],
        available_tests=[
            "permission_test",
            "tool_access_test",
            "memory_access_test",
        ],
        retrieved_knowledge=[
            "Sensitive tools require proper permission "
            "and authorization."
        ],
        chain_state={
            "experiment_id": "DAY10_COMPARISON",
            "step": 2,
        },
    )

    ranked = planner.rank_candidates(
        planner_input
    )

    assert ranked

    adaptive_next_test = ranked[0][0].test_name

    assert adaptive_next_test == "tool_access_test"

    static_next_test = "tool_access_test"

    assert adaptive_next_test == static_next_test

def test_day10_adaptive_choice_changes_with_finding():
    planner = AdaptivePlanner()

    # Scenario A: permission weakness
    permission_input = PlannerInput(
        findings=[
            Finding(
                finding="weak_permission_control",
                severity="high",
                confidence=1.0,
                evidence="Unauthorized permission access reproduced.",
            )
        ],
            previous_tests=[
                "permission_test",
            ],
        available_tests=[
            "permission_test",
            "tool_access_test",
            "memory_access_test",
        ],
        retrieved_knowledge=[
            "Sensitive tools require proper permission and authorization."
        ],
        chain_state={"step": 2},
    )

    permission_ranked = planner.rank_candidates(
        permission_input
    )

    permission_next = permission_ranked[0][0].test_name

    # Scenario B: no permission finding; memory-related finding
    memory_input = PlannerInput(
        findings=[
            Finding(
                finding="memory_validation_weakness",
                severity="high",
                confidence=1.0,
                evidence="Untrusted information entered agent memory.",
            )
        ],
        previous_tests=[
            "permission_test",
            "tool_access_test",
        ],
        available_tests=[
            "permission_test",
            "tool_access_test",
            "memory_access_test",
        ],
        retrieved_knowledge=[
            "Agent memory should validate untrusted information "
            "before treating it as trusted instructions."
        ],
        chain_state={"step": 1},
    )

    memory_ranked = planner.rank_candidates(
        memory_input
    )

    memory_next = memory_ranked[0][0].test_name

    assert permission_next == "tool_access_test"
    assert memory_next == "memory_access_test"

    # The planner reacted differently to the different findings.
    assert permission_next != memory_next

def test_day10_information_gain_affects_candidate_score():
    planner = AdaptivePlanner()

    low_gain = CandidateMetadata(
        test_name="memory_access_test",
        relevance=0.5,
        severity=0.5,
        confidence=0.5,
        expected_information_gain=0.4,
        testing_cost=0.3,
    )

    high_gain = CandidateMetadata(
        test_name="tool_access_test",
        relevance=0.5,
        severity=0.5,
        confidence=0.5,
        expected_information_gain=0.9,
        testing_cost=0.3,
    )

    low_score = planner.scorer.score_candidate(
        low_gain
    )

    high_score = planner.scorer.score_candidate(
        high_gain
    )

    assert high_score > low_score

def test_day10_testing_cost_affects_candidate_score():
    planner = AdaptivePlanner()

    low_cost = CandidateMetadata(
        test_name="tool_access_test",
        relevance=0.8,
        severity=0.8,
        confidence=0.8,
        expected_information_gain=0.8,
        testing_cost=0.2,
    )

    high_cost = CandidateMetadata(
        test_name="memory_access_test",
        relevance=0.8,
        severity=0.8,
        confidence=0.8,
        expected_information_gain=0.8,
        testing_cost=0.8,
    )

    low_cost_score = planner.scorer.score_candidate(
        low_cost
    )

    high_cost_score = planner.scorer.score_candidate(
        high_cost
    )

    assert low_cost_score > high_cost_score


def test_build_candidates_respects_prerequisite_dependencies():
    planner = AdaptivePlanner()

    planner_input = PlannerInput(
        findings=[],
        previous_tests=[],
        available_tests=[
            "permission_test",
            "tool_access_test",
            "memory_access_test",
        ],
    )

    candidates = planner.build_candidates(
        planner_input
    )

    candidate_names = [
        candidate.test_name
        for candidate in candidates
    ]

    assert candidate_names == [
        "permission_test"
    ]


def test_build_candidates_allows_tool_after_permission():
    planner = AdaptivePlanner()

    planner_input = PlannerInput(
        findings=[],
        previous_tests=[
            "permission_test"
        ],
        available_tests=[
            "permission_test",
            "tool_access_test",
            "memory_access_test",
        ],
    )

    candidates = planner.build_candidates(
        planner_input
    )

    candidate_names = [
        candidate.test_name
        for candidate in candidates
    ]

    assert candidate_names == [
        "tool_access_test"
    ]


def test_build_candidates_allows_memory_after_tool():
    planner = AdaptivePlanner()

    planner_input = PlannerInput(
        findings=[],
        previous_tests=[
            "permission_test",
            "tool_access_test",
        ],
        available_tests=[
            "permission_test",
            "tool_access_test",
            "memory_access_test",
        ],
    )

    candidates = planner.build_candidates(
        planner_input
    )

    candidate_names = [
        candidate.test_name
        for candidate in candidates
    ]

    assert candidate_names == [
        "memory_access_test"
    ]