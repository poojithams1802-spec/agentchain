import unittest

from sandbox.baseline.static_baseline import run_static_baseline


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


if __name__ == "__main__":
    unittest.main()