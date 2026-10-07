from sandbox.evaluation.day7_adaptive_run import (
    run_day7_adaptive_experiment,
)
from sandbox.evaluation.day7_controlled_experiment import (
    get_day7_experiment,
)
from types import SimpleNamespace


class FakeAdaptiveLoop:
    def run_detailed(
        self,
        planner_input,
        experiment_id,
        max_tests,
    ):
        assert max_tests == 3
        assert planner_input.testing_budget.max_tests == 3

        return {
            "status": "completed",
            "experiment_id": experiment_id,
            "tests_used": 3,
            "selected_tests": [
                "permission_test",
                "tool_access_test",
                "memory_access_test",
            ],
            "decisions": [],
            "execution_results": [
                {
                    "status": "completed",
                    "test": "permission_test",
                    "finding": "weak_permission_control",
                    "severity": "high",
                    "evidence": {},
                    "confidence": 1.0,
                    "execution_cost": {
                        "test_count": 1,
                        "execution_time_seconds": 0.00001,
                    },
                },
                {
                    "status": "completed",
                    "test": "tool_access_test",
                    "finding": "unsafe_tool_access",
                    "severity": "high",
                    "evidence": {},
                    "confidence": 1.0,
                    "execution_cost": {
                        "test_count": 1,
                        "execution_time_seconds": 0.00001,
                    },
                },
                {
                    "status": "completed",
                    "test": "memory_access_test",
                    "finding": "memory_validation_weakness",
                    "severity": "medium",
                    "evidence": {},
                    "confidence": 1.0,
                    "execution_cost": {
                        "test_count": 1,
                        "execution_time_seconds": 0.00001,
                    },
                },
            ],
            "findings": [
                "weak_permission_control",
                "unsafe_tool_access",
                "memory_validation_weakness",
            ],
            "llm_calls_used": 3,
            "llm_calls": 3,
            "fallback_used": False,
            "budget_used": {
                "tests": 3,
                "llm_calls": 3,
                "time_seconds": 0.0,
            },
            "budget_used_delta": {
                "tests": 3,
                "llm_calls": 3,
            },
        }


def test_day7_controlled_adaptive_runner():
    config = get_day7_experiment()

    planner_input = SimpleNamespace(
        testing_budget=SimpleNamespace(
            max_tests=5,
            max_llm_calls=3,
            max_time_seconds=30.0,
        )
    )

    result = run_day7_adaptive_experiment(
        adaptive_loop=FakeAdaptiveLoop(),
        planner_input=planner_input,
        experiment_id="day7-adaptive-controlled-test",
    )

    assert result["status"] == "completed"
    assert result["strategy"] == "adaptive"
    assert result["test_budget"] == config["test_budget"]["adaptive"]
    assert result["evaluation"]["total_tests"] == 3
    assert result["llm_calls"] == 3
    assert result["fallback_used"] is False


def test_day7_runner_does_not_change_equal_budget():
    config = get_day7_experiment()

    planner_input = SimpleNamespace(
        testing_budget=SimpleNamespace(
            max_tests=99,
            max_llm_calls=3,
            max_time_seconds=30.0,
        )
    )

    run_day7_adaptive_experiment(
        adaptive_loop=FakeAdaptiveLoop(),
        planner_input=planner_input,
        experiment_id="day7-budget-test",
    )

    assert planner_input.testing_budget.max_tests == 3
    assert (
        planner_input.testing_budget.max_tests
        == config["test_budget"]["adaptive"]
    )