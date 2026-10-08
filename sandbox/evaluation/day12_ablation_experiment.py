"""
Phase 3 Day 12 - Ablation Experiment Integration.

P4 responsibility:
- invoke the existing P3 ablation runner
- pass its output into the P4 metrics evaluator
- preserve the raw planner results
- produce a comparable evaluation record

No planner or LLM logic is implemented here.
"""

from __future__ import annotations

from typing import Any

from sandbox.evaluation.day11_ablation_scenario_runner import (
    run_day11_common_scenario,
)

from sandbox.evaluation.day12_ablation_metrics import (
    calculate_day12_ablation_metrics,
)


EXPECTED_TEST_SEQUENCE = [
    "permission_test",
    "tool_access_test",
    "memory_access_test",
]


def run_day12_ablation_experiment(
    max_steps: int = 3,
) -> dict[str, Any]:
    """
    Run the existing P3 A/B/C/D planner ablation and evaluate it.

    The same controlled scenario is used for all configurations.
    """
    raw_result = run_day11_common_scenario(
        max_steps=max_steps,
    )

    metrics_result = calculate_day12_ablation_metrics(
        raw_result,
        expected_tests=EXPECTED_TEST_SEQUENCE[:max_steps],
    )

    return {
        "study": "phase3_day12_ablation_experiments",
        "scenario_id": raw_result.get(
            "scenario_id",
            "N/A",
        ),
        "experiment_version": raw_result.get(
            "experiment_version",
            "N/A",
        ),
        "scenario_version": raw_result.get(
            "scenario_version",
            "N/A",
        ),
        "random_seed": raw_result.get(
            "random_seed",
            "N/A",
        ),
        "same_initial_state": raw_result.get(
            "same_initial_state",
            False,
        ),
        "max_steps": max_steps,

        # Preserve the raw P3 output.
        "raw_ablation_result": raw_result,

        # P4 calculated metrics.
        "metrics": metrics_result,
    }