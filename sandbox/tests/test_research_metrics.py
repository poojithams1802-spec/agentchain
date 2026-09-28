import unittest

from sandbox.evaluation.day12_dataset import (
    build_day12_dataset
)

from sandbox.evaluation.research_metrics import (
    calculate_research_metrics
)


class TestResearchMetrics(unittest.TestCase):

    def test_research_metrics(self):

        dataset = build_day12_dataset()

        metrics = calculate_research_metrics(
            dataset
        )

        # ----------------------------------------------
        # Static metrics
        # ----------------------------------------------

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

        # ----------------------------------------------
        # Adaptive metrics
        # ----------------------------------------------

        self.assertEqual(
            metrics["adaptive"]["experiments"],
            2
        )

        self.assertEqual(
            metrics["adaptive"]["total_tests"],
            6
        )

        self.assertEqual(
            metrics["adaptive"]["total_findings"],
            6
        )

        self.assertEqual(
            metrics["adaptive"]["candidate_chains"],
            2
        )

        self.assertEqual(
            metrics["adaptive"]["validated_chains"],
            1
        )

        self.assertEqual(
            metrics["adaptive"]["average_chain_length"],
            3.0
        )

        expected_validation_rate = (
            1.0 + 0.3333
        ) / 2

        self.assertAlmostEqual(
            metrics["adaptive"]["validation_rate"],
            expected_validation_rate,
            places=4
        )

        self.assertEqual(
            metrics["adaptive"]["execution_count"],
            6
        )


if __name__ == "__main__":
    unittest.main()