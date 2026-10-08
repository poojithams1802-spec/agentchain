"""
Tests for the Phase 3 Day 11 common ablation scenario runner.
"""

import unittest

from sandbox.evaluation.day11_ablation_scenario_runner import (
    build_day11_ablation_inputs,
    build_day11_planner_input,
    get_day11_common_scenario,
    run_day11_common_scenario,
    validate_day11_common_scenario,
)


class FakePlanner:
    """
    Deterministic stand-in for P3's AdaptivePlanner.

    Day 11 tests the P4 scenario boundary, so we should not
    depend on an actual LLM or RAG service here.
    """

    def run_ablation_suite(
        self,
        planner_input,
        max_steps=1,
    ):
        results = []

        for config_id in ("A", "B", "C", "D"):
            results.append(
                {
                    "configuration": {
                        "config_id": config_id,
                        "name": {
                            "A": "llm_only",
                            "B": "llm_rag",
                            "C": "llm_chain",
                            "D": "llm_rag_chain",
                        }[config_id],
                    },
                    "status": "completed",
                    "runner_scope": "planner_only",
                    "tests_requested": max_steps,
                    "tests_selected": 1,
                    "selected_tests": [
                        planner_input.available_tests[0]
                    ],
                    "decisions": [],
                    "budget_used": {
                        "tests": 1,
                        "llm_calls": (
                            1
                            if config_id in ("A", "B", "C", "D")
                            else 0
                        ),
                        "time_seconds": 0.0,
                    },
                    "remaining_budget": {
                        "tests": (
                            planner_input.testing_budget.max_tests - 1
                        ),
                        "llm_calls": (
                            planner_input.testing_budget.max_llm_calls - 1
                        ),
                        "time_seconds": (
                            planner_input.testing_budget.max_time_seconds
                        ),
                    },
                }
            )

        return {
            "study": "phase3_ablation",
            "runner_scope": "planner_only",
            "same_initial_state": True,
            "configurations": results,
        }


class TestDay11AblationScenarioRunner(unittest.TestCase):

    def test_common_scenario_is_valid(self):
        scenario = get_day11_common_scenario()

        result = validate_day11_common_scenario(
            scenario
        )

        self.assertTrue(result["valid"])
        self.assertIsNone(result["error"])

    def test_planner_input_contains_common_state(self):
        scenario = get_day11_common_scenario()

        planner_input = build_day11_planner_input(
            scenario
        )

        self.assertEqual(
            planner_input.available_tests,
            [
                "permission_test",
                "tool_access_test",
                "memory_access_test",
            ],
        )

        self.assertEqual(
            planner_input.previous_tests,
            [],
        )

        self.assertEqual(
            planner_input.chain_state["chain_id"],
            "CHAIN-AUTH-TOOL-MEM",
        )

        self.assertEqual(
            planner_input.chain_state["ordered_steps"],
            planner_input.available_tests,
        )

        self.assertEqual(
            planner_input.testing_budget.max_tests,
            3,
        )

        self.assertEqual(
            planner_input.testing_budget.max_llm_calls,
            3,
        )

        self.assertEqual(
            planner_input.testing_budget.max_time_seconds,
            30.0,
        )

    def test_builds_four_independent_ablation_inputs(self):
        inputs = build_day11_ablation_inputs()

        self.assertEqual(
            len(inputs),
            4,
        )

        self.assertEqual(
            [item["config_id"] for item in inputs],
            ["A", "B", "C", "D"],
        )

        for item in inputs:
            planner_input = item["planner_input"]

            self.assertEqual(
                planner_input.available_tests,
                [
                    "permission_test",
                    "tool_access_test",
                    "memory_access_test",
                ],
            )

            self.assertEqual(
                planner_input.previous_tests,
                [],
            )

    def test_ablation_inputs_do_not_share_mutable_state(self):
        inputs = build_day11_ablation_inputs()

        first = inputs[0]["planner_input"]
        second = inputs[1]["planner_input"]

        first.previous_tests.append(
            "permission_test"
        )

        first.chain_state["test_marker"] = True

        self.assertEqual(
            second.previous_tests,
            [],
        )

        self.assertNotIn(
            "test_marker",
            second.chain_state,
        )

    def test_runner_uses_same_initial_state(self):
        fake_planner = FakePlanner()

        result = run_day11_common_scenario(
            max_steps=1,
            planner=fake_planner,
        )

        self.assertEqual(
            result["status"],
            "completed",
        )

        self.assertEqual(
            result["scenario_id"],
            "DAY11-COMMON-001",
        )

        self.assertTrue(
            result["same_initial_state"]
        )

        self.assertEqual(
            len(result["configurations"]),
            4,
        )

        self.assertEqual(
            [
                item["configuration"]["config_id"]
                for item in result["configurations"]
            ],
            ["A", "B", "C", "D"],
        )

    def test_runner_preserves_common_scenario_metadata(self):
        fake_planner = FakePlanner()

        result = run_day11_common_scenario(
            max_steps=1,
            planner=fake_planner,
        )

        self.assertEqual(
            result["experiment_version"],
            "day11-v1",
        )

        self.assertEqual(
            result["scenario_version"],
            "sandbox-v1",
        )

        self.assertEqual(
            result["random_seed"],
            42,
        )

        self.assertEqual(
            result["runner_scope"],
            "common_scenario",
        )


if __name__ == "__main__":
    unittest.main()