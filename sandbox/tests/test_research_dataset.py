import unittest

from sandbox.evaluation.research_dataset import (
    create_research_dataset,
    add_experiment
)


class TestResearchDataset(unittest.TestCase):

    def test_create_empty_dataset(self):

        dataset = create_research_dataset()

        self.assertEqual(
            dataset["experiments"],
            []
        )

        self.assertEqual(
            dataset["total_experiments"],
            0
        )

    def test_add_experiment(self):

        dataset = create_research_dataset()

        experiment = {
            "experiment_id": "EXP008",
            "mode": "adaptive",
            "validation_rate": 0.3333
        }

        result = add_experiment(
            dataset,
            experiment
        )

        self.assertEqual(
            result["total_experiments"],
            1
        )

        self.assertEqual(
            result["experiments"][0]["experiment_id"],
            "EXP008"
        )

        self.assertEqual(
            result["experiments"][0]["validation_rate"],
            0.3333
        )


if __name__ == "__main__":
    unittest.main()