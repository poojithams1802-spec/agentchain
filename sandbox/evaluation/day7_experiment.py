import sys

sys.path.insert(0, "ai-engine")

from adaptive_loop import AdaptiveLoop
from planner import AdaptivePlanner
from schemas import PlannerInput

from .day7_static_run import run_day7_static_experiment
from .day7_adaptive_run import run_day7_adaptive_experiment
from .day7_comparison import compare_day7_runs


DAY7_TESTS = [
    "permission_test",
    "tool_access_test",
    "memory_access_test",
]


def run_day7_experiment(
    adaptive_responses,
    static_experiment_id="day7-static-final-001",
    adaptive_experiment_id="day7-adaptive-final-001",
):
    """
    Run the complete Day 7 controlled static-vs-adaptive experiment.

    The adaptive responses are supplied externally so the experiment
    remains deterministic and reproducible.
    """

    if not isinstance(adaptive_responses, list):
        raise ValueError(
            "adaptive_responses must be a list."
        )

    if len(adaptive_responses) != 3:
        raise ValueError(
            "Day 7 requires exactly 3 adaptive responses."
        )

    # --------------------------------------------------
    # Static
    # --------------------------------------------------

    static_result = run_day7_static_experiment(
        static_experiment_id
    )

    if static_result["status"] != "completed":
        return {
            "status": "failed",
            "stage": "static",
            "error": static_result.get("error"),
        }

    # --------------------------------------------------
    # Adaptive
    # --------------------------------------------------

    planner = AdaptivePlanner()

    response_index = {
        "value": 0
    }

    def fake_generate_json(prompt):
        index = response_index["value"]

        if index >= len(adaptive_responses):
            raise RuntimeError(
                "Adaptive response sequence exhausted."
            )

        response = adaptive_responses[index]
        response_index["value"] += 1

        return response

    planner.llm_client.generate_json = (
        fake_generate_json
    )

    planner_input = PlannerInput(
        findings=[],
        previous_tests=[],
        available_tests=DAY7_TESTS.copy(),
    )

    adaptive_loop = AdaptiveLoop(
        planner=planner
    )

    adaptive_result = run_day7_adaptive_experiment(
        adaptive_loop=adaptive_loop,
        planner_input=planner_input,
        experiment_id=adaptive_experiment_id,
    )

    if adaptive_result["status"] != "completed":
        return {
            "status": "failed",
            "stage": "adaptive",
            "error": adaptive_result.get("error"),
        }

    # --------------------------------------------------
    # Comparison
    # --------------------------------------------------

    comparison = compare_day7_runs(
        static_result,
        adaptive_result,
    )

    if comparison["status"] != "completed":
        return {
            "status": "failed",
            "stage": "comparison",
            "error": comparison.get("error"),
        }

    return {
        "status": "completed",
        "study": "phase3_day7_static_vs_adaptive",
        "static_result": static_result,
        "adaptive_result": adaptive_result,
        "comparison": comparison,
    }