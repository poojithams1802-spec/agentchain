import unittest

from ..evaluation.phase2_conditions import (
    PHASE2_CONDITIONS,
    get_all_phase2_conditions,
    get_phase2_condition,
)


class TestPhase2Conditions(unittest.TestCase):

    def test_all_four_conditions_exist(self):
        expected = {
            "rule_based_fixed_mitigation",
            "llm_recommendation_only",
            "level3_proposed",
            "wrong_control",
        }

        self.assertEqual(
            set(PHASE2_CONDITIONS.keys()),
            expected
        )

    def test_rule_based_condition(self):
        condition = get_phase2_condition(
            "rule_based_fixed_mitigation"
        )

        self.assertIsNotNone(condition)
        self.assertTrue(condition["automatic_application"])
        self.assertTrue(condition["replay"])
        self.assertTrue(condition["validation"])

    def test_llm_recommendation_only(self):
        condition = get_phase2_condition(
            "llm_recommendation_only"
        )

        self.assertIsNotNone(condition)
        self.assertFalse(condition["automatic_application"])
        self.assertFalse(condition["replay"])
        self.assertFalse(condition["validation"])

    def test_level3_condition(self):
        condition = get_phase2_condition(
            "level3_proposed"
        )

        self.assertIsNotNone(condition)
        self.assertTrue(condition["automatic_application"])
        self.assertTrue(condition["replay"])
        self.assertTrue(condition["validation"])

    def test_wrong_control_condition(self):
        condition = get_phase2_condition(
            "wrong_control"
        )

        self.assertIsNotNone(condition)
        self.assertTrue(condition["automatic_application"])
        self.assertTrue(condition["replay"])
        self.assertTrue(condition["validation"])

    def test_unknown_condition(self):
        self.assertIsNone(
            get_phase2_condition("unknown_condition")
        )

    def test_get_all_conditions(self):
        conditions = get_all_phase2_conditions()

        self.assertEqual(
            len(conditions),
            4
        )


if __name__ == "__main__":
    unittest.main()