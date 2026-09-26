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


if __name__ == "__main__":
    unittest.main()