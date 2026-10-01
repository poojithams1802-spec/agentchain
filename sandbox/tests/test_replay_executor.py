import unittest

from sandbox.mitigation.replay_executor import replay_attack


class TestReplayExecutor(unittest.TestCase):

    def test_authorization_gate_replay(self):
        result = replay_attack(
            experiment_id="replay_executor_1",
            test_name="permission_test",
            control_name="authorization_gate"
        )

        self.assertEqual(
            result["status"],
            "completed"
        )

        self.assertEqual(
            result["test"],
            "permission_test"
        )

        self.assertEqual(
            result["control"],
            "authorization_gate"
        )

        self.assertTrue(
            result["attack_disrupted"]
        )

        self.assertEqual(
            result["before"]["status"],
            "completed"
        )

        self.assertTrue(
            result["after"]["mitigation_applied"]
        )

        self.assertEqual(
            result["reset"]["status"],
            "reset"
        )

    def test_tool_allowlist_replay(self):
        result = replay_attack(
            experiment_id="replay_executor_2",
            test_name="tool_access_test",
            control_name="tool_allowlist"
        )

        self.assertEqual(
            result["status"],
            "completed"
        )

        self.assertTrue(
            result["attack_disrupted"]
        )

        self.assertEqual(
            result["after"]["mitigation_control"],
            "tool_allowlist"
        )

    def test_memory_validation_replay(self):
        result = replay_attack(
            experiment_id="replay_executor_3",
            test_name="memory_access_test",
            control_name="memory_validation"
        )

        self.assertEqual(
            result["status"],
            "completed"
        )

        self.assertTrue(
            result["attack_disrupted"]
        )

        self.assertEqual(
            result["after"]["mitigation_control"],
            "memory_validation"
        )


if __name__ == "__main__":
    unittest.main()