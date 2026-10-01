import unittest

from sandbox.mitigation.replay_executor import replay_attack
from sandbox.execution.sandbox_executor import execute_sandbox_test


class TestReplayBaseline(unittest.TestCase):

    def test_authorization_replay_restores_baseline(self):
        experiment_id = "baseline_auth_test"

        replay = replay_attack(
            experiment_id,
            "permission_test",
            "authorization_gate"
        )

        self.assertEqual(
            replay["status"],
            "completed"
        )

        self.assertTrue(
            replay["attack_disrupted"]
        )

        # After replay_attack(), mitigation should already
        # have been reset.
        baseline = execute_sandbox_test(
            experiment_id,
            "permission_test"
        )

        self.assertNotIn(
            "mitigation_applied",
            baseline
        )

    def test_tool_replay_restores_baseline(self):
        experiment_id = "baseline_tool_test"

        replay = replay_attack(
            experiment_id,
            "tool_access_test",
            "tool_allowlist"
        )

        self.assertTrue(
            replay["attack_disrupted"]
        )

        baseline = execute_sandbox_test(
            experiment_id,
            "tool_access_test"
        )

        self.assertNotIn(
            "mitigation_applied",
            baseline
        )

    def test_memory_replay_restores_baseline(self):
        experiment_id = "baseline_memory_test"

        replay = replay_attack(
            experiment_id,
            "memory_access_test",
            "memory_validation"
        )

        self.assertTrue(
            replay["attack_disrupted"]
        )

        baseline = execute_sandbox_test(
            experiment_id,
            "memory_access_test"
        )

        self.assertNotIn(
            "mitigation_applied",
            baseline
        )


if __name__ == "__main__":
    unittest.main()