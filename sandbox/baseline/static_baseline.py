from ..execution.sandbox_executor import execute_sandbox_test


STATIC_TEST_SEQUENCE = [
    "permission_test",
    "tool_access_test",
    "memory_access_test",
]


def run_static_baseline(experiment_id):
    """
    Execute the predefined static testing sequence.

    Unlike the adaptive planner, this baseline does not
    choose the next test based on previous findings.
    """

    if not experiment_id:
        return {
            "status": "failed",
            "experiment_id": experiment_id,
            "tests": [],
            "findings": [],
            "total_tests": 0,
            "total_findings": 0,
            "error": "experiment_id is required."
        }

    results = []

    for test_name in STATIC_TEST_SEQUENCE:

        result = execute_sandbox_test(
            experiment_id,
            test_name
        )

        results.append(result)

    findings = [
        result["finding"]
        for result in results
        if result["status"] == "completed"
        and result["finding"] is not None
    ]

    return {
        "status": "completed",
        "experiment_id": experiment_id,
        "tests": results,
        "findings": findings,
        "total_tests": len(results),
        "total_findings": len(findings)
    }