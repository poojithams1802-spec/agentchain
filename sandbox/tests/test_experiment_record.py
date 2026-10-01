import unittest

from sandbox.evaluation.experiment_record import (
    record_experiment_result
)


class TestExperimentRecord(unittest.TestCase):

    def test_exp008_record(self):

        result = record_experiment_result(
            experiment_id="EXP008",
            mode="adaptive",
            executed_tests=[
                "tool_access_test",
                "memory_access_test",
                "permission_test"
            ],
            findings=[
                "unsafe_tool_access",
                "memory_validation_weakness",
                "weak_permission_control"
            ],
            candidate_chains=[
                "CHAIN-d2a39833"
            ],
            validated_chains=[],
            average_chain_length=3.0,
            validation_rate=0.3333,
            execution_count=3,
            llm_calls=3,
            fallback_used=True
        )

        self.assertEqual(
            result["experiment_id"],
            "EXP008"
        )

        self.assertEqual(
            result["mode"],
            "adaptive"
        )

        self.assertEqual(
            result["execution_count"],
            3
        )

        self.assertEqual(
            result["validation_rate"],
            0.3333
        )

        self.assertEqual(
            result["candidate_chains"],
            ["CHAIN-d2a39833"]
        )

        self.assertEqual(
            result["validated_chains"],
            []
        )

        self.assertEqual(
            result["llm_calls"],
            3
        )

        self.assertTrue(
            result["fallback_used"]
        )
        def test_phase2_mitigation_record(self):

            result = record_experiment_result(
                experiment_id="EXP-P2-001",
                mode="adaptive",
                executed_tests=[
                    "permission_test"
                ],
                findings=[
                    "weak_permission_control"
                ],
                candidate_chains=[
                    "CHAIN-001"
                ],
                validated_chains=[
                    "CHAIN-001"
                ],
                average_chain_length=1.0,
                validation_rate=1.0,
                execution_count=1,
                llm_calls=1,
                fallback_used=False,

                mitigation_control="authorization_gate",
                mitigation_selected=True,
                mitigation_applied=True,
                attack_success_before=True,
                attack_success_after=False,
                chain_disrupted=True,
                residual_vulnerable_steps=[],
                mitigation_validation=True
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

if __name__ == "__main__":
    unittest.main()