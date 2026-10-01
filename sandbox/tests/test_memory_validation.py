import unittest

from sandbox.mitigation.memory_validation import validate_memory
from sandbox.mitigation.mitigation_executor import apply_mitigation


class TestMemoryValidation(unittest.TestCase):

    def test_empty_memory_is_blocked(self):
        result = validate_memory("")

        self.assertFalse(result["valid"])
        self.assertEqual(result["status"], "blocked")

    def test_valid_memory_is_accepted(self):
        result = validate_memory("User prefers dark mode.")

        self.assertTrue(result["valid"])
        self.assertEqual(result["status"], "validated")

    def test_executor_integration(self):
        result = apply_mitigation(
            experiment_id="exp_day2",
            control_name="memory_validation",
            memory_value=""
        )

        self.assertEqual(result["status"], "applied")
        self.assertEqual(
            result["target"],
            "memory_validation_weakness"
        )
        self.assertFalse(result["valid"])


if __name__ == "__main__":
    unittest.main()