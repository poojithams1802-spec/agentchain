from __future__ import annotations

import json
import sys
from pathlib import Path

AI_ENGINE_DIR = Path(__file__).resolve().parents[1]
if str(AI_ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(AI_ENGINE_DIR))

from ablation_experiment_runner import (
    AblationExperimentRunner,
    save_ablation_result,
)
from schemas import PlannerInput, TestingBudget


def main() -> None:
    """
    Run the real Day 12 A-D ablation against the controlled sandbox.

    IMPORTANT:
    In the integrated P2 flow, replace the example experiment IDs below
    with IDs supplied by P2. P3 must not generate production IDs.

    The experimental budget is explicit so that the saved result records
    the intended Phase 3 testing constraints:
        - maximum tests: 3
        - maximum LLM calls: 3
        - maximum planner/experiment time budget: 30 seconds
    """

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
            "chain_id": "PHASE3_DAY12_CONTROLLED_CHAIN",
            "ordered_steps": [
                "permission_test",
                "tool_access_test",
                "memory_access_test",
            ],
            "dependencies": {
                "tool_access_test": [
                    "permission_test"
                ],
                "memory_access_test": [
                    "tool_access_test"
                ],
            },
            "validation_result": {},
        },
        testing_budget=TestingBudget(
            max_tests=3,
            max_llm_calls=3,
            max_time_seconds=30.0,
        ),
    )

    experiment_ids = {
        # Replace these with P2-issued IDs for integrated runs.
        "A": "DAY12-ABL-A",
        "B": "DAY12-ABL-B",
        "C": "DAY12-ABL-C",
        "D": "DAY12-ABL-D",
    }

    runner = AblationExperimentRunner()

    result = runner.run_suite(
        planner_input=planner_input,
        experiment_ids=experiment_ids,
        max_tests=3,
    )

    output_path = save_ablation_result(
        result,
        AI_ENGINE_DIR / "results" / "phase3_ablation_day12.json",
    )

    print("=" * 72)
    print("PHASE 3 DAY 12 — ABLATION EXPERIMENT")
    print("=" * 72)
    print(f"Saved local result: {output_path}")

    for item in result["results"]:
        config = item["configuration"]

        print("\n" + "-" * 72)
        print(
            f"Configuration {config['config_id']}: "
            f"{config['name']}"
        )
        print(f"Status: {item['status']}")
        print(f"Selected tests: {item['selected_tests']}")
        print(f"Findings: {len(item['findings'])}")
        print(f"LLM calls: {item['llm_calls']}")
        print(
            f"Selection accuracy: "
            f"{item['selection_accuracy']}"
        )
        print(
            f"Execution success rate: "
            f"{item['execution_success_rate']}"
        )
        print(
            f"Planner time: "
            f"{item['planner_time_seconds']:.4f}s"
        )
        print(
            f"Execution time: "
            f"{item['execution_time_seconds']:.4f}s"
        )
        print(
            f"Total time: "
            f"{item['total_time_seconds']:.4f}s"
        )
        print(
            f"Budget used: "
            f"{json.dumps(item['budget_used'])}"
        )

    print("\n" + "=" * 72)
    print("Day 12 ablation run complete.")
    print("=" * 72)


if __name__ == "__main__":
    main()
