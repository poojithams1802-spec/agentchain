import unittest

from validator.chain_validator import ChainValidator


class TestChainValidator(unittest.TestCase):

    def setUp(self):
        self.validator = ChainValidator("EXP001")

    def test_valid_chain(self):
        result = self.validator.validate_chain(
            "CHAIN001",
            [
                "permission_test",
                "tool_access_test",
                "memory_access_test"
            ]
        )

        self.assertEqual(result["chain_id"], "CHAIN001")
        self.assertEqual(result["status"], "validated")
        self.assertEqual(result["validated_steps"], 3)
        self.assertEqual(result["total_steps"], 3)

        for step in result["steps"]:
            self.assertTrue(step["valid"])
            self.assertTrue(step["finding_matches"])

    def test_invalid_test_in_chain(self):
        result = self.validator.validate_chain(
            "CHAIN002",
            [
                "permission_test",
                "invalid_test"
            ]
        )

        self.assertEqual(result["status"], "invalid")
        self.assertEqual(result["validated_steps"], 1)
        self.assertEqual(result["total_steps"], 2)

    def test_expected_finding_is_recorded(self):
        result = self.validator.validate_chain(
            "CHAIN003",
            ["tool_access_test"]
        )

        step = result["steps"][0]

        self.assertEqual(
            step["expected_finding"],
            "unsafe_tool_access"
        )

        self.assertEqual(
            step["finding"],
            "unsafe_tool_access"
        )

        self.assertTrue(step["finding_matches"])
        self.assertTrue(step["valid"])

    def test_evidence_is_recorded(self):
        result = self.validator.validate_chain(
            "CHAIN004",
            ["permission_test"]
        )

        step = result["steps"][0]

        self.assertTrue(step["evidence_exists"])
        self.assertTrue(step["valid"])
        self.assertIsNotNone(step["evidence"])

    def test_empty_chain_is_invalid(self):
        result = self.validator.validate_chain(
            "CHAIN005",
            []
        )

        self.assertEqual(result["status"], "invalid")
        self.assertEqual(result["validated_steps"], 0)
        self.assertEqual(result["total_steps"], 0)
        self.assertEqual(
            result["error"],
            "Attack chain must contain at least one test."
        )

    def test_non_list_chain_is_invalid(self):
        result = self.validator.validate_chain(
            "CHAIN006",
            "permission_test"
        )

        self.assertEqual(result["status"], "invalid")
        self.assertEqual(result["validated_steps"], 0)
        self.assertEqual(result["total_steps"], 0)
        self.assertEqual(
            result["error"],
            "tests must be a list."
        )

    def test_empty_test_name_is_invalid(self):
        result = self.validator.validate_chain(
            "CHAIN007",
            ["permission_test", ""]
        )

        self.assertEqual(result["status"], "invalid")
        self.assertEqual(result["validated_steps"], 0)
        self.assertEqual(result["total_steps"], 2)
        self.assertEqual(
            result["error"],
            "Every chain step must contain a valid test name."
        )


if __name__ == "__main__":
    unittest.main()