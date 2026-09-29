import unittest

from sandbox.evaluation.day12_dataset import (
    build_day12_dataset
)

from sandbox.evaluation.research_summary import (
    summarize_research_dataset
)


class TestResearchSummary(unittest.TestCase):

    def test_research_summary(self):

        dataset = build_day12_dataset()

        summary = summarize_research_dataset(
            dataset
        )

        # --------------------------------------------------
        # Overall
        # --------------------------------------------------

        self.assertEqual(
            summary["total_experiments"],
            4
        )

        # --------------------------------------------------
        # Static
        # --------------------------------------------------

        self.assertEqual(
            summary["static"]["experiments"],
            1
        )

        self.assertEqual(
            summary["static"]["total_tests"],
            3
        )

        self.assertEqual(
            summary["static"]["total_findings"],
            3
        )

        self.assertEqual(
            summary["static"]["total_candidate_chains"],
            1
        )

        self.assertEqual(
            summary["static"]["total_validated_chains"],
            1
        )

        self.assertEqual(
            summary["static"]["average_validation_rate"],
            1.0
        )

        # --------------------------------------------------
        # Adaptive
        # --------------------------------------------------

        self.assertEqual(
            summary["adaptive"]["experiments"],
            3
        )

        self.assertEqual(
            summary["adaptive"]["total_tests"],
            9
        )

        self.assertEqual(
            summary["adaptive"]["total_findings"],
            9
        )

        self.assertEqual(
            summary["adaptive"]["total_candidate_chains"],
            3
        )

        self.assertEqual(
            summary["adaptive"]["total_validated_chains"],
            2
        )

        expected_average_rate = (
            1.0 + 0.3333 + 1.0
        ) / 3

        self.assertAlmostEqual(
            summary["adaptive"]["average_validation_rate"],
            expected_average_rate,
            places=4
        )


if __name__ == "__main__":
    unittest.main()