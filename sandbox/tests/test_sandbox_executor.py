import unittest

from sandbox.execution.sandbox_executor import execute_sandbox_test


class TestSandboxExecutor(unittest.TestCase):

    def test_permission_execution(self):
        result = execute_sandbox_test(
            "EXP001",
            "permission_test"
        )

        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["test"], "permission_test")
        self.assertEqual(
            result["finding"],
            "weak_permission_control"
        )
        self.assertEqual(result["severity"], "high")

    def test_tool_access_execution(self):
        result = execute_sandbox_test(
            "EXP001",
            "tool_access_test"
        )

        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["test"], "tool_access_test")
        self.assertEqual(
            result["finding"],
            "unsafe_tool_access"
        )
        self.assertEqual(result["severity"], "high")

    def test_memory_execution(self):
        result = execute_sandbox_test(
            "EXP001",
            "memory_access_test"
        )

        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["test"], "memory_access_test")
        self.assertEqual(
            result["finding"],
            "memory_validation_weakness"
        )
        self.assertEqual(result["severity"], "medium")

    def test_missing_experiment_id(self):
        result = execute_sandbox_test(
            "",
            "tool_access_test"
        )

        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["test"], "tool_access_test")

    def test_invalid_test(self):
        result = execute_sandbox_test(
            "EXP001",
            "invalid_test"
        )

        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["test"], "invalid_test")


if __name__ == "__main__":
    unittest.main()