import unittest

from sandbox.mitigation.authorization_gate import (
    check_authorization
)

from sandbox.mitigation.mitigation_executor import (
    apply_mitigation
)


class TestAuthorizationGate(unittest.TestCase):

    def test_denied_permission_blocks_operation(self):

        result = check_authorization(
            "DENIED",
            "GRANTED"
        )

        self.assertFalse(result["allowed"])
        self.assertEqual(
            result["status"],
            "blocked"
        )

    def test_granted_permission_allows_operation(self):

        result = check_authorization(
            "GRANTED",
            "GRANTED"
        )

        self.assertTrue(result["allowed"])
        self.assertEqual(
            result["status"],
            "allowed"
        )

    def test_authorization_gate_in_executor(self):

        result = apply_mitigation(
            experiment_id="EXP011",
            control_name="authorization_gate",
            permission="DENIED",
            required_permission="GRANTED"
        )

        self.assertEqual(
            result["status"],
            "applied"
        )

        self.assertFalse(
            result["allowed"]
        )

        self.assertEqual(
            result["target"],
            "weak_permission_control"
        )


if __name__ == "__main__":
    unittest.main()