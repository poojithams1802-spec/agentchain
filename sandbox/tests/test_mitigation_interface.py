import unittest

from sandbox.mitigation.mitigation_executor import apply_mitigation
from sandbox.mitigation.mitigation_registry import (
    get_all_controls,
    get_control,
    is_valid_control,
)
from sandbox.mitigation.mitigation_state import (
    is_mitigation_active,
    reset_mitigations,
)


class TestMitigationExecutor(unittest.TestCase):

    def setUp(self):
        self.experiment_id = "test_experiment"
        reset_mitigations(self.experiment_id)

    def tearDown(self):
        reset_mitigations(self.experiment_id)

    # ---------------------------------------------------------
    # Invalid experiment ID
    # ---------------------------------------------------------

    def test_missing_experiment_id(self):
        result = apply_mitigation(
            None,
            "authorization_gate"
        )

        self.assertEqual(
            result["status"],
            "failed"
        )

        self.assertIn(
            "experiment_id is required",
            result["evidence"]
        )

    # ---------------------------------------------------------
    # Missing control
    # ---------------------------------------------------------

    def test_missing_control_name(self):
        result = apply_mitigation(
            self.experiment_id,
            None
        )

        self.assertEqual(
            result["status"],
            "failed"
        )

        self.assertIn(
            "control_name is required",
            result["evidence"]
        )

    # ---------------------------------------------------------
    # Invalid control
    # ---------------------------------------------------------

    def test_invalid_control(self):
        result = apply_mitigation(
            self.experiment_id,
            "invalid_control"
        )

        self.assertEqual(
            result["status"],
            "failed"
        )

        self.assertIn(
            "Control is not registered",
            result["evidence"]
        )

    # ---------------------------------------------------------
    # Authorization Gate
    # ---------------------------------------------------------

    def test_authorization_control_without_required_data(self):
        result = apply_mitigation(
            self.experiment_id,
            "authorization_gate"
        )

        self.assertEqual(
            result["status"],
            "applied"
        )

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

    # ---------------------------------------------------------
    # Tool Allowlist
    # ---------------------------------------------------------

    def test_tool_allowlist_without_required_data(self):
        result = apply_mitigation(
            self.experiment_id,
            "tool_allowlist"
        )

        self.assertEqual(
            result["status"],
            "applied"
        )

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

    # ---------------------------------------------------------
    # Memory Validation
    # ---------------------------------------------------------

    def test_registered_control_without_required_data(self):
        result = apply_mitigation(
            self.experiment_id,
            "memory_validation"
        )

        self.assertEqual(
            result["status"],
            "applied"
        )

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

    # ---------------------------------------------------------
    # Authorization validation with data
    # ---------------------------------------------------------

    def test_authorization_with_valid_data(self):
        result = apply_mitigation(
            self.experiment_id,
            "authorization_gate",
            permission="admin",
            required_permission="admin"
        )

        self.assertEqual(
            result["status"],
            "applied"
        )

        self.assertTrue(
            result["allowed"]
        )

        self.assertEqual(
            result["target"],
            "weak_permission_control"
        )

    # ---------------------------------------------------------
    # Tool allowlist validation with data
    # ---------------------------------------------------------

    def test_tool_allowlist_with_valid_data(self):
        result = apply_mitigation(
            self.experiment_id,
            "tool_allowlist",
            tool_name="search_tool",
            allowed_tools=["search_tool", "file_tool"]
        )

        self.assertEqual(
            result["status"],
            "applied"
        )

        self.assertTrue(
            result["allowed"]
        )

        self.assertEqual(
            result["target"],
            "unsafe_tool_access"
        )

    # ---------------------------------------------------------
    # Memory validation with data
    # ---------------------------------------------------------

    def test_memory_validation_with_valid_data(self):
        result = apply_mitigation(
            self.experiment_id,
            "memory_validation",
            memory_value="trusted memory"
        )

        self.assertEqual(
            result["status"],
            "applied"
        )

        self.assertTrue(
            result["valid"]
        )

        self.assertEqual(
            result["target"],
            "memory_validation_weakness"
        )

    # ---------------------------------------------------------
    # Authorization missing required data
    # ---------------------------------------------------------

    def test_authorization_missing_required_data(self):
        result = apply_mitigation(
            self.experiment_id,
            "authorization_gate",
            permission="admin"
        )

        self.assertEqual(
            result["status"],
            "failed"
        )

        self.assertIn(
            "permission and required_permission",
            result["evidence"]
        )

    # ---------------------------------------------------------
    # Tool allowlist missing required data
    # ---------------------------------------------------------

    def test_tool_allowlist_missing_required_data(self):
        result = apply_mitigation(
            self.experiment_id,
            "tool_allowlist",
            tool_name="search_tool"
        )

        self.assertEqual(
            result["status"],
            "failed"
        )

        self.assertIn(
            "tool_name and allowed_tools",
            result["evidence"]
        )

    # ---------------------------------------------------------
    # Memory validation missing required data
    # ---------------------------------------------------------

    def test_memory_validation_missing_required_data(self):
        result = apply_mitigation(
            self.experiment_id,
            "memory_validation",
            memory_value=None
        )

        self.assertEqual(
            result["status"],
            "applied"
        )

        self.assertEqual(
            result["target"],
            "memory_validation_weakness"
        )

    # ---------------------------------------------------------
    # Registry validation
    # ---------------------------------------------------------

    def test_authorization_control_is_registered(self):
        self.assertTrue(
            is_valid_control("authorization_gate")
        )

    def test_tool_allowlist_control_is_registered(self):
        self.assertTrue(
            is_valid_control("tool_allowlist")
        )

    def test_memory_validation_control_is_registered(self):
        self.assertTrue(
            is_valid_control("memory_validation")
        )

    # ---------------------------------------------------------
    # Registry lookup
    # ---------------------------------------------------------

    def test_get_authorization_control(self):
        control = get_control(
            "authorization_gate"
        )

        self.assertIsNotNone(control)

        self.assertEqual(
            control["target"],
            "weak_permission_control"
        )

    def test_get_tool_allowlist_control(self):
        control = get_control(
            "tool_allowlist"
        )

        self.assertIsNotNone(control)

        self.assertEqual(
            control["target"],
            "unsafe_tool_access"
        )

    def test_get_memory_validation_control(self):
        control = get_control(
            "memory_validation"
        )

        self.assertIsNotNone(control)

        self.assertEqual(
            control["target"],
            "memory_validation_weakness"
        )

    # ---------------------------------------------------------
    # All controls
    # ---------------------------------------------------------

    def test_all_controls_available(self):
        controls = get_all_controls()

        self.assertIn(
            "authorization_gate",
            controls
        )

        self.assertIn(
            "tool_allowlist",
            controls
        )

        self.assertIn(
            "memory_validation",
            controls
        )


if __name__ == "__main__":
    unittest.main()