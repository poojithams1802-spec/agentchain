from ..test_runner import run_test
from ..mitigation.mitigation_state import is_mitigation_active


ALLOWED_TESTS = {
    "permission_test",
    "tool_access_test",
    "memory_access_test",
}


# Maps each security test to its corresponding defensive control.
TEST_MITIGATION_MAP = {
    "permission_test": "authorization_gate",
    "tool_access_test": "tool_allowlist",
    "memory_access_test": "memory_validation",
}


def execute_sandbox_test(experiment_id, test_name):
    """
    Execute one controlled sandbox test.

    The experiment_id identifies the experiment.
    The test_name identifies which deterministic sandbox
    scenario should be executed.

    If the corresponding mitigation is active for the
    experiment, the vulnerable result is converted into
    a blocked/validated result.
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

    # Run the original deterministic vulnerability scenario.
    result = run_test(test_name)

    # Find the defensive control associated with this test.
    mitigation_control = TEST_MITIGATION_MAP.get(test_name)

    # Check whether that control is active for this experiment.
    mitigation_active = (
        mitigation_control is not None
        and is_mitigation_active(
            experiment_id,
            mitigation_control
        )
    )

    # No mitigation is active.
    # Return the original Phase 1 result unchanged.
    if not mitigation_active:
        return result

    # ---------------------------------------------------------
    # Mitigation is active.
    # Convert the vulnerable result into a protected result.
    # ---------------------------------------------------------

    return {
        "status": "completed",
        "test": test_name,
        "finding": result["finding"],
        "severity": result["severity"],
        "evidence": {
            "original": result["evidence"],
            "mitigation": mitigation_control,
            "mitigation_status": "active",
            "result": "attack_blocked"
        },
        "confidence": 1.0,
        "mitigation_applied": True,
        "mitigation_control": mitigation_control,
    }