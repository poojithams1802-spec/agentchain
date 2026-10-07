"""
Phase 3 P3 -> P4 adaptive test execution boundary.

P3 is responsible for selecting the next test.
P4 is responsible for validating that the selected test
is sandbox-approved and then executing it.

No planner/scoring logic belongs in this module.
"""

from .sandbox_executor import (
    ALLOWED_TESTS,
    execute_sandbox_test,
)


def validate_selected_test(selected_test):
    """
    Validate a planner-selected test against the
    P4-approved sandbox test registry.

    Args:
        selected_test (str): Test selected by P3.

    Returns:
        dict: Validation result.
    """

    if not selected_test:
        return {
            "valid": False,
            "selected_test": selected_test,
            "error": "selected_test is required.",
        }

    if not isinstance(selected_test, str):
        return {
            "valid": False,
            "selected_test": selected_test,
            "error": "selected_test must be a string.",
        }

    if selected_test not in ALLOWED_TESTS:
        return {
            "valid": False,
            "selected_test": selected_test,
            "error": f"Test is not sandbox-approved: {selected_test}",
        }

    return {
        "valid": True,
        "selected_test": selected_test,
        "error": None,
    }


def execute_selected_test(
    experiment_id,
    selected_test,
):
    """
    Validate and execute a P3-selected sandbox test.

    The underlying sandbox execution contract remains unchanged.

    Args:
        experiment_id (str): Experiment identifier.
        selected_test (str): Test selected by P3.

    Returns:
        dict: Structured adaptive test execution result.
    """

    validation = validate_selected_test(
        selected_test
    )

    if not validation["valid"]:
        return {
            "status": "rejected",
            "experiment_id": experiment_id,
            "selected_test": selected_test,
            "validation": validation,
            "executed": False,
            "result": None,
            "execution_cost": None,
        }

    if not experiment_id:
        return {
            "status": "failed",
            "experiment_id": experiment_id,
            "selected_test": selected_test,
            "validation": validation,
            "executed": False,
            "result": {
                "status": "failed",
                "test": selected_test,
                "finding": None,
                "severity": None,
                "evidence": "experiment_id is required.",
            },
            "execution_cost": None,
        }

    result = execute_sandbox_test(
        experiment_id,
        selected_test,
    )

    return {
        "status": result.get("status"),
        "experiment_id": experiment_id,
        "selected_test": selected_test,
        "validation": validation,
        "executed": result.get("status") == "completed",
        "result": result,
        "execution_cost": result.get("execution_cost"),
    }