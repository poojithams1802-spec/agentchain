import sys
from pathlib import Path

import pytest

AI_ENGINE_DIR = Path(__file__).resolve().parents[1]

if str(AI_ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(AI_ENGINE_DIR))

from adaptive_loop import AdaptiveLoop
from schemas import (
    PlannerDecision,
    PlannerInput,
    TestingBudget as Budget,
)


class FakePlanner:
    def __init__(self):
        self.calls = []

    def plan(self, planner_input):
        self.calls.append(
            {
                "previous_tests": list(planner_input.previous_tests),
                "findings": list(planner_input.findings),
            }
        )

        if not planner_input.previous_tests:
            return PlannerDecision(
                selected_test="permission_test",
                reason="Start with permission testing.",
                priority=0.9,
                confidence=0.9,
            )

        return PlannerDecision(
            selected_test="tool_access_test",
            reason="Fallback: use the next approved test.",
            priority=0.8,
            confidence=0.8,
        )


def test_run_detailed_exposes_adaptive_evaluation_data(monkeypatch):
    planner = FakePlanner()

    def fake_execute(decision, experiment_id):
        return {
            "status": "completed",
            "test": decision.selected_test,
            "finding": f"finding_for_{decision.selected_test}",
            "severity": "high",
            "evidence": "controlled evidence",
            "confidence": 1.0,
            "execution_cost": {
                "time_seconds": 0.12,
                "operations": 2,
            },
        }

    monkeypatch.setattr("adaptive_loop.execute_planned_test", fake_execute)

    planner_input = PlannerInput(
        available_tests=[
            "permission_test",
            "tool_access_test",
        ]
    )

    loop = AdaptiveLoop(planner=planner)

    result = loop.run_detailed(
        planner_input=planner_input,
        experiment_id="day7-detailed",
        max_tests=2,
    )

    assert result["status"] == "completed"
    assert result["experiment_id"] == "day7-detailed"
    assert result["tests_used"] == 2

    assert result["selected_tests"] == [
        "permission_test",
        "tool_access_test",
    ]

    assert len(result["decisions"]) == 2
    assert result["decisions"][0]["selected_test"] == "permission_test"
    assert result["decisions"][1]["reason"].startswith("Fallback")

    assert len(result["execution_results"]) == 2
    assert (
        result["execution_results"][0]["execution_cost"]["time_seconds"]
        == 0.12
    )

    assert len(result["findings"]) == 2
    assert result["findings"][0].finding == "finding_for_permission_test"

    assert result["fallback_used"] is True


def test_run_remains_backward_compatible(monkeypatch):
    planner = FakePlanner()

    def fake_execute(decision, experiment_id):
        return {
            "status": "completed",
            "test": decision.selected_test,
            "finding": "permission finding",
            "severity": "high",
            "evidence": "evidence",
            "confidence": 1.0,
        }

    monkeypatch.setattr("adaptive_loop.execute_planned_test", fake_execute)

    planner_input = PlannerInput(
        available_tests=["permission_test"]
    )

    loop = AdaptiveLoop(planner=planner)

    findings = loop.run(
        planner_input=planner_input,
        experiment_id="day7-compat",
        max_tests=1,
    )

    assert len(findings) == 1
    assert findings[0].finding == "permission finding"


def test_run_detailed_preserves_failed_execution_without_finding(monkeypatch):
    planner = FakePlanner()

    def fake_execute(decision, experiment_id):
        return {
            "status": "failed",
            "test": decision.selected_test,
            "finding": None,
            "severity": None,
            "evidence": "controlled execution failed",
            "confidence": 0.0,
            "execution_cost": {
                "time_seconds": 0.05,
            },
        }

    monkeypatch.setattr("adaptive_loop.execute_planned_test", fake_execute)

    planner_input = PlannerInput(
        available_tests=["permission_test"]
    )

    loop = AdaptiveLoop(planner=planner)

    result = loop.run_detailed(
        planner_input=planner_input,
        experiment_id="day7-failed",
        max_tests=1,
    )

    assert result["tests_used"] == 1
    assert result["selected_tests"] == ["permission_test"]
    assert result["findings"] == []
    assert result["execution_results"][0]["status"] == "failed"
    assert result["execution_results"][0]["execution_cost"]["time_seconds"] == 0.05


def test_run_detailed_counts_failed_attempts_and_elapsed_time(monkeypatch):
    clock = [0.0]

    class SequencePlanner:
        def plan(self, planner_input):
            clock[0] += 0.01
            selected_test = (
                "permission_test"
                if not planner_input.previous_tests
                else "tool_access_test"
            )
            return PlannerDecision(
                selected_test=selected_test,
                reason="Select next test.",
                priority=0.9,
                confidence=0.9,
            )

    def execute_with_elapsed_time(decision, experiment_id):
        clock[0] += 0.03
        if decision.selected_test == "permission_test":
            return {
                "status": "failed",
                "test": decision.selected_test,
                "finding": None,
                "severity": None,
                "evidence": "controlled execution failed",
                "confidence": 0.0,
            }
        return {
            "status": "completed",
            "test": decision.selected_test,
            "finding": "unsafe_tool_access",
            "severity": "high",
            "evidence": "controlled evidence",
            "confidence": 1.0,
        }

    monkeypatch.setattr("adaptive_loop.perf_counter", lambda: clock[0])
    monkeypatch.setattr(
        "adaptive_loop.execute_planned_test",
        execute_with_elapsed_time,
    )

    planner_input = PlannerInput(
        available_tests=["permission_test", "tool_access_test"],
        testing_budget=Budget(
            max_tests=1,
            max_llm_calls=3,
            max_time_seconds=1.0,
        ),
    )
    result = AdaptiveLoop(planner=SequencePlanner()).run_detailed(
        planner_input=planner_input,
        experiment_id="failed-attempt-budget",
        max_tests=3,
    )

    assert result["tests_used"] == 1
    assert result["selected_tests"] == ["permission_test"]
    assert result["budget_used"]["tests"] == 1
    assert result["budget_used"]["time_seconds"] == pytest.approx(0.04)
    assert [item["status"] for item in result["execution_results"]] == ["failed"]
    assert result["findings"] == []


@pytest.mark.parametrize(
    ("planning_duration", "execution_duration", "expected_attempts"),
    [
        (0.11, 0.0, 0),
        (0.02, 0.09, 1),
    ],
)
def test_run_detailed_stops_starting_sandbox_when_time_budget_exhausted(
    monkeypatch,
    planning_duration,
    execution_duration,
    expected_attempts,
):
    clock = [0.0]
    sandbox_calls = []

    class TimedPlanner:
        def plan(self, planner_input):
            clock[0] += planning_duration
            return PlannerDecision(
                selected_test="permission_test",
                reason="Select permission test.",
                priority=0.9,
                confidence=0.9,
            )

    def execute_test(decision, experiment_id):
        sandbox_calls.append(decision.selected_test)
        clock[0] += execution_duration
        return {
            "status": "completed",
            "test": decision.selected_test,
            "finding": "weak_permission_control",
            "severity": "high",
            "evidence": "controlled evidence",
            "confidence": 1.0,
        }

    monkeypatch.setattr("adaptive_loop.perf_counter", lambda: clock[0])
    monkeypatch.setattr(
        "adaptive_loop.execute_planned_test",
        execute_test,
    )

    planner_input = PlannerInput(
        available_tests=["permission_test", "tool_access_test"],
        testing_budget=Budget(
            max_tests=3,
            max_llm_calls=3,
            max_time_seconds=0.1,
        ),
    )
    result = AdaptiveLoop(planner=TimedPlanner()).run_detailed(
        planner_input=planner_input,
        experiment_id="time-budget-exhausted",
        max_tests=3,
    )

    assert len(sandbox_calls) == expected_attempts
    assert result["selected_tests"] == ["permission_test"]
    assert result["tests_used"] == expected_attempts
    assert len(result["execution_results"]) == expected_attempts
    assert result["budget_used"]["tests"] == expected_attempts
    assert result["budget_used"]["time_seconds"] == pytest.approx(
        planning_duration + (execution_duration if expected_attempts else 0.0)
    )