import unittest

from sandbox.mitigation.replay_executor import replay_attack
from sandbox.mitigation.mitigation_state import (
    is_mitigation_active,
    reset_mitigations,
)


class TestReplayExecutorErrors(unittest.TestCase):

    def tearDown(self):
        reset_mitigations("error_test")

    def test_missing_experiment_id(self):
        result = replay_attack(
            experiment_id=None,
            test_name="permission_test",
            control_name="authorization_gate"
        )

        self.assertEqual(result["status"], "failed")
        self.assertEqual(
            result["evidence"],
            "experiment_id is required."
        )

    def test_missing_test_name(self):
        result = replay_attack(
            experiment_id="error_test",
            test_name=None,
            control_name="authorization_gate"
        )

        self.assertEqual(result["status"], "failed")
        self.assertEqual(
            result["evidence"],
            "test_name is required."
        )

    def test_missing_control_name(self):
        result = replay_attack(
            experiment_id="error_test",
            test_name="permission_test",
            control_name=None
        )

        self.assertEqual(result["status"], "failed")
        self.assertEqual(
            result["evidence"],
            "control_name is required."
        )

    def test_invalid_test_name(self):
        result = replay_attack(
            experiment_id="error_test",
            test_name="invalid_test",
            control_name="authorization_gate"
        )

        self.assertEqual(result["status"], "completed")
        self.assertEqual(
            result["before"]["status"],
            "failed"
        )

        # The mitigation should still have been reset.
        self.assertFalse(
            is_mitigation_active(
                "error_test",
                "authorization_gate"
            )
        )


if __name__ == "__main__":
    unittest.main()