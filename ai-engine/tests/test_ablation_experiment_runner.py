from __future__ import annotations

import os
os.environ.setdefault("GEMINI_API_KEY", "test-key")

import sys
from pathlib import Path

AI_ENGINE_DIR = Path(__file__).resolve().parents[1]
if str(AI_ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(AI_ENGINE_DIR))

from ablation_experiment_runner import AblationExperimentRunner
from planner import AdaptivePlanner
from schemas import PlannerDecision, PlannerInput


class FakePlanner:
    def __init__(self):
        self.calls = []

    @staticmethod
    def budget_exhausted(state):
        return (
            state.budget_used.tests >= state.testing_budget.max_tests
            or state.budget_used.llm_calls >= state.testing_budget.max_llm_calls
            or state.budget_used.time_seconds
            >= state.testing_budget.max_time_seconds
        )

    @staticmethod
    def remaining_budget(state):
        return {
            "tests": max(
                0,
                state.testing_budget.max_tests
                - state.budget_used.tests,
            ),
            "llm_calls": max(
                0,
                state.testing_budget.max_llm_calls
                - state.budget_used.llm_calls,
            ),
            "time_seconds": max(
                0.0,
                state.testing_budget.max_time_seconds
                - state.budget_used.time_seconds,
            ),
        }

    def plan(self, state, configuration=None):
        config_id = configuration.config_id
        self.calls.append(config_id)

        choices = {
            "A": ["permission_test", "tool_access_test"],
            "B": ["tool_access_test", "memory_access_test"],
            "C": ["memory_access_test", "permission_test"],
            "D": ["permission_test", "memory_access_test"],
        }

        index = len(state.previous_tests)
        selected = choices[config_id][index]

        state.budget_used.llm_calls += 1

        return PlannerDecision(
            selected_test=selected,
            reason=f"Controlled decision for configuration {config_id}.",
            priority=0.9,
            confidence=0.9,
        )


def make_input():
    return PlannerInput(
        available_tests=[
            "permission_test",
            "tool_access_test",
            "memory_access_test",
        ]
    )


def fake_execute(decision, experiment_id):
    findings = {
        "permission_test": (
            "weak_permission_control",
            "high",
        ),
        "tool_access_test": (
            "unsafe_tool_access",
            "high",
        ),
        "memory_access_test": (
            "memory_validation_weakness",
            "medium",
        ),
    }

    finding, severity = findings[decision.selected_test]

    return {
        "status": "completed",
        "test": decision.selected_test,
        "finding": finding,
        "severity": severity,
        "evidence": f"Controlled result for {decision.selected_test}.",
        "confidence": 1.0,
    }


def test_run_configuration_executes_selected_tests_and_records_metrics():
    planner = FakePlanner()
    runner = AblationExperimentRunner(
        planner=planner,
        executor=fake_execute,
    )

    result = runner.run_configuration(
        planner_input=make_input(),
        configuration="B",
        experiment_id="P2-AB-B",
        max_tests=2,
        expected_test_sequence=[
            "tool_access_test",
            "memory_access_test",
        ],
    )

    assert result["configuration"]["config_id"] == "B"
    assert result["experiment_id"] == "P2-AB-B"
    assert result["runner_scope"] == "planner_plus_sandbox"
    assert result["selected_tests"] == [
        "tool_access_test",
        "memory_access_test",
    ]
    assert result["tests_required"] == 2
    assert len(result["findings"]) == 2
    assert result["execution_success_rate"] == 1.0
    assert result["selection_accuracy"] == 1.0
    assert result["llm_calls"] == 2
    assert result["budget_used"]["tests"] == 2


def test_suite_uses_same_initial_state_for_all_four_configurations():
    planner = FakePlanner()
    runner = AblationExperimentRunner(
        planner=planner,
        executor=fake_execute,
    )

    initial = make_input()

    result = runner.run_suite(
        planner_input=initial,
        experiment_ids={
            "A": "P2-AB-A",
            "B": "P2-AB-B",
            "C": "P2-AB-C",
            "D": "P2-AB-D",
        },
        max_tests=2,
    )

    assert result["same_initial_state"] is True
    assert result["configuration_order"] == [
        "A",
        "B",
        "C",
        "D",
    ]
    assert len(result["results"]) == 4
    assert [
        item["configuration"]["config_id"]
        for item in result["results"]
    ] == ["A", "B", "C", "D"]

    # Caller state must not be mutated by the suite.
    assert initial.previous_tests == []
    assert initial.findings == []
    assert initial.budget_used.tests == 0
    assert initial.budget_used.llm_calls == 0


def test_missing_experiment_id_is_rejected():
    runner = AblationExperimentRunner(
        planner=FakePlanner(),
        executor=fake_execute,
    )

    try:
        runner.run_suite(
            planner_input=make_input(),
            experiment_ids={
                "A": "P2-AB-A",
                "B": "P2-AB-B",
                "C": "P2-AB-C",
            },
            max_tests=1,
        )
    except ValueError as error:
        assert "Missing experiment IDs" in str(error)
    else:
        raise AssertionError(
            "Expected missing experiment ID validation error."
        )


def test_execution_failure_is_recorded_without_corrupting_the_run():
    planner = FakePlanner()

    def failing_executor(decision, experiment_id):
        if decision.selected_test == "permission_test":
            raise RuntimeError("controlled sandbox failure")

        return fake_execute(
            decision,
            experiment_id,
        )

    runner = AblationExperimentRunner(
        planner=planner,
        executor=failing_executor,
    )

    result = runner.run_configuration(
        planner_input=make_input(),
        configuration="A",
        experiment_id="P2-AB-A",
        max_tests=2,
    )

    assert result["tests_required"] == 2
    assert result["selected_tests"] == [
        "permission_test",
        "tool_access_test",
    ]
    assert len(result["findings"]) == 1
    assert len(result["errors"]) == 1
    assert result["execution_records"][0]["status"] == "failed"
    assert result["execution_records"][1]["status"] == "completed"


def test_real_planner_can_be_used_with_a_deterministic_plan_method(monkeypatch):
    planner = AdaptivePlanner()

    def fake_plan(state, configuration=None):
        state.budget_used.llm_calls += 1
        return PlannerDecision(
            selected_test=state.available_tests[
                len(state.previous_tests)
            ],
            reason="Deterministic Day 12 test decision.",
            priority=0.8,
            confidence=1.0,
        )

    monkeypatch.setattr(
        planner,
        "plan",
        fake_plan,
    )

    runner = AblationExperimentRunner(
        planner=planner,
        executor=fake_execute,
    )

    result = runner.run_configuration(
        planner_input=make_input(),
        configuration="D",
        experiment_id="P2-AB-D",
        max_tests=2,
    )

    assert result["configuration"]["config_id"] == "D"
    assert result["tests_selected"] == 2
    assert result["llm_calls"] == 2
