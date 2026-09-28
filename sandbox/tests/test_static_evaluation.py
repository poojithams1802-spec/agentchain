import unittest

from sandbox.evaluation.static_evaluation import (
    run_static_evaluation
)


class TestStaticEvaluation(unittest.TestCase):

    def test_static_evaluation(self):

        result = run_static_evaluation(
            "STATIC_DAY10",
            "STATIC_CHAIN_DAY10"
        )

        self.assertEqual(
            result["status"],
            "completed"
        )

        evaluation = result["evaluation"]

        self.assertEqual(
            evaluation["mode"],
            "static"
        )

        self.assertEqual(
            evaluation["total_tests"],
            3
        )

        self.assertEqual(
            evaluation["total_findings"],
            3
        )

        self.assertEqual(
            evaluation["candidate_chains"],
            1
        )

        self.assertEqual(
            evaluation["validated_chains"],
            1
        )

        self.assertEqual(
            evaluation["average_chain_length"],
            3
        )

        self.assertEqual(
            evaluation["validation_rate"],
            1.0
        )


if __name__ == "__main__":
    unittest.main()