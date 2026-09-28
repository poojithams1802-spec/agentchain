import unittest

from sandbox.evaluation.day12_dataset import (
    build_day12_dataset
)


class TestDay12Dataset(unittest.TestCase):

    def test_day12_dataset(self):

        dataset = build_day12_dataset()

        self.assertEqual(
            dataset["total_experiments"],
            2
        )

        self.assertEqual(
            dataset["experiments"][0]["experiment_id"],
            "EXP007"
        )

        self.assertEqual(
            dataset["experiments"][1]["experiment_id"],
            "EXP008"
        )

        self.assertEqual(
            dataset["experiments"][0]["validation_rate"],
            1.0
        )

        self.assertEqual(
            dataset["experiments"][1]["validation_rate"],
            0.3333
        )

        self.assertEqual(
            dataset["experiments"][0]["execution_count"],
            3
        )

        self.assertEqual(
            dataset["experiments"][1]["execution_count"],
            3
        )


if __name__ == "__main__":
    unittest.main()