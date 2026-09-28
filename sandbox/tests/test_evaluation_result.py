import unittest

from sandbox.evaluation.evaluation_result import (
    create_evaluation_result
)


class TestEvaluationResult(unittest.TestCase):

    def test_static_result(self):

        result = create_evaluation_result(
            "static",
            "STATIC_DAY10",
            3,
            3,
            1,
            1,
            3.0,
            1.0
        )

        self.assertEqual(
            result["mode"],
            "static"
        )

        self.assertEqual(
            result["experiment_id"],
            "STATIC_DAY10"
        )

        self.assertEqual(
            result["total_tests"],
            3
        )

        self.assertEqual(
            result["total_findings"],
            3
        )

        self.assertEqual(
            result["candidate_chains"],
            1
        )

        self.assertEqual(
            result["validated_chains"],
            1
        )

        self.assertEqual(
            result["average_chain_length"],
            3.0
        )

        self.assertEqual(
            result["validation_rate"],
            1.0
        )

    def test_adaptive_result_structure(self):

        result = create_evaluation_result(
            "adaptive",
            "ADAPTIVE_DAY10",
            2,
            2,
            1,
            1,
            2.0,
            1.0
        )

        self.assertEqual(
            result["mode"],
            "adaptive"
        )

        self.assertEqual(
            result["experiment_id"],
            "ADAPTIVE_DAY10"
        )

        self.assertEqual(
            result["total_tests"],
            2
        )

        self.assertEqual(
            result["candidate_chains"],
            1
        )

    def test_invalid_mode(self):

        with self.assertRaises(ValueError):
            create_evaluation_result(
                "unknown",
                "TEST",
                0,
                0,
                0,
                0,
                0.0,
                0.0
            )


if __name__ == "__main__":
    unittest.main()