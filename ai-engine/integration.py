from pydantic import ValidationError

from schemas import PlannerDecision, SandboxTestRequest


def decision_to_sandbox_request(
    decision: PlannerDecision,
) -> SandboxTestRequest:
    """
    Convert a validated planner decision into a sandbox test request.

    This function does not execute the test. It only validates
    and converts the selected test name into the internal
    Person 3 sandbox request model.
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


def build_sandbox_execution_request(
    decision: PlannerDecision,
    experiment_id: str,
) -> dict[str, str]:
    """
    Build the frozen shared contract for Person 4's sandbox executor.

    Person 2 is responsible for generating experiment_id.
    Person 3 only passes it through together with the selected test.
    """

    if not experiment_id or not experiment_id.strip():
        raise ValueError("experiment_id must not be empty.")

    request = decision_to_sandbox_request(decision)

    return {
        "experiment_id": experiment_id,
        "test": request.test,
    }