import unittest

from sandbox.mitigation.mitigation_executor import apply_mitigation
from sandbox.mitigation.mitigation_state import (
    is_mitigation_active,
    reset_mitigations,
)


class TestTwoArgumentMitigation(unittest.TestCase):

    def setUp(self):
        self.experiment_id = "two_argument_test"
        reset_mitigations(self.experiment_id)

    def tearDown(self):
        reset_mitigations(self.experiment_id)

    def test_authorization_gate_two_arguments(self):
        result = apply_mitigation(
            self.experiment_id,
            "authorization_gate"
        )

        self.assertEqual(result["status"], "applied")
        self.assertEqual(
            result["target"],
            "weak_permission_control"
        )
        self.assertEqual(
            result["test"],
            "permission_test"
        )
        self.assertTrue(
            is_mitigation_active(
                self.experiment_id,
                "authorization_gate"
            )
        )

    def test_tool_allowlist_two_arguments(self):
        result = apply_mitigation(
            self.experiment_id,
            "tool_allowlist"
        )

        self.assertEqual(result["status"], "applied")
        self.assertEqual(
            result["target"],
            "unsafe_tool_access"
        )
        self.assertEqual(
            result["test"],
            "tool_access_test"
        )
        self.assertTrue(
            is_mitigation_active(
                self.experiment_id,
                "tool_allowlist"
            )
        )

    def test_memory_validation_two_arguments(self):
        result = apply_mitigation(
            self.experiment_id,
            "memory_validation"
        )

        self.assertEqual(result["status"], "applied")
        self.assertEqual(
            result["target"],
            "memory_validation_weakness"
        )
        self.assertEqual(
            result["test"],
            "memory_access_test"
        )
        self.assertTrue(
            is_mitigation_active(
                self.experiment_id,
                "memory_validation"
            )
        )


if __name__ == "__main__":
    unittest.main()