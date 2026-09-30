import unittest

from sandbox.mitigation.mitigation_registry import (
    is_valid_control,
    get_control,
    get_all_controls,
)

from sandbox.mitigation.mitigation_executor import (
    apply_mitigation,
)


class TestMitigationRegistry(unittest.TestCase):

    def test_registered_controls(self):
        self.assertTrue(is_valid_control("authorization_gate"))
        self.assertTrue(is_valid_control("tool_allowlist"))
        self.assertTrue(is_valid_control("memory_validation"))

    def test_unknown_control(self):
        self.assertFalse(is_valid_control("unknown_control"))

    def test_get_control(self):
        control = get_control("tool_allowlist")

        self.assertIsNotNone(control)
        self.assertEqual(
            control["target"],
            "unsafe_tool_access"
        )

    def test_get_all_controls(self):
        controls = get_all_controls()

        self.assertEqual(len(controls), 3)


class TestMitigationExecutor(unittest.TestCase):

    def test_missing_experiment_id(self):
        result = apply_mitigation(
            "",
            "tool_allowlist"
        )

        self.assertEqual(result["status"], "failed")

    def test_missing_control(self):
        result = apply_mitigation(
            "EXP011",
            ""
        )

        self.assertEqual(result["status"], "failed")

    def test_unknown_control(self):
        result = apply_mitigation(
            "EXP011",
            "unknown_control"
        )

        self.assertEqual(result["status"], "failed")

    def test_registered_control(self):
        result = apply_mitigation(
            "EXP011",
            "tool_allowlist"
        )

        self.assertEqual(result["status"], "ready")
        self.assertEqual(
            result["control"],
            "tool_allowlist"
        )


if __name__ == "__main__":
    unittest.main()