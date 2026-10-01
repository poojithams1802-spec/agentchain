import unittest

from sandbox.mitigation.replay_executor import replay_attack
from sandbox.evaluation.mitigation_evaluation import (
    build_mitigation_experiment_record
)
from sandbox.evaluation.research_metrics import (
    calculate_research_metrics
)


class TestPhase2MitigationEvaluation(unittest.TestCase):

    MITIGATION_CASES = [
        (
            "permission_test",
            "authorization_gate"
        ),
        (
            "tool_access_test",
            "tool_allowlist"
        ),
        (
            "memory_access_test",
            "memory_validation"
        )
    ]

    def test_all_predefined_mitigations(self):

        records = []

        for index, (test_name, control_name) in enumerate(
            self.MITIGATION_CASES,
            start=1
        ):

            experiment_id = (
                f"DAY5-AUTO-{index}"
            )

            replay_result = replay_attack(
                experiment_id,
                test_name,
                control_name
            )

            self.assertEqual(
                replay_result["status"],
                "completed"
            )

            self.assertTrue(
                replay_result["before_validation"]["valid"]
            )

            self.assertTrue(
                replay_result["after_validation"]["valid"]
            )

            self.assertTrue(
                replay_result["disrupted"]
            )

            self.assertEqual(
                replay_result[
                    "residual_vulnerable_steps"
                ],
                []
            )

            self.assertEqual(
                replay_result[
                    "validation_result"
                ]["status"],
                "validated"
            )

            record = (
                build_mitigation_experiment_record(
                    replay_result
                )
            )

            records.append(record)

        dataset = {
            "experiments": records
        }

        metrics = calculate_research_metrics(
            dataset
        )

        adaptive = metrics["adaptive"]

        # ----------------------------------------------
        # Experiment counts
        # ----------------------------------------------

        self.assertEqual(
            adaptive["experiments"],
            3
        )

        self.assertEqual(
            adaptive["mitigation_selections"],
            3
        )

        # ----------------------------------------------
        # Mitigation application
        # ----------------------------------------------

        self.assertEqual(
            adaptive[
                "successful_mitigation_applications"
            ],
            3
        )

        self.assertEqual(
            adaptive[
                "mitigation_application_success"
            ],
            1.0
        )

        # ----------------------------------------------
        # Before / after attack results
        # ----------------------------------------------

        self.assertEqual(
            adaptive["attack_success_before"],
            3
        )

        self.assertEqual(
            adaptive["attack_success_after"],
            0
        )

        self.assertEqual(
            adaptive[
                "attack_success_rate_before"
            ],
            1.0
        )

        self.assertEqual(
            adaptive[
                "attack_success_rate_after"
            ],
            0.0
        )

        # ----------------------------------------------
        # Chain disruption
        # ----------------------------------------------

        self.assertEqual(
            adaptive["disrupted_chains"],
            3
        )

        self.assertEqual(
            adaptive["chain_disruption_rate"],
            1.0
        )

        # ----------------------------------------------
        # Validation
        # ----------------------------------------------

        self.assertEqual(
            adaptive["mitigation_validations"],
            3
        )

        self.assertEqual(
            adaptive[
                "mitigation_validation_rate"
            ],
            1.0
        )

        # ----------------------------------------------
        # Residual vulnerable steps
        # ----------------------------------------------

        self.assertEqual(
            adaptive[
                "residual_vulnerable_steps"
            ],
            0
        )

        # ----------------------------------------------
        # Selection accuracy
        # ----------------------------------------------

        self.assertEqual(
            adaptive[
                "mitigation_selection_accuracy"
            ],
            1.0
        )


if __name__ == "__main__":
    unittest.main()