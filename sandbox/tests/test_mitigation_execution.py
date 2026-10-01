import unittest

from sandbox.execution.sandbox_executor import execute_sandbox_test
from sandbox.mitigation.mitigation_state import (
    activate_mitigation,
    reset_mitigations,
)


class TestMitigationExecution(unittest.TestCase):

    def setUp(self):
        reset_mitigations("execution_test")

    def tearDown(self):
        reset_mitigations("execution_test")

    def test_permission_without_mitigation(self):
        result = execute_sandbox_test(
            "execution_test",
            "permission_test"
        )

        self.assertEqual(result["status"], "completed")
        self.assertEqual(
            result["confidence"],
            1.0
        )
        self.assertNotIn(
            "mitigation_applied",
            result
        )

    def test_permission_with_authorization_gate(self):
        activate_mitigation(
            "execution_test",
            "authorization_gate"
        )

        result = execute_sandbox_test(
            "execution_test",
            "permission_test"
        )

        self.assertEqual(result["status"], "completed")
        self.assertTrue(result["mitigation_applied"])
        self.assertEqual(
            result["mitigation_control"],
            "authorization_gate"
        )
        self.assertEqual(
            result["evidence"]["result"],
            "attack_blocked"
        )

    def test_tool_access_with_tool_allowlist(self):
        activate_mitigation(
            "execution_test",
            "tool_allowlist"
        )

        result = execute_sandbox_test(
            "execution_test",
            "tool_access_test"
        )

        self.assertTrue(result["mitigation_applied"])
        self.assertEqual(
            result["mitigation_control"],
            "tool_allowlist"
        )
        self.assertEqual(
            result["evidence"]["result"],
            "attack_blocked"
        )

    def test_memory_access_with_validation(self):
        activate_mitigation(
            "execution_test",
            "memory_validation"
        )

        result = execute_sandbox_test(
            "execution_test",
            "memory_access_test"
        )

        self.assertTrue(result["mitigation_applied"])
        self.assertEqual(
            result["mitigation_control"],
            "memory_validation"
        )
        self.assertEqual(
            result["evidence"]["result"],
            "attack_blocked"
        )


if __name__ == "__main__":
    unittest.main()