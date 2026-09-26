import unittest

from sandbox.execution.sandbox_executor import execute_sandbox_test
from sandbox.validator.chain_validator import ChainValidator


class TestDay7Integration(unittest.TestCase):

    def setUp(self):
        self.experiment_id = "EXP_DAY7"

    def test_sandbox_finding_to_validation(self):

        # Step 1: execute first security test
        first_result = execute_sandbox_test(
            self.experiment_id,
            "permission_test"
        )

        self.assertEqual(
            first_result["status"],
            "completed"
        )

        self.assertEqual(
            first_result["finding"],
            "weak_permission_control"
        )

        self.assertEqual(
            first_result["confidence"],
            1.0
        )

        # Step 2: execute second security test
        second_result = execute_sandbox_test(
            self.experiment_id,
            "tool_access_test"
        )

        self.assertEqual(
            second_result["status"],
            "completed"
        )

        self.assertEqual(
            second_result["finding"],
            "unsafe_tool_access"
        )

        self.assertEqual(
            second_result["confidence"],
            1.0
        )

        # Step 3: construct candidate chain
        candidate_chain = [
            "permission_test",
            "tool_access_test"
        ]

        # Step 4: validate candidate chain
        validator = ChainValidator(
            self.experiment_id
        )

        validation = validator.validate_chain(
            "CHAIN_DAY7",
            candidate_chain
        )

        # Step 5: verify validation result
        self.assertEqual(
            validation["status"],
            "validated"
        )

        self.assertEqual(
            validation["validated_steps"],
            2
        )

        self.assertEqual(
            validation["total_steps"],
            2
        )


if __name__ == "__main__":
    unittest.main()