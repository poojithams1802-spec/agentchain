import unittest

from sandbox.evaluation.comparison import compare_evaluations


class TestEvaluationComparison(unittest.TestCase):

    def test_compare_static_and_adaptive(self):

        static_result = {
            "mode": "static",
            "experiment_id": "STATIC_TEST",
            "total_tests": 3,
            "total_findings": 3,
            "candidate_chains": 1,
            "validated_chains": 1,
            "average_chain_length": 3.0,
            "validation_rate": 1.0
        }

        adaptive_result = {
            "mode": "adaptive",
            "experiment_id": "ADAPTIVE_TEST",
            "total_tests": 2,
            "total_findings": 2,
            "candidate_chains": 1,
            "validated_chains": 1,
            "average_chain_length": 2.0,
            "validation_rate": 1.0
        }

        result = compare_evaluations(
            static_result,
            adaptive_result
        )

        self.assertEqual(
            result["comparison"]["total_tests_difference"],
            -1
        )

        self.assertEqual(
            result["comparison"]["total_findings_difference"],
            -1
        )

        self.assertEqual(
            result["comparison"]["candidate_chains_difference"],
            0
        )

        self.assertEqual(
            result["comparison"]["validated_chains_difference"],
            0
        )

        self.assertEqual(
            result["comparison"]["average_chain_length_difference"],
            -1.0
        )

        self.assertEqual(
            result["comparison"]["validation_rate_difference"],
            0.0
        )


if __name__ == "__main__":
    unittest.main()