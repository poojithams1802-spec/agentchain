import unittest

from sandbox.evaluation.day12_dataset import build_day12_dataset
from sandbox.evaluation.research_metrics import calculate_research_metrics


class TestResearchMetrics(unittest.TestCase):

    def test_research_metrics(self):

        dataset = build_day12_dataset()

        metrics = calculate_research_metrics(dataset)

        # --------------------------------------------------
        # Static
        # --------------------------------------------------

        self.assertEqual(
            metrics["static"]["experiments"],
            1
        )

        self.assertEqual(
            metrics["static"]["total_tests"],
            3
        )

        self.assertEqual(
            metrics["static"]["total_findings"],
            3
        )

        self.assertEqual(
            metrics["static"]["valid_findings"],
            3
        )

        self.assertEqual(
            metrics["static"]["candidate_chains"],
            1
        )

        self.assertEqual(
            metrics["static"]["validated_chains"],
            1
        )

        self.assertEqual(
            metrics["static"]["average_chain_length"],
            3.0
        )

        self.assertEqual(
            metrics["static"]["validation_rate"],
            1.0
        )

        self.assertEqual(
            metrics["static"]["execution_count"],
            3
        )

        self.assertEqual(
            metrics["static"]["llm_calls"],
            0
        )

        # --------------------------------------------------
        # Adaptive
        # --------------------------------------------------

        self.assertEqual(
            metrics["adaptive"]["experiments"],
            3
        )

        self.assertEqual(
            metrics["adaptive"]["total_tests"],
            9
        )

        self.assertEqual(
            metrics["adaptive"]["total_findings"],
            9
        )

        self.assertEqual(
            metrics["adaptive"]["valid_findings"],
            9
        )

        self.assertEqual(
            metrics["adaptive"]["candidate_chains"],
            3
        )

        self.assertEqual(
            metrics["adaptive"]["validated_chains"],
            2
        )

        self.assertEqual(
            metrics["adaptive"]["average_chain_length"],
            3.0
        )

        expected_validation_rate = (
            1.0 + 0.3333 + 1.0
        ) / 3

        self.assertAlmostEqual(
            metrics["adaptive"]["validation_rate"],
            expected_validation_rate,
            places=4
        )

        self.assertEqual(
            metrics["adaptive"]["execution_count"],
            9
        )

        self.assertEqual(
            metrics["adaptive"]["llm_calls"],
            0
        )
        def test_phase2_mitigation_metrics(self):

            dataset = {
                "experiments": [
                    {
                        "experiment_id": "EXP-P2-001",
                        "mode": "adaptive",
                        "executed_tests": [
                            "permission_test"
                        ],
                        "findings": [
                            "weak_permission_control"
                        ],
                        "candidate_chains": [
                            "CHAIN-001"
                        ],
                        "validated_chains": [
                            "CHAIN-001"
                        ],
                        "average_chain_length": 1.0,
                        "validation_rate": 1.0,
                        "execution_count": 1,
                        "llm_calls": 1,

                        "mitigation_control":
                            "authorization_gate",
                        "mitigation_selected": True,
                        "mitigation_applied": True,
                        "attack_success_before": True,
                        "attack_success_after": False,
                        "chain_disrupted": True,
                        "residual_vulnerable_steps": [],
                        "mitigation_validation": True
                    }
                ]
            }

            metrics = calculate_research_metrics(dataset)

            adaptive = metrics["adaptive"]

            self.assertEqual(
                adaptive["mitigation_selections"],
                1
            )

            self.assertEqual(
                adaptive["successful_mitigation_applications"],
                1
            )

            self.assertEqual(
                adaptive["attack_success_before"],
                1
            )

            self.assertEqual(
                adaptive["attack_success_after"],
                0
            )

            self.assertEqual(
                adaptive["disrupted_chains"],
                1
            )

            self.assertEqual(
                adaptive["mitigation_validations"],
                1
            )

            self.assertEqual(
                adaptive["residual_vulnerable_steps"],
                0
            )

            self.assertEqual(
                adaptive["mitigation_selection_accuracy"],
                1.0
            )

            self.assertEqual(
                adaptive["mitigation_application_success"],
                1.0
            )

            self.assertEqual(
                adaptive["attack_success_rate_before"],
                1.0
            )

            self.assertEqual(
                adaptive["attack_success_rate_after"],
                0.0
            )

            self.assertEqual(
                adaptive["chain_disruption_rate"],
                1.0
            )

            self.assertEqual(
                adaptive["mitigation_validation_rate"],
                1.0
            )

if __name__ == "__main__":
    unittest.main()