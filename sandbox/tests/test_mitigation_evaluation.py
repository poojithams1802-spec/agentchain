import unittest

from sandbox.evaluation.mitigation_evaluation import (
    build_mitigation_experiment_record
)


class TestMitigationEvaluation(unittest.TestCase):

    def test_successful_mitigation_record(self):

        replay_result = {
            "status": "completed",
            "experiment_id": "EXP-P2-001",
            "test": "permission_test",
            "control": "authorization_gate",

            "before": {
                "status": "completed",
                "finding": "weak_permission_control",
                "severity": "high"
            },

            "activation": {
                "status": "applied",
                "control": "authorization_gate"
            },

            "after": {
                "status": "completed",
                "finding": "weak_permission_control",
                "severity": "high",
                "mitigation_applied": True,
                "evidence": {
                    "result": "attack_blocked"
                }
            },

            "before_validation": {
                "valid": True
            },

            "after_validation": {
                "valid": True
            },

            "disrupted": True,

            "residual_vulnerable_steps": [],

            "validation_result": {
                "status": "validated",
                "validation_rate": 1.0
            }
        }

        result = build_mitigation_experiment_record(
            replay_result
        )

        self.assertEqual(
            result["experiment_id"],
            "EXP-P2-001"
        )

        self.assertEqual(
            result["mode"],
            "adaptive"
        )

        self.assertEqual(
            result["mitigation_control"],
            "authorization_gate"
        )

        self.assertTrue(
            result["mitigation_selected"]
        )

        self.assertTrue(
            result["mitigation_applied"]
        )

        self.assertTrue(
            result["attack_success_before"]
        )

        self.assertFalse(
            result["attack_success_after"]
        )

        self.assertTrue(
            result["chain_disrupted"]
        )

        self.assertEqual(
            result["residual_vulnerable_steps"],
            []
        )

        self.assertTrue(
            result["mitigation_validation"]
        )

        self.assertEqual(
            result["execution_count"],
            2
        )

    def test_failed_disruption_record(self):

        replay_result = {
            "status": "completed",
            "experiment_id": "EXP-P2-002",
            "test": "tool_access_test",
            "control": "authorization_gate",

            "before": {
                "status": "completed",
                "finding": "unsafe_tool_access",
                "severity": "high"
            },

            "activation": {
                "status": "applied",
                "control": "authorization_gate"
            },

            "after": {
                "status": "completed",
                "finding": "unsafe_tool_access",
                "severity": "high"
            },

            "before_validation": {
                "valid": True
            },

            "after_validation": {
                "valid": True
            },

            "disrupted": False,

            "residual_vulnerable_steps": [
                "tool_access_test"
            ],

            "validation_result": {
                "status": "invalid",
                "validation_rate": 0.0
            }
        }

        result = build_mitigation_experiment_record(
            replay_result
        )

        self.assertTrue(
            result["attack_success_before"]
        )

        self.assertTrue(
            result["attack_success_after"]
        )

        self.assertFalse(
            result["chain_disrupted"]
        )

        self.assertEqual(
            result["residual_vulnerable_steps"],
            ["tool_access_test"]
        )

        self.assertFalse(
            result["mitigation_validation"]
        )

    def test_invalid_replay_result(self):

        with self.assertRaises(ValueError):

            build_mitigation_experiment_record(
                {
                    "status": "failed"
                }
            )


if __name__ == "__main__":
    unittest.main()