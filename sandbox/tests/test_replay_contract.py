import unittest

from sandbox.mitigation.replay_executor import replay_attack
from sandbox.mitigation.mitigation_state import (
    is_mitigation_active,
    reset_mitigations,
)


class TestReplayContract(unittest.TestCase):

    def setUp(self):
        self.experiment_id = "replay_contract_test"

        reset_mitigations(
            self.experiment_id
        )

    def tearDown(self):
        reset_mitigations(
            self.experiment_id
        )

    # ---------------------------------------------------------
    # Authorization Gate
    # ---------------------------------------------------------

    def test_authorization_gate_replay_contract(self):

        result = replay_attack(
            self.experiment_id,
            "permission_test",
            "authorization_gate"
        )

        self.assertEqual(
            result["status"],
            "completed"
        )

        self.assertEqual(
            result["experiment_id"],
            self.experiment_id
        )

        self.assertEqual(
            result["test"],
            "permission_test"
        )

        self.assertEqual(
            result["control"],
            "authorization_gate"
        )

        self.assertIn(
            "before_validation",
            result
        )

        self.assertIn(
            "after_validation",
            result
        )

        self.assertIn(
            "disrupted",
            result
        )

        self.assertIn(
            "residual_vulnerable_steps",
            result
        )

        self.assertIn(
            "validation_result",
            result
        )

        self.assertTrue(
            result["disrupted"]
        )

        self.assertEqual(
            result["residual_vulnerable_steps"],
            []
        )

        self.assertEqual(
            result["validation_result"]["status"],
            "validated"
        )

    # ---------------------------------------------------------
    # Tool Allowlist
    # ---------------------------------------------------------

    def test_tool_allowlist_replay_contract(self):

        result = replay_attack(
            self.experiment_id,
            "tool_access_test",
            "tool_allowlist"
        )

        self.assertEqual(
            result["status"],
            "completed"
        )

        self.assertEqual(
            result["test"],
            "tool_access_test"
        )

        self.assertEqual(
            result["control"],
            "tool_allowlist"
        )

        self.assertIn(
            "before_validation",
            result
        )

        self.assertIn(
            "after_validation",
            result
        )

        self.assertIn(
            "disrupted",
            result
        )

        self.assertIn(
            "residual_vulnerable_steps",
            result
        )

        self.assertIn(
            "validation_result",
            result
        )

        self.assertTrue(
            result["disrupted"]
        )

        self.assertEqual(
            result["residual_vulnerable_steps"],
            []
        )

        self.assertEqual(
            result["validation_result"]["status"],
            "validated"
        )

    # ---------------------------------------------------------
    # Memory Validation
    # ---------------------------------------------------------

    def test_memory_validation_replay_contract(self):

        result = replay_attack(
            self.experiment_id,
            "memory_access_test",
            "memory_validation"
        )

        self.assertEqual(
            result["status"],
            "completed"
        )

        self.assertEqual(
            result["test"],
            "memory_access_test"
        )

        self.assertEqual(
            result["control"],
            "memory_validation"
        )

        self.assertIn(
            "before_validation",
            result
        )

        self.assertIn(
            "after_validation",
            result
        )

        self.assertIn(
            "disrupted",
            result
        )

        self.assertIn(
            "residual_vulnerable_steps",
            result
        )

        self.assertIn(
            "validation_result",
            result
        )

        self.assertTrue(
            result["disrupted"]
        )

        self.assertEqual(
            result["residual_vulnerable_steps"],
            []
        )

        self.assertEqual(
            result["validation_result"]["status"],
            "validated"
        )

    # ---------------------------------------------------------
    # Backward compatibility
    # ---------------------------------------------------------

    def test_old_replay_fields_are_preserved(self):

        result = replay_attack(
            self.experiment_id,
            "tool_access_test",
            "tool_allowlist"
        )

        self.assertIn(
            "before",
            result
        )

        self.assertIn(
            "after",
            result
        )

        self.assertIn(
            "attack_disrupted",
            result
        )

        self.assertTrue(
            result["attack_disrupted"]
        )

    # ---------------------------------------------------------
    # Mitigation reset
    # ---------------------------------------------------------

    def test_mitigation_is_reset_after_replay(self):

        result = replay_attack(
            self.experiment_id,
            "permission_test",
            "authorization_gate"
        )

        self.assertEqual(
            result["reset"]["status"],
            "reset"
        )

        self.assertFalse(
            is_mitigation_active(
                self.experiment_id,
                "authorization_gate"
            )
        )

    # ---------------------------------------------------------
    # Invalid experiment
    # ---------------------------------------------------------

    def test_missing_experiment_id(self):

        result = replay_attack(
            None,
            "permission_test",
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
    # Invalid test
    # ---------------------------------------------------------

    def test_missing_test_name(self):

        result = replay_attack(
            self.experiment_id,
            None,
            "authorization_gate"
        )

        self.assertEqual(
            result["status"],
            "failed"
        )

        self.assertIn(
            "test_name is required",
            result["evidence"]
        )

    # ---------------------------------------------------------
    # Invalid control
    # ---------------------------------------------------------

    def test_missing_control_name(self):

        result = replay_attack(
            self.experiment_id,
            "permission_test",
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


if __name__ == "__main__":
    unittest.main()