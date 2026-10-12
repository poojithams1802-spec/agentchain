
import unittest
from unittest.mock import patch

from . import chain_replay_executor
from .chain_replay_executor import replay_chain
from ..mitigation.mitigation_state import get_active_mitigations


class TestChainReplayExecutor(unittest.TestCase):

    def test_successful_chain_disruption(self):
        result = replay_chain(
            "DAY4-CHAIN-001",
            "CHAIN-AUTH-TOOL",
            "authorization_gate",
        )

        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["chain_id"], "CHAIN-AUTH-TOOL")
        self.assertEqual(result["chain_length"], 2)
        self.assertEqual(
            result["blocked_steps"],
            ["permission_test"],
        )
        self.assertEqual(
            result["residual_vulnerable_steps"],
            ["tool_access_test"],
        )
        self.assertTrue(result["chain_disrupted"])
        self.assertEqual(
            result["validation_result"]["status"],
            "validated",
        )
        self.assertEqual(
            result["validation_result"]["validation_rate"],
            1.0,
        )
        self.assertEqual(result["reset"]["status"], "reset")

    def test_three_step_chain_disruption(self):
        result = replay_chain(
            "DAY4-CHAIN-002",
            "CHAIN-AUTH-TOOL-MEM",
            "authorization_gate",
        )

        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["chain_length"], 3)
        self.assertEqual(
            result["blocked_steps"],
            ["permission_test"],
        )
        self.assertEqual(
            result["residual_vulnerable_steps"],
            [
                "tool_access_test",
                "memory_access_test",
            ],
        )
        self.assertTrue(result["chain_disrupted"])
        self.assertEqual(
            result["validation_result"]["status"],
            "validated",
        )
        self.assertEqual(result["reset"]["status"], "reset")

    def test_wrong_control_does_not_disrupt_chain(self):
        result = replay_chain(
            "DAY4-CHAIN-003",
            "CHAIN-AUTH-TOOL",
            "memory_validation",
        )

        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["blocked_steps"], [])
        self.assertEqual(
            result["residual_vulnerable_steps"],
            [
                "permission_test",
                "tool_access_test",
            ],
        )
        self.assertFalse(result["chain_disrupted"])
        self.assertEqual(
            result["validation_result"]["status"],
            "invalid",
        )
        self.assertEqual(
            result["validation_result"]["validation_rate"],
            0.0,
        )
        self.assertEqual(result["reset"]["status"], "reset")

    def test_unknown_chain_fails(self):
        result = replay_chain(
            "DAY4-CHAIN-004",
            "UNKNOWN-CHAIN",
            "authorization_gate",
        )

        self.assertEqual(result["status"], "failed")
        self.assertIn("Unknown chain", result["error"])

    def test_mitigation_state_resets_if_replay_raises(self):
        """
        Verify cleanup when replay raises after mitigation activation.
        """
        experiment_id = "DAY4-CHAIN-CLEANUP-EXCEPTION"

        original_execute_steps = (
            chain_replay_executor._execute_steps
        )
        calls = 0

        def fail_on_after_replay(exp_id, steps):
            nonlocal calls
            calls += 1

            # The first call runs the baseline.
            # The second call occurs after mitigation activation.
            if calls == 2:
                raise RuntimeError(
                    "injected post-activation failure"
                )

            return original_execute_steps(exp_id, steps)

        with patch.object(
            chain_replay_executor,
            "_execute_steps",
            side_effect=fail_on_after_replay,
        ):
            with self.assertRaisesRegex(
                RuntimeError,
                "injected post-activation failure",
            ):
                replay_chain(
                    experiment_id,
                    "CHAIN-AUTH-TOOL-MEM",
                    "authorization_gate",
                )

        # Confirm that the exception did not leave mitigation state active.
        self.assertEqual(
            get_active_mitigations(experiment_id),
            [],
        )


if __name__ == "__main__":
    unittest.main()
