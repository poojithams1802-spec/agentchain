import unittest

from sandbox.evaluation.adaptive_evaluation import (
    run_adaptive_evaluation
)


class TestAdaptiveEvaluation(unittest.TestCase):

    def test_adaptive_evaluation(self):

        result = run_adaptive_evaluation(
            experiment_id="ADAPTIVE_TEST",
            executed_tests=[
                "permission_test",
                "tool_access_test"
            ],
            findings=[
                "weak_permission_control",
                "unsafe_tool_access"
            ],
            candidate_chains=[
                "CHAIN_001"
            ],
            validated_chains=[
                "CHAIN_001"
            ],
            chain_lengths=[
                2
            ],
            validation_rates=[
                1.0
            ]
        )

        self.assertEqual(
            result["status"],
            "completed"
        )

        self.assertEqual(
            result["evaluation"]["mode"],
            "adaptive"
        )

        self.assertEqual(
            result["evaluation"]["total_tests"],
            2
        )

        self.assertEqual(
            result["evaluation"]["total_findings"],
            2
        )

        self.assertEqual(
            result["evaluation"]["candidate_chains"],
            1
        )

        self.assertEqual(
            result["evaluation"]["validated_chains"],
            1
        )

        self.assertEqual(
            result["evaluation"]["average_chain_length"],
            2.0
        )

        self.assertEqual(
            result["evaluation"]["validation_rate"],
            1.0
        )

        self.assertEqual(
            result["adaptive_sequence"],
            [
                "permission_test",
                "tool_access_test"
            ]
        )


if __name__ == "__main__":
    unittest.main()