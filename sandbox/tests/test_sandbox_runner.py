import unittest

from test_runner import run_test


class TestSandboxRunner(unittest.TestCase):

    def test_permission_test(self):
        result = run_test("permission_test")

        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["test"], "permission_test")
        self.assertEqual(result["finding"], "weak_permission_control")
        self.assertEqual(result["severity"], "high")

    def test_tool_access_test(self):
        result = run_test("tool_access_test")

        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["test"], "tool_access_test")
        self.assertEqual(result["finding"], "unsafe_tool_access")
        self.assertEqual(result["severity"], "high")

    def test_memory_access_test(self):
        result = run_test("memory_access_test")

        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["test"], "memory_access_test")
        self.assertEqual(result["finding"], "memory_validation_weakness")
        self.assertEqual(result["severity"], "medium")

    def test_unknown_test(self):
        result = run_test("unknown_test")

        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["test"], "unknown_test")


if __name__ == "__main__":
    unittest.main()