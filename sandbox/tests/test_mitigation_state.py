import unittest

from sandbox.mitigation.mitigation_state import (
    activate_mitigation,
    is_mitigation_active,
    get_active_mitigations,
    reset_mitigations,
)


class TestMitigationState(unittest.TestCase):

    def setUp(self):
        reset_mitigations("test_exp")

    def test_activate_mitigation(self):
        result = activate_mitigation(
            "test_exp",
            "authorization_gate"
        )

        self.assertEqual(result["status"], "activated")
        self.assertTrue(
            is_mitigation_active(
                "test_exp",
                "authorization_gate"
            )
        )

    def test_experiment_isolation(self):
        activate_mitigation(
            "test_exp",
            "authorization_gate"
        )

        self.assertTrue(
            is_mitigation_active(
                "test_exp",
                "authorization_gate"
            )
        )

        self.assertFalse(
            is_mitigation_active(
                "another_exp",
                "authorization_gate"
            )
        )

    def test_get_active_mitigations(self):
        activate_mitigation(
            "test_exp",
            "authorization_gate"
        )

        activate_mitigation(
            "test_exp",
            "tool_allowlist"
        )

        controls = get_active_mitigations("test_exp")

        self.assertEqual(
            controls,
            [
                "authorization_gate",
                "tool_allowlist"
            ]
        )

    def test_reset_mitigations(self):
        activate_mitigation(
            "test_exp",
            "authorization_gate"
        )

        reset_mitigations("test_exp")

        self.assertFalse(
            is_mitigation_active(
                "test_exp",
                "authorization_gate"
            )
        )

        self.assertEqual(
            get_active_mitigations("test_exp"),
            []
        )


if __name__ == "__main__":
    unittest.main()