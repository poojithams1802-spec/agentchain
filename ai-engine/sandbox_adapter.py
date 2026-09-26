from typing import Any

from integration import build_sandbox_execution_request
from schemas import PlannerDecision


REQUIRED_RESPONSE_FIELDS = {
    "status",
    "test",
    "finding",
    "severity",
    "evidence",
}

VALID_STATUSES = {
    "completed",
    "failed",
}


def execute_planned_test(
    decision: PlannerDecision,
    experiment_id: str,
) -> dict[str, Any]:
    """
    Execute the test selected by the planner through
    Person 4's sandbox executor.

    Person 2 supplies experiment_id.
    Person 3 supplies the planner decision.
    Person 4 performs the actual sandbox execution.
    """

    request = build_sandbox_execution_request(
        decision,
        experiment_id,
    )

    # Import only when execution is requested so the AI engine
    # remains independently testable.
    from execution.sandbox_executor import execute_sandbox_test

    result = execute_sandbox_test(
        request["experiment_id"],
        request["test"],
    )

    return validate_sandbox_response(result)


def validate_sandbox_response(
    response: dict[str, Any],
) -> dict[str, Any]:
    """
    Validate the response returned by Person 4's sandbox executor.
    """

    if not isinstance(response, dict):
        raise ValueError(
            "Sandbox executor must return a dictionary."
        )

    missing_fields = REQUIRED_RESPONSE_FIELDS - response.keys()

    if missing_fields:
        raise ValueError(
            f"Sandbox response is missing fields: "
            f"{sorted(missing_fields)}"
        )

    if response["status"] not in VALID_STATUSES:
        raise ValueError(
            f"Invalid sandbox status: {response['status']}"
        )

    if response["status"] == "failed":
        if response["finding"] is not None:
            raise ValueError(
                "Failed sandbox response must have finding=None."
            )

        if response["severity"] is not None:
            raise ValueError(
                "Failed sandbox response must have severity=None."
            )

    return response