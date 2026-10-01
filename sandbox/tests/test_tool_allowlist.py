import unittest

from sandbox.mitigation.tool_allowlist import check_tool_access
from sandbox.mitigation.mitigation_executor import apply_mitigation


class TestToolAllowlist(unittest.TestCase):

    def test_tool_not_allowed(self):
        result = check_tool_access(
            "file",
            ["search", "memory"]
        )

        self.assertFalse(result["allowed"])
        self.assertEqual(result["status"], "blocked")

    def test_tool_allowed(self):
        result = check_tool_access(
            "search",
            ["search", "memory"]
        )

        self.assertTrue(result["allowed"])
        self.assertEqual(result["status"], "allowed")

    def test_executor_integration(self):
        result = apply_mitigation(
            experiment_id="exp_day2",
            control_name="tool_allowlist",
            tool_name="file",
            allowed_tools=["search", "memory"]
        )

        self.assertEqual(result["status"], "applied")
        self.assertEqual(result["target"], "unsafe_tool_access")
        self.assertFalse(result["allowed"])


if __name__ == "__main__":
    unittest.main()