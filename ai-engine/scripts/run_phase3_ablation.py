from __future__ import annotations

import sys
from pathlib import Path
from unittest import runner

AI_ENGINE_DIR = Path(__file__).resolve().parents[1]

if str(AI_ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(AI_ENGINE_DIR))

from ablation_experiment_runner import (
    AblationExperimentRunner,
    save_ablation_result,
)
from schemas import PlannerInput, TestingBudget


def main() -> None:
    # Same initial input and candidate pool for A, B, C, and D.
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
            "chain_id": "PHASE3_GEMINI_CONTROLLED_CHAIN",
            "ordered_steps": [
                "permission_test",
                "tool_access_test",
                "memory_access_test",
            ],
            "dependencies": {
                "tool_access_test": ["permission_test"],
                "memory_access_test": ["tool_access_test"],
            },
            "validation_result": {},
        },
        testing_budget=TestingBudget(
            max_tests=3,
            max_llm_calls=4,
            max_time_seconds=30.0,
        ),
    )

    # Local research IDs only. P2 supplies IDs for production integration.
    experiment_ids = {
        "A": "GEMINI-ABL-A-20261011",
        "B": "GEMINI-ABL-B-20261011",
        "C": "GEMINI-ABL-C-20261011",
        "D": "GEMINI-ABL-D-20261011",
    }

    runner = AblationExperimentRunner()

    print("=" * 65)
    print("PHASE 3 — GEMINI A/B/C/D ABLATION EXPERIMENT")
    print("=" * 65)
    print("Tests per configuration: 3")
    print("Maximum LLM calls per configuration: 4")
    print("Time budget per configuration: 30 seconds")
    print("Configurations: A, B, C, D")
    print("Output: results/phase3_ablation_gemini_20261011.json")
    print()

    # No independent ground-truth sequence has been established yet.
    expected_test_sequence = None

    result = runner.run_suite(
        planner_input=planner_input,
        experiment_ids=experiment_ids,
        max_tests=3,
        expected_test_sequence=expected_test_sequence,
    )

    output_path = save_ablation_result(
        result,
        AI_ENGINE_DIR
        / "results"
        / "phase3_ablation_gemini_20261011.json",
    )

    print("\n" + "=" * 65)
    print("EXPERIMENT SUMMARY")
    print("=" * 65)

    for experiment in result.get("results", []):
        print(f"\nConfiguration: {experiment.get('configuration')}")
        print(f"Status: {experiment.get('status')}")
        print(f"Tests selected: {experiment.get('tests_selected')}")
        print(f"LLM calls: {experiment.get('llm_calls')}")
        print(f"Fallback used: {experiment.get('fallback_used')}")
        print(f"Fallback decisions: {experiment.get('fallback_decisions')}")
        print(f"Non-fallback decisions: {experiment.get('non_fallback_decisions')}")
        print(f"Selection accuracy: {experiment.get('selection_accuracy')}")
        print(f"Execution time: {experiment.get('execution_time_seconds')}")
        print(f"Total time: {experiment.get('total_time_seconds')}")

    print("\nSaved results to:")
    print(output_path)


if __name__ == "__main__":
    main()
