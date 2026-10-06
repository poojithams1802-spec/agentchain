import unittest

from .chain_executor import execute_chain


class TestChainExecutor(unittest.TestCase):

    def test_execute_two_step_chain(self):
        result = execute_chain(
            "PHASE3-DAY2-AUTH-TOOL",
            "CHAIN-AUTH-TOOL",
        )

        self.assertEqual(
            result["status"],
            "validated",
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
            result["validated_steps"],
            2,
        )

        self.assertEqual(
            result["total_steps"],
            2,
        )

        self.assertEqual(
            result["validation_rate"],
            1.0,
        )

        self.assertTrue(
            result["all_findings_reproduced"]
        )

        self.assertEqual(
            len(result["steps"]),
            2,
        )

    def test_execute_three_step_chain(self):
        result = execute_chain(
            "PHASE3-DAY2-AUTH-TOOL-MEM",
            "CHAIN-AUTH-TOOL-MEM",
        )

        self.assertEqual(
            result["status"],
            "validated",
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
            result["validation_rate"],
            1.0,
        )

    def test_unknown_chain(self):
        result = execute_chain(
            "PHASE3-DAY2-UNKNOWN",
            "CHAIN-DOES-NOT-EXIST",
        )

        self.assertEqual(
            result["status"],
            "invalid",
        )

        self.assertIn(
            "Unknown chain",
            result["error"],
        )

    def test_missing_experiment_id(self):
        result = execute_chain(
            "",
            "CHAIN-AUTH-TOOL",
        )

        self.assertEqual(
            result["status"],
            "invalid",
        )

        self.assertEqual(
            result["error"],
            "experiment_id is required.",
        )

    def test_missing_chain_id(self):
        result = execute_chain(
            "PHASE3-DAY2-MISSING",
            "",
        )

        self.assertEqual(
            result["status"],
            "invalid",
        )

        self.assertEqual(
            result["error"],
            "chain_id is required.",
        )


if __name__ == "__main__":
    unittest.main()