import sys

sys.path.insert(
    0,
    "ai-engine"
)

from adaptive_loop import AdaptiveLoop
from planner import AdaptivePlanner
from schemas import PlannerInput

from sandbox.evaluation.day7_adaptive_run import (
    run_day7_adaptive_experiment,
)


def test_day7_adaptive_full_pipeline():
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
            "reason": "Follow the authorization finding into tool access.",
            "priority": 0.9,
            "confidence": 0.9,
        },
        {
            "selected_test": "memory_access_test",
            "reason": "Continue to the dependent memory validation step.",
            "priority": 0.8,
            "confidence": 0.9,
        },
    ]

    response_index = {"value": 0}

    def fake_generate_json(prompt):
        index = response_index["value"]

        response_index["value"] += 1

        return responses[index]

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

    result = run_day7_adaptive_experiment(
        adaptive_loop=adaptive_loop,
        planner_input=planner_input,
        experiment_id="day7-adaptive-e2e-001",
    )

    assert result["status"] == "completed"
    assert result["strategy"] == "adaptive"

    assert result["test_budget"] == 3

    assert result["evaluation"]["total_tests"] == 3
    assert result["evaluation"]["total_findings"] == 3

    assert result["evaluation"]["execution_cost"]["test_count"] == 3

    assert result["llm_calls"] == 3
    assert result["fallback_used"] is False

    assert result["validation"]["status"] == "validated"
    assert result["validation"]["validated_steps"] == 3