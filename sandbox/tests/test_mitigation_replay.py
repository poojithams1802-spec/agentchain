import unittest

from sandbox.execution.sandbox_executor import execute_sandbox_test
from sandbox.mitigation.mitigation_state import (
    activate_mitigation,
    reset_mitigations,
)


class TestMitigationReplay(unittest.TestCase):

    def setUp(self):
        self.experiment_id = "replay_test"
        reset_mitigations(self.experiment_id)

    def tearDown(self):
        reset_mitigations(self.experiment_id)

    def test_authorization_gate_replay(self):
        # BEFORE: run the attack without mitigation
        before = execute_sandbox_test(
            self.experiment_id,
            "permission_test"
        )

        self.assertEqual(before["status"], "completed")
        self.assertNotIn("mitigation_applied", before)

        # Apply the defensive control
        activation = activate_mitigation(
            self.experiment_id,
            "authorization_gate"
        )

        self.assertEqual(
            activation["status"],
            "activated"
        )

        # AFTER: replay the SAME attack
        after = execute_sandbox_test(
            self.experiment_id,
            "permission_test"
        )

        self.assertEqual(after["status"], "completed")
        self.assertTrue(after["mitigation_applied"])
        self.assertEqual(
            after["mitigation_control"],
            "authorization_gate"
        )
        self.assertEqual(
            after["evidence"]["result"],
            "attack_blocked"
        )

    def test_tool_allowlist_replay(self):
        # BEFORE
        before = execute_sandbox_test(
            self.experiment_id,
            "tool_access_test"
        )

        self.assertEqual(before["status"], "completed")
        self.assertNotIn("mitigation_applied", before)

        # Apply mitigation
        activate_mitigation(
            self.experiment_id,
            "tool_allowlist"
        )

        # AFTER: same attack
        after = execute_sandbox_test(
            self.experiment_id,
            "tool_access_test"
        )

        self.assertTrue(after["mitigation_applied"])
        self.assertEqual(
            after["mitigation_control"],
            "tool_allowlist"
        )
        self.assertEqual(
            after["evidence"]["result"],
            "attack_blocked"
        )

    def test_memory_validation_replay(self):
        # BEFORE
        before = execute_sandbox_test(
            self.experiment_id,
            "memory_access_test"
        )

        self.assertEqual(before["status"], "completed")
        self.assertNotIn("mitigation_applied", before)

        # Apply mitigation
        activate_mitigation(
            self.experiment_id,
            "memory_validation"
        )

        # AFTER: same attack
        after = execute_sandbox_test(
            self.experiment_id,
            "memory_access_test"
        )

        self.assertTrue(after["mitigation_applied"])
        self.assertEqual(
            after["mitigation_control"],
            "memory_validation"
        )
        self.assertEqual(
            after["evidence"]["result"],
            "attack_blocked"
        )

    def test_reset_restores_baseline(self):
        # Activate mitigation
        activate_mitigation(
            self.experiment_id,
            "authorization_gate"
        )

        protected = execute_sandbox_test(
            self.experiment_id,
            "permission_test"
        )

        self.assertTrue(protected["mitigation_applied"])

        # Reset mitigation
        reset_result = reset_mitigations(
            self.experiment_id
        )

        self.assertEqual(
            reset_result["status"],
            "reset"
        )

        # Run the SAME attack again
        baseline = execute_sandbox_test(
            self.experiment_id,
            "permission_test"
        )

        # Mitigation should no longer affect execution
        self.assertNotIn(
            "mitigation_applied",
            baseline
        )


if __name__ == "__main__":
    unittest.main()