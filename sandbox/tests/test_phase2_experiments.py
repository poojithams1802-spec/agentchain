import unittest

from ..evaluation.phase2_experiments import (
    EXPERIMENTS,
    get_all_phase2_experiments,
    get_experiment_condition,
    get_phase2_experiment,
)


class TestPhase2Experiments(unittest.TestCase):

    def test_expected_number_of_experiments(self):
        self.assertEqual(len(EXPERIMENTS), 12)

    def test_three_rule_based_experiments(self):
        experiments = [
            e for e in EXPERIMENTS
            if e["condition"] == "rule_based_fixed_mitigation"
        ]

        self.assertEqual(len(experiments), 3)

        mappings = {
            e["test"]: e["control"]
            for e in experiments
        }

        self.assertEqual(
            mappings,
            {
                "permission_test": "authorization_gate",
                "tool_access_test": "tool_allowlist",
                "memory_access_test": "memory_validation",
            }
        )

    def test_three_llm_recommendation_experiments(self):
        experiments = [
            e for e in EXPERIMENTS
            if e["condition"] == "llm_recommendation_only"
        ]

        self.assertEqual(len(experiments), 3)

        for experiment in experiments:
            self.assertEqual(experiment["llm_calls"], 1)

    def test_three_level3_experiments(self):
        experiments = [
            e for e in EXPERIMENTS
            if e["condition"] == "level3_proposed"
        ]

        self.assertEqual(len(experiments), 3)

    def test_three_wrong_control_experiments(self):
        experiments = [
            e for e in EXPERIMENTS
            if e["condition"] == "wrong_control"
        ]

        self.assertEqual(len(experiments), 3)

    def test_wrong_controls_are_mismatched(self):
        expected = {
            "permission_test": "tool_allowlist",
            "tool_access_test": "memory_validation",
            "memory_access_test": "authorization_gate",
        }

        experiments = [
            e for e in EXPERIMENTS
            if e["condition"] == "wrong_control"
        ]

        actual = {
            e["test"]: e["control"]
            for e in experiments
        }

        self.assertEqual(actual, expected)

    def test_experiment_lookup(self):
        experiment = get_phase2_experiment("P2-L3-001")

        self.assertIsNotNone(experiment)
        self.assertEqual(
            experiment["test"],
            "permission_test"
        )
        self.assertEqual(
            experiment["control"],
            "authorization_gate"
        )

    def test_unknown_experiment(self):
        self.assertIsNone(
            get_phase2_experiment("UNKNOWN")
        )

    def test_condition_lookup(self):
        condition = get_experiment_condition(
            "P2-L3-001"
        )

        self.assertIsNotNone(condition)
        self.assertEqual(
            condition["name"],
            "Level-3 proposed approach"
        )

    def test_all_experiments_returns_copies(self):
        experiments = get_all_phase2_experiments()

        self.assertEqual(len(experiments), 12)

        experiments[0]["experiment_id"] = "MODIFIED"

        self.assertNotEqual(
            EXPERIMENTS[0]["experiment_id"],
            "MODIFIED"
        )
    def test_expected_controls_are_defined(self):
        for experiment in EXPERIMENTS:
            self.assertIn(
                "expected_control",
                experiment
            )

            self.assertIn(
                "control",
                experiment
            )
    def test_wrong_controls_are_marked_incorrect(self):
        wrong_experiments = [
            e for e in EXPERIMENTS
            if e["condition"] == "wrong_control"
        ]

        for experiment in wrong_experiments:
            self.assertNotEqual(
                experiment["expected_control"],
                experiment["control"]
            )
if __name__ == "__main__":
    unittest.main()