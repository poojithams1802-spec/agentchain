import unittest

from .sandbox_executor import execute_sandbox_test


class TestSandboxExecutorCost(unittest.TestCase):

    def test_execution_cost_metadata_exists(self):
        result = execute_sandbox_test(
            "DAY5-COST-001",
            "permission_test",
        )

        self.assertEqual(
            result["status"],
            "completed",
        )

        self.assertIn(
            "execution_cost",
            result,
        )

        self.assertEqual(
            result["execution_cost"]["test_count"],
            1,
        )

        self.assertGreaterEqual(
            result["execution_cost"]["execution_time_seconds"],
            0.0,
        )

    def test_mitigated_execution_preserves_cost_metadata(self):
        from ..mitigation.mitigation_executor import apply_mitigation
        from ..mitigation.mitigation_state import reset_mitigations

        experiment_id = "DAY5-COST-002"

        reset_mitigations(experiment_id)

        activation = apply_mitigation(
            experiment_id,
            "authorization_gate",
        )

        self.assertEqual(
            activation["status"],
            "applied",
        )

        result = execute_sandbox_test(
            experiment_id,
            "permission_test",
        )

        self.assertTrue(
            result["mitigation_applied"]
        )

        self.assertIn(
            "execution_cost",
            result,
        )

        self.assertEqual(
            result["execution_cost"]["test_count"],
            1,
        )

        self.assertGreaterEqual(
            result["execution_cost"]["execution_time_seconds"],
            0.0,
        )

        reset_mitigations(experiment_id)


if __name__ == "__main__":
    unittest.main()