import unittest

from sandbox.validator.chain_validator import ChainValidator


class TestChainValidator(unittest.TestCase):

    def setUp(self):
        self.validator = ChainValidator("EXP001")

    # -------------------------------------------------------------
    # Test 1: Valid complete chain
    # -------------------------------------------------------------

    def test_valid_chain(self):
        result = self.validator.validate_chain(
            "CHAIN001",
            [
                "permission_test",
                "tool_access_test",
                "memory_access_test"
            ]
        )

        self.assertEqual(result["status"], "validated")
        self.assertEqual(result["validated_steps"], 3)
        self.assertEqual(result["total_steps"], 3)

    # -------------------------------------------------------------
    # Test 2: Invalid test in chain
    # -------------------------------------------------------------

    def test_invalid_test_in_chain(self):
        result = self.validator.validate_chain(
            "CHAIN002",
            [
                "permission_test",
                "unknown_test"
            ]
        )

        self.assertEqual(result["status"], "invalid")
        self.assertEqual(result["validated_steps"], 1)
        self.assertEqual(result["total_steps"], 2)

    # -------------------------------------------------------------
    # Test 3: Expected finding is recorded
    # -------------------------------------------------------------

    def test_expected_finding_is_recorded(self):
        result = self.validator.validate_chain(
            "CHAIN003",
            ["tool_access_test"]
        )

        step = result["steps"][0]

        self.assertEqual(
            step["finding"],
            "unsafe_tool_access"
        )

        self.assertEqual(
            step["expected_finding"],
            "unsafe_tool_access"
        )

        self.assertTrue(
            step["finding_matches"]
        )

    # -------------------------------------------------------------
    # Test 4: Evidence is recorded
    # -------------------------------------------------------------

    def test_evidence_is_recorded(self):
        result = self.validator.validate_chain(
            "CHAIN004",
            ["permission_test"]
        )

        step = result["steps"][0]

        self.assertTrue(
            step["evidence_exists"]
        )

        self.assertIsNotNone(
            step["evidence"]
        )

    # -------------------------------------------------------------
    # Test 5: Empty chain
    # -------------------------------------------------------------

    def test_empty_chain(self):
        result = self.validator.validate_chain(
            "CHAIN005",
            []
        )

        self.assertEqual(
            result["status"],
            "invalid"
        )

        self.assertEqual(
            result["validated_steps"],
            0
        )

    # -------------------------------------------------------------
    # Test 6: Tests must be a list
    # -------------------------------------------------------------

    def test_non_list_chain(self):
        result = self.validator.validate_chain(
            "CHAIN006",
            "permission_test"
        )

        self.assertEqual(
            result["status"],
            "invalid"
        )

        self.assertEqual(
            result["validated_steps"],
            0
        )

    # -------------------------------------------------------------
    # Test 7: Empty test name
    # -------------------------------------------------------------

    def test_empty_test_name(self):
        result = self.validator.validate_chain(
            "CHAIN007",
            [""]
        )

        self.assertEqual(
            result["status"],
            "invalid"
        )

        self.assertEqual(
            result["validated_steps"],
            0
        )

    # -------------------------------------------------------------
    # Day 6 dependency test 1:
    # Valid dependency order
    # -------------------------------------------------------------

    def test_valid_chain_dependencies(self):
        result = self.validator.validate_chain(
            "CHAIN_DEP_001",
            [
                "permission_test",
                "tool_access_test",
                "memory_access_test"
            ]
        )

        self.assertEqual(
            result["status"],
            "validated"
        )

        self.assertEqual(
            result["validated_steps"],
            3
        )

        self.assertEqual(
            result["total_steps"],
            3
        )

        for step in result["steps"]:
            self.assertTrue(
                step["dependency_valid"]
            )

    # -------------------------------------------------------------
    # Day 6 dependency test 2:
    # Invalid dependency order
    # -------------------------------------------------------------

    def test_invalid_chain_dependencies(self):
        result = self.validator.validate_chain(
            "CHAIN_DEP_002",
            [
                "tool_access_test",
                "permission_test"
            ]
        )

        self.assertEqual(
            result["status"],
            "invalid"
        )

        first_step = result["steps"][0]

        self.assertFalse(
            first_step["dependency_valid"]
        )

        self.assertIn(
            "requires: permission_test",
            first_step["dependency_error"]
        )


if __name__ == "__main__":
    unittest.main()