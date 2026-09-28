import unittest

from sandbox.baseline.static_baseline import (
    run_static_baseline,
    validate_static_chain
)


class TestStaticBaseline(unittest.TestCase):

    def test_static_baseline_execution(self):

        result = run_static_baseline("STATIC_TEST")

        self.assertEqual(
            result["status"],
            "completed"
        )

        self.assertEqual(
            result["experiment_id"],
            "STATIC_TEST"
        )

        self.assertEqual(
            result["total_tests"],
            3
        )

        self.assertEqual(
            result["total_findings"],
            3
        )

    def test_static_test_order(self):

        result = run_static_baseline("STATIC_TEST")

        tests = [
            item["test"]
            for item in result["tests"]
        ]

        expected_order = [
            "permission_test",
            "tool_access_test",
            "memory_access_test"
        ]

        self.assertEqual(
            tests,
            expected_order
        )

    def test_static_findings(self):

        result = run_static_baseline("STATIC_TEST")

        expected_findings = [
            "weak_permission_control",
            "unsafe_tool_access",
            "memory_validation_weakness"
        ]

        self.assertEqual(
            result["findings"],
            expected_findings
        )

    def test_static_confidence(self):

        result = run_static_baseline("STATIC_TEST")

        for test_result in result["tests"]:

            self.assertEqual(
                test_result["confidence"],
                1.0
            )

    def test_static_research_metrics(self):

        result = run_static_baseline("STATIC_TEST")

        self.assertEqual(
            result["total_tests"],
            3
        )

        self.assertEqual(
            result["total_findings"],
            3
        )

        self.assertEqual(
            result["average_confidence"],
            1.0
        )

        self.assertEqual(
            result["test_sequence"],
            [
                "permission_test",
                "tool_access_test",
                "memory_access_test"
            ]
        )

    def test_static_chain_validation(self):

        result = validate_static_chain(
            "STATIC_TEST",
            "STATIC_CHAIN_TEST"
        )

        self.assertEqual(
            result["status"],
            "completed"
        )

        self.assertEqual(
            result["candidate_chain"],
            [
                "permission_test",
                "tool_access_test",
                "memory_access_test"
            ]
        )

        validation = result["validation"]

        self.assertEqual(
            validation["status"],
            "validated"
        )

        self.assertEqual(
            validation["validated_steps"],
            3
        )

        self.assertEqual(
            validation["total_steps"],
            3
        )

        self.assertEqual(
            validation["chain_length"],
            3
        )

        self.assertEqual(
            validation["validation_rate"],
            1.0
        )

        self.assertTrue(
            validation["all_findings_reproduced"]
        )


if __name__ == "__main__":
    unittest.main()