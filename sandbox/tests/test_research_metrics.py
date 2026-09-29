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


if __name__ == "__main__":
    unittest.main()