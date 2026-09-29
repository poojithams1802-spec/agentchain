import unittest

from sandbox.evaluation.day12_dataset import (
    build_day12_dataset
)


class TestDay12Dataset(unittest.TestCase):

    def test_day12_dataset(self):

        dataset = build_day12_dataset()

        # ----------------------------------------------
        # Dataset size
        # ----------------------------------------------

        self.assertEqual(
            dataset["total_experiments"],
            4
        )

        # ----------------------------------------------
        # EXP007
        # ----------------------------------------------

        self.assertEqual(
            dataset["experiments"][0]["experiment_id"],
            "EXP007"
        )

        self.assertEqual(
            dataset["experiments"][0]["mode"],
            "adaptive"
        )

        self.assertEqual(
            dataset["experiments"][0]["validation_rate"],
            1.0
        )

        # ----------------------------------------------
        # EXP008
        # ----------------------------------------------

        self.assertEqual(
            dataset["experiments"][1]["experiment_id"],
            "EXP008"
        )

        self.assertEqual(
            dataset["experiments"][1]["mode"],
            "adaptive"
        )

        self.assertEqual(
            dataset["experiments"][1]["validation_rate"],
            0.3333
        )

        # ----------------------------------------------
        # STATIC_DAY12
        # ----------------------------------------------

        self.assertEqual(
            dataset["experiments"][3]["experiment_id"],
            "STATIC_DAY12"
        )

        self.assertEqual(
            dataset["experiments"][3]["mode"],
            "static"
        )

        self.assertEqual(
            dataset["experiments"][2]["validation_rate"],
            1.0
        )

        self.assertEqual(
            dataset["experiments"][2]["execution_count"],
            3
        )


if __name__ == "__main__":
    unittest.main()