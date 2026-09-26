from ..test_runner import run_test


ALLOWED_TESTS = {
    "permission_test",
    "tool_access_test",
    "memory_access_test",
}


def execute_sandbox_test(experiment_id, test_name):
    """
    Execute one controlled sandbox test.

    The experiment_id identifies the experiment.
    The test_name identifies which deterministic sandbox
    scenario should be executed.
    """

    if not experiment_id:
        return {
            "status": "failed",
            "test": test_name,
            "finding": None,
            "severity": None,
            "evidence": "experiment_id is required.",
        }

    if test_name not in ALLOWED_TESTS:
        return {
            "status": "failed",
            "test": test_name,
            "finding": None,
            "severity": None,
            "evidence": f"Unknown test: {test_name}",
        }

    result = run_test(test_name)

    return result