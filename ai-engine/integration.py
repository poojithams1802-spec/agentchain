from pydantic import ValidationError

from schemas import PlannerDecision, SandboxTestRequest


def decision_to_sandbox_request(
    decision: PlannerDecision,
) -> SandboxTestRequest:
    """
    Convert a validated planner decision into a sandbox test request.

    This function does not execute the test. It only validates
    and converts the selected test name into the request schema.
    """

    try:
        request = SandboxTestRequest(
            test=decision.selected_test
        )
    except ValidationError as error:
        raise ValueError(
            f"Planner selected an invalid sandbox test: "
            f"{decision.selected_test}"
        ) from error

    return request