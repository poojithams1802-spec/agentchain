import sys

sys.path.insert(0, "ai-engine")

from adaptive_loop import AdaptiveLoop
from planner import AdaptivePlanner
from schemas import PlannerInput

from sandbox.evaluation.day7_static_run import (
    run_day7_static_experiment,
)
from sandbox.evaluation.day7_adaptive_run import (
    run_day7_adaptive_experiment,
)
from sandbox.evaluation.day7_comparison import (
    compare_day7_runs,
)


def test_day7_full_static_vs_adaptive_comparison():
    # --------------------------------------------------
    # Static controlled run
    # --------------------------------------------------
    static_result = run_day7_static_experiment(
        "day7-static-comparison-001"
    )

    assert static_result["status"] == "completed"

    # --------------------------------------------------
    # Adaptive controlled run
    # --------------------------------------------------
    planner = AdaptivePlanner()

    responses = [
        {
            "selected_test": "permission_test",
            "reason": "Check authorization weakness first.",
            "priority": 0.9,
            "confidence": 0.9,
        },
        {
            "selected_test": "tool_access_test",
            "reason": "Follow the authorization weakness into tool access.",
            "priority": 0.9,
            "confidence": 0.9,
        },
        {
            "selected_test": "memory_access_test",
            "reason": "Continue to the dependent memory-validation step.",
            "priority": 0.8,
            "confidence": 0.9,
        },
    ]

    index = {"value": 0}

    def fake_generate_json(prompt):
        response = responses[index["value"]]
        index["value"] += 1
        return response

    planner.llm_client.generate_json = fake_generate_json

    planner_input = PlannerInput(
        findings=[],
        previous_tests=[],
        available_tests=[
            "permission_test",
            "tool_access_test",
            "memory_access_test",
        ],
    )

    adaptive_loop = AdaptiveLoop(
        planner=planner
    )

    adaptive_result = run_day7_adaptive_experiment(
        adaptive_loop=adaptive_loop,
        planner_input=planner_input,
        experiment_id="day7-adaptive-comparison-001",
    )

    assert adaptive_result["status"] == "completed"

    # --------------------------------------------------
    # Compare
    # --------------------------------------------------
    comparison = compare_day7_runs(
        static_result,
        adaptive_result,
    )

    assert comparison["status"] == "completed"

    assert comparison["equal_test_budget"] is True
    assert comparison["test_budget"] == 3

    assert comparison["static"]["tests"] == 3
    assert comparison["adaptive"]["tests"] == 3

    assert comparison["static"]["findings"] == 3
    assert comparison["adaptive"]["findings"] == 3

    assert comparison["static"]["validated_chains"] == 1
    assert comparison["adaptive"]["validated_chains"] == 1

    assert comparison["static"]["llm_calls"] == 0
    assert comparison["adaptive"]["llm_calls"] == 3

    assert comparison["static"]["fallback_used"] is False
    assert comparison["adaptive"]["fallback_used"] is False

    assert (
        comparison["static"]["execution_time_seconds"]
        >= 0.0
    )

    assert (
        comparison["adaptive"]["execution_time_seconds"]
        >= 0.0
    )