import unittest

from .adaptive_test_executor import (
    validate_selected_test,
    execute_selected_test,
)


class TestAdaptiveTestExecutor(unittest.TestCase):

    def test_valid_selected_test(self):
        result = validate_selected_test(
            "permission_test"
        )

        self.assertTrue(
            result["valid"]
        )

        self.assertEqual(
            result["selected_test"],
            "permission_test",
        )

        self.assertIsNone(
            result["error"]
        )

    def test_invalid_selected_test(self):
        result = validate_selected_test(
            "invented_test"
        )

        self.assertFalse(
            result["valid"]
        )

        self.assertEqual(
            result["selected_test"],
            "invented_test",
        )

        self.assertIn(
            "not sandbox-approved",
            result["error"],
        )

    def test_missing_selected_test(self):
        result = validate_selected_test(
            None
        )

        self.assertFalse(
            result["valid"]
        )

        self.assertIn(
            "required",
            result["error"],
        )

    def test_non_string_selected_test(self):
        result = validate_selected_test(
            123
        )

        self.assertFalse(
            result["valid"]
        )

        self.assertIn(
            "must be a string",
            result["error"],
        )

    def test_execute_valid_selected_test(self):
        result = execute_selected_test(
            "DAY6-SELECTED-001",
            "permission_test",
        )

        self.assertEqual(
            result["status"],
            "completed",
        )

        self.assertTrue(
            result["executed"]
        )

        self.assertEqual(
            result["selected_test"],
            "permission_test",
        )

        self.assertEqual(
            result["result"]["test"],
            "permission_test",
        )

        self.assertIn(
            "execution_cost",
            result,
        )

        self.assertEqual(
            result["execution_cost"]["test_count"],
            1,
        )

    def test_execute_invalid_selected_test_is_rejected(self):
        result = execute_selected_test(
            "DAY6-SELECTED-002",
            "invented_test",
        )

        self.assertEqual(
            result["status"],
            "rejected",
        )

        self.assertFalse(
            result["executed"]
        )

        self.assertIsNone(
            result["result"]
        )

        self.assertIsNone(
            result["execution_cost"]
        )


if __name__ == "__main__":
    unittest.main()