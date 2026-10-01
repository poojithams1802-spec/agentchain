import unittest

from ..evaluation.phase2_metrics import (
    calculate_phase2_metrics,
)


class TestPhase2Metrics(unittest.TestCase):

    def setUp(self):
        self.results = [
            # --------------------------------------------------
            # Rule-based
            # --------------------------------------------------

            {
                "condition": "rule_based_fixed_mitigation",
                "selection_correct": True,
                "mitigation_control": "authorization_gate",
                "mitigation_applied": True,
                "attack_success_before": True,
                "attack_success_after": False,
                "chain_disrupted": True,
                "mitigation_validation": True,
                "residual_vulnerable_steps": [],
                "llm_calls": 0,
            },
            {
                "condition": "rule_based_fixed_mitigation",
                "selection_correct": True,
                "mitigation_control": "tool_allowlist",
                "mitigation_applied": True,
                "attack_success_before": True,
                "attack_success_after": False,
                "chain_disrupted": True,
                "mitigation_validation": True,
                "residual_vulnerable_steps": [],
                "llm_calls": 0,
            },

            # --------------------------------------------------
            # LLM recommendation only
            # --------------------------------------------------

            {
                "condition": "llm_recommendation_only",
                "selection_correct": True,
                "mitigation_control": "authorization_gate",
                "mitigation_applied": False,
                "attack_success_before": None,
                "attack_success_after": None,
                "chain_disrupted": False,
                "mitigation_validation": False,
                "residual_vulnerable_steps": [],
                "llm_calls": 1,
            },

            # --------------------------------------------------
            # Level 3
            # --------------------------------------------------

            {
                "condition": "level3_proposed",
                "selection_correct": True,
                "mitigation_control": "authorization_gate",
                "mitigation_applied": True,
                "attack_success_before": True,
                "attack_success_after": False,
                "chain_disrupted": True,
                "mitigation_validation": True,
                "residual_vulnerable_steps": [],
                "llm_calls": 1,
            },

            # --------------------------------------------------
            # Wrong control
            # --------------------------------------------------

            {
                "condition": "wrong_control",
                "selection_correct": False,
                "mitigation_control": "tool_allowlist",
                "mitigation_applied": True,
                "attack_success_before": True,
                "attack_success_after": True,
                "chain_disrupted": False,
                "mitigation_validation": False,
                "residual_vulnerable_steps": [
                    "permission_test"
                ],
                "llm_calls": 1,
            },
        ]

    # ------------------------------------------------------
    # Grouping
    # ------------------------------------------------------

    def test_metrics_are_grouped_by_condition(self):
        metrics = calculate_phase2_metrics(
            self.results
        )

        self.assertIn(
            "rule_based_fixed_mitigation",
            metrics
        )

        self.assertIn(
            "llm_recommendation_only",
            metrics
        )

        self.assertIn(
            "level3_proposed",
            metrics
        )

        self.assertIn(
            "wrong_control",
            metrics
        )

    # ------------------------------------------------------
    # Rule-based metrics
    # ------------------------------------------------------

    def test_rule_based_metrics(self):
        metrics = calculate_phase2_metrics(
            self.results
        )

        result = metrics[
            "rule_based_fixed_mitigation"
        ]

        self.assertEqual(
            result["experiment_count"],
            2
        )

        self.assertEqual(
            result["mitigation_selection_accuracy"],
            1.0
        )

        self.assertEqual(
            result["mitigation_application_success"],
            1.0
        )

        self.assertEqual(
            result["attack_success_rate_before"],
            1.0
        )

        self.assertEqual(
            result["attack_success_rate_after"],
            0.0
        )

        self.assertEqual(
            result["chain_disruption_rate"],
            1.0
        )

        self.assertEqual(
            result["mitigation_validation_rate"],
            1.0
        )

    # ------------------------------------------------------
    # LLM recommendation-only metrics
    # ------------------------------------------------------

    def test_llm_recommendation_only_metrics(self):
        metrics = calculate_phase2_metrics(
            self.results
        )

        result = metrics[
            "llm_recommendation_only"
        ]

        self.assertEqual(
            result["experiment_count"],
            1
        )

        self.assertEqual(
            result["mitigation_selection_accuracy"],
            1.0
        )

        self.assertIsNone(
            result["mitigation_application_success"]
        )

        self.assertIsNone(
            result["attack_success_rate_before"]
        )

        self.assertIsNone(
            result["attack_success_rate_after"]
        )

        self.assertIsNone(
            result["chain_disruption_rate"]
        )

        self.assertIsNone(
            result["mitigation_validation_rate"]
        )

        self.assertEqual(
            result["llm_calls"],
            1
        )

    # ------------------------------------------------------
    # Level-3 metrics
    # ------------------------------------------------------

    def test_level3_metrics(self):
        metrics = calculate_phase2_metrics(
            self.results
        )

        result = metrics[
            "level3_proposed"
        ]

        self.assertEqual(
            result["mitigation_application_success"],
            1.0
        )

        self.assertEqual(
            result["attack_success_rate_before"],
            1.0
        )

        self.assertEqual(
            result["attack_success_rate_after"],
            0.0
        )

        self.assertEqual(
            result["chain_disruption_rate"],
            1.0
        )

        self.assertEqual(
            result["mitigation_validation_rate"],
            1.0
        )

    # ------------------------------------------------------
    # Wrong-control metrics
    # ------------------------------------------------------

    def test_wrong_control_metrics(self):
        metrics = calculate_phase2_metrics(
            self.results
        )

        result = metrics[
            "wrong_control"
        ]

        self.assertEqual(
            result["mitigation_selection_accuracy"],
            0.0
        )

        self.assertEqual(
            result["mitigation_application_success"],
            1.0
        )

        self.assertEqual(
            result["attack_success_rate_before"],
            1.0
        )

        self.assertEqual(
            result["attack_success_rate_after"],
            1.0
        )

        self.assertEqual(
            result["chain_disruption_rate"],
            0.0
        )

        self.assertEqual(
            result["mitigation_validation_rate"],
            0.0
        )

        self.assertEqual(
            result["residual_vulnerable_steps"],
            [
                "permission_test"
            ]
        )

    # ------------------------------------------------------
    # Invalid condition
    # ------------------------------------------------------

    def test_unknown_condition_is_rejected(self):
        invalid_results = [
            {
                "condition": "unknown_condition"
            }
        ]

        with self.assertRaises(ValueError):
            calculate_phase2_metrics(
                invalid_results
            )

    # ------------------------------------------------------
    # Invalid input
    # ------------------------------------------------------

    def test_invalid_input_is_rejected(self):
        with self.assertRaises(ValueError):
            calculate_phase2_metrics(
                {}
            )


if __name__ == "__main__":
    unittest.main()