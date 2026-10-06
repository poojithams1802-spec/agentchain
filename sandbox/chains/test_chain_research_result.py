import unittest
from unittest.mock import patch

from .chain_executor import (
    execute_chain,
    chain_result_to_research_result,
    execute_chain_as_research_result,
)


class TestChainResearchResult(unittest.TestCase):

    def test_two_step_chain_research_result(self):
        chain_result = execute_chain(
            "DAY3-RESEARCH-001",
            "CHAIN-AUTH-TOOL",
        )

        result = chain_result_to_research_result(
            chain_result
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
            result["validated_chains"],
            ["CHAIN-AUTH-TOOL"],
        )

    def test_three_step_chain_research_result(self):
        chain_result = execute_chain(
            "DAY3-RESEARCH-002",
            "CHAIN-AUTH-TOOL-MEM",
        )

        result = chain_result_to_research_result(
            chain_result
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

    def test_conversion_helper_does_not_execute_chain(self):
        chain_result = {
            "status": "validated",
            "experiment_id": "DAY3-CONVERSION-001",
            "chain_id": "CHAIN-AUTH-TOOL",
            "name": "Authorization to Tool Access",
            "description": "Test chain",
            "steps": [
                {
                    "test": "permission_test",
                    "finding": "weak_permission_control",
                },
                {
                    "test": "tool_access_test",
                    "finding": "unsafe_tool_access",
                },
            ],
            "chain_length": 2,
            "validated_steps": 2,
            "total_steps": 2,
            "validation_rate": 1.0,
            "all_findings_reproduced": True,
            "error": None,
        }

        with patch(
            "sandbox.chains.chain_executor.execute_chain"
        ) as mocked_execute:

            result = chain_result_to_research_result(
                chain_result
            )

            mocked_execute.assert_not_called()

        self.assertEqual(
            result["chain_id"],
            "CHAIN-AUTH-TOOL",
        )

        self.assertEqual(
            result["chain_length"],
            2,
        )

    def test_backward_compatible_helper_executes_once(self):
        with patch(
            "sandbox.chains.chain_executor.execute_chain"
        ) as mocked_execute:

            mocked_execute.return_value = {
                "status": "validated",
                "experiment_id": "DAY3-COMPAT-001",
                "chain_id": "CHAIN-AUTH-TOOL",
                "name": "Authorization to Tool Access",
                "description": "Test chain",
                "steps": [
                    {
                        "test": "permission_test",
                        "finding": "weak_permission_control",
                    },
                    {
                        "test": "tool_access_test",
                        "finding": "unsafe_tool_access",
                    },
                ],
                "chain_length": 2,
                "validated_steps": 2,
                "total_steps": 2,
                "validation_rate": 1.0,
                "all_findings_reproduced": True,
                "error": None,
            }

            result = execute_chain_as_research_result(
                "DAY3-COMPAT-001",
                "CHAIN-AUTH-TOOL",
            )

            mocked_execute.assert_called_once_with(
                "DAY3-COMPAT-001",
                "CHAIN-AUTH-TOOL",
            )

        self.assertEqual(
            result["chain_id"],
            "CHAIN-AUTH-TOOL",
        )

        self.assertEqual(
            result["validated_steps"],
            2,
        )


if __name__ == "__main__":
    unittest.main()