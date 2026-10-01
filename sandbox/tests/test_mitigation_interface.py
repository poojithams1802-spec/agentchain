import unittest

from sandbox.mitigation.mitigation_executor import apply_mitigation


class TestMitigationExecutor(unittest.TestCase):

    def test_missing_experiment_id(self):
        result = apply_mitigation(
            experiment_id=None,
            control_name="authorization_gate"
        )

        self.assertEqual(result["status"], "failed")
        self.assertEqual(
            result["evidence"],
            "experiment_id is required."
        )

    def test_missing_control_name(self):
        result = apply_mitigation(
            experiment_id="exp1",
            control_name=None
        )

        self.assertEqual(result["status"], "failed")
        self.assertEqual(
            result["evidence"],
            "control_name is required."
        )

    def test_invalid_control(self):
        result = apply_mitigation(
            experiment_id="exp1",
            control_name="invalid_control"
        )

        self.assertEqual(result["status"], "failed")
        self.assertEqual(
            result["evidence"],
            "Control is not registered."
        )

    def test_authorization_control_missing_data(self):
        result = apply_mitigation(
            experiment_id="exp1",
            control_name="authorization_gate"
        )

        self.assertEqual(result["status"], "failed")
        self.assertEqual(
            result["target"],
            "weak_permission_control"
        )

    def test_tool_allowlist_missing_data(self):
        result = apply_mitigation(
            experiment_id="exp1",
            control_name="tool_allowlist"
        )

        self.assertEqual(result["status"], "failed")
        self.assertEqual(
            result["target"],
            "unsafe_tool_access"
        )

    def test_registered_control_without_required_data(self):
        result = apply_mitigation(
            experiment_id="exp1",
            control_name="memory_validation"
        )

        self.assertEqual(result["status"], "failed")
        self.assertEqual(
            result["target"],
            "memory_validation_weakness"
        )


if __name__ == "__main__":
    unittest.main()