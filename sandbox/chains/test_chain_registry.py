import unittest

from .chain_definitions import CHAIN_DEFINITIONS
from .chain_registry import (
    get_all_chains,
    get_chain,
    register_chain,
    validate_chain_definition,
)


class TestChainRegistry(unittest.TestCase):

    def test_existing_chain_definitions_are_valid(self):
        for chain_id, chain in CHAIN_DEFINITIONS.items():

            valid, error = validate_chain_definition(chain)

            self.assertTrue(
                valid,
                msg=f"{chain_id} should be valid: {error}",
            )

    def test_auth_tool_chain(self):
        chain = get_chain("CHAIN-AUTH-TOOL")

        self.assertIsNotNone(chain)
        self.assertEqual(
            chain["steps"],
            [
                "permission_test",
                "tool_access_test",
            ],
        )

    def test_auth_tool_memory_chain(self):
        chain = get_chain("CHAIN-AUTH-TOOL-MEM")

        self.assertIsNotNone(chain)
        self.assertEqual(
            chain["steps"],
            [
                "permission_test",
                "tool_access_test",
                "memory_access_test",
            ],
        )

    def test_unknown_chain_returns_none(self):
        self.assertIsNone(
            get_chain("CHAIN-DOES-NOT-EXIST")
        )

    def test_invalid_unknown_test(self):
        invalid_chain = {
            "chain_id": "CHAIN-INVALID",
            "name": "Invalid Chain",
            "description": "Test invalid sandbox step.",
            "steps": [
                "permission_test",
                "unknown_test",
            ],
            "dependencies": {
                "permission_test": [],
                "unknown_test": [
                    "permission_test",
                ],
            },
        }

        valid, error = validate_chain_definition(invalid_chain)

        self.assertFalse(valid)
        self.assertIn(
            "Unsupported sandbox test",
            error,
        )

    def test_dependency_order_is_required(self):
        invalid_chain = {
            "chain_id": "CHAIN-WRONG-ORDER",
            "name": "Wrong Order",
            "description": "Dependency order should fail.",
            "steps": [
                "tool_access_test",
                "permission_test",
            ],
            "dependencies": {
                "permission_test": [],
                "tool_access_test": [
                    "permission_test",
                ],
            },
        }

        valid, error = validate_chain_definition(invalid_chain)

        self.assertFalse(valid)
        self.assertIn(
            "requires earlier step",
            error,
        )

    def test_register_chain(self):
        chain = {
            "chain_id": "CHAIN-TEST-REGISTER",
            "name": "Registry Test Chain",
            "description": "Temporary registry test.",
            "steps": [
                "permission_test",
            ],
            "dependencies": {
                "permission_test": [],
            },
        }

        registered = register_chain(chain)

        self.assertEqual(
            registered["chain_id"],
            "CHAIN-TEST-REGISTER",
        )

        fetched = get_chain("CHAIN-TEST-REGISTER")

        self.assertIsNotNone(fetched)
        self.assertEqual(
            fetched["steps"],
            ["permission_test"],
        )
    def test_validator_first_import_has_no_cycle(self):
        """The validator must import cleanly before the chain executor."""
        import subprocess
        import sys

        result = subprocess.run(
            [
                sys.executable,
                "-c",
                (
                    "from sandbox.validator.chain_validator import ChainValidator; "
                    "from sandbox.chains.chain_executor import execute_chain; "
                    "print(ChainValidator.__name__, execute_chain.__name__)"
                ),
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("ChainValidator execute_chain", result.stdout)

if __name__ == "__main__":
    unittest.main()