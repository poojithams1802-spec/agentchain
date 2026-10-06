import unittest

from .chain_executor import execute_chain_as_research_result


class TestChainResearchResult(unittest.TestCase):

    def test_two_step_chain_research_result(self):
        result = execute_chain_as_research_result(
            "DAY3-RESEARCH-001",
            "CHAIN-AUTH-TOOL",
        )

        self.assertEqual(
            result["experiment_id"],
            "DAY3-RESEARCH-001",
        )

        self.assertEqual(
            result["chain_id"],
            "CHAIN-AUTH-TOOL",
        )

        self.assertEqual(
            result["chain_name"],
            "Authorization to Tool Access",
        )

        self.assertEqual(
            result["chain_steps"],
            [
                "permission_test",
                "tool_access_test",
            ],
        )

        self.assertEqual(
            result["chain_length"],
            2,
        )

        self.assertEqual(
            result["validated_steps"],
            2,
        )

        self.assertEqual(
            result["chain_validation_rate"],
            1.0,
        )

        self.assertTrue(
            result["all_findings_reproduced"]
        )

        self.assertEqual(
            result["chain_status"],
            "validated",
        )

        self.assertEqual(
            result["executed_tests"],
            [
                "permission_test",
                "tool_access_test",
            ],
        )

        self.assertEqual(
            result["findings"],
            [
                "weak_permission_control",
                "unsafe_tool_access",
            ],
        )

        self.assertEqual(
            result["validated_chains"],
            ["CHAIN-AUTH-TOOL"],
        )

    def test_three_step_chain_research_result(self):
        result = execute_chain_as_research_result(
            "DAY3-RESEARCH-002",
            "CHAIN-AUTH-TOOL-MEM",
        )

        self.assertEqual(
            result["chain_length"],
            3,
        )

        self.assertEqual(
            result["validated_steps"],
            3,
        )

        self.assertEqual(
            result["chain_validation_rate"],
            1.0,
        )

        self.assertTrue(
            result["all_findings_reproduced"]
        )

        self.assertEqual(
            result["chain_status"],
            "validated",
        )

        self.assertEqual(
            len(result["executed_tests"]),
            3,
        )

        self.assertEqual(
            len(result["findings"]),
            3,
        )


if __name__ == "__main__":
    unittest.main()