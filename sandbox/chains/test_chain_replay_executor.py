import unittest

from .chain_replay_executor import replay_chain


class TestChainReplayExecutor(unittest.TestCase):

    def test_successful_chain_disruption(self):
        result = replay_chain(
            "DAY4-CHAIN-001",
            "CHAIN-AUTH-TOOL",
            "authorization_gate",
        )

        self.assertEqual(
            result["status"],
            "completed",
        )

        self.assertEqual(
            result["chain_id"],
            "CHAIN-AUTH-TOOL",
        )

        self.assertEqual(
            result["chain_length"],
            2,
        )

        self.assertEqual(
            result["blocked_steps"],
            ["permission_test"],
        )

        self.assertEqual(
            result["residual_vulnerable_steps"],
            ["tool_access_test"],
        )

        self.assertTrue(
            result["chain_disrupted"]
        )

        self.assertEqual(
            result["validation_result"]["status"],
            "validated",
        )

        self.assertEqual(
            result["validation_result"]["validation_rate"],
            1.0,
        )

    def test_three_step_chain_disruption(self):
        result = replay_chain(
            "DAY4-CHAIN-002",
            "CHAIN-AUTH-TOOL-MEM",
            "authorization_gate",
        )

        self.assertEqual(
            result["status"],
            "completed",
        )

        self.assertEqual(
            result["chain_length"],
            3,
        )

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

        self.assertTrue(
            result["chain_disrupted"]
        )

        self.assertEqual(
            result["validation_result"]["status"],
            "validated",
        )

    def test_wrong_control_does_not_disrupt_chain(self):
        result = replay_chain(
            "DAY4-CHAIN-003",
            "CHAIN-AUTH-TOOL",
            "memory_validation",
        )

        self.assertEqual(
            result["status"],
            "completed",
        )

        self.assertEqual(
            result["blocked_steps"],
            [],
        )

        self.assertEqual(
            result["residual_vulnerable_steps"],
            [
                "permission_test",
                "tool_access_test",
            ],
        )

        self.assertFalse(
            result["chain_disrupted"]
        )

        self.assertEqual(
            result["validation_result"]["status"],
            "invalid",
        )

        self.assertEqual(
            result["validation_result"]["validation_rate"],
            0.0,
        )

    def test_unknown_chain_fails(self):
        result = replay_chain(
            "DAY4-CHAIN-004",
            "UNKNOWN-CHAIN",
            "authorization_gate",
        )

        self.assertEqual(
            result["status"],
            "failed",
        )

        self.assertIn(
            "Unknown chain",
            result["error"],
        )


if __name__ == "__main__":
    unittest.main()