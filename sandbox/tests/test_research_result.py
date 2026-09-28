import unittest

from sandbox.evaluation.research_result import (
    create_research_result
)


class TestResearchResult(unittest.TestCase):

    def test_adaptive_research_result(self):

        result = create_research_result(
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
            result["llm_calls"],
            3
        )

        self.assertTrue(
            result["fallback_used"]
        )

        self.assertEqual(
            len(result["executed_tests"]),
            3
        )

    def test_invalid_mode(self):

        with self.assertRaises(ValueError):
            create_research_result(
                experiment_id="TEST",
                mode="unknown",
                executed_tests=[],
                findings=[],
                candidate_chains=[],
                validated_chains=[],
                average_chain_length=0.0,
                validation_rate=0.0,
                execution_count=0
            )


if __name__ == "__main__":
    unittest.main()