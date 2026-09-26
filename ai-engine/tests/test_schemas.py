from schemas import ExperimentRequest
import pytest
from pydantic import ValidationError

from schemas import SandboxTestRequest, SandboxTestResponse


def test_sandbox_request_accepts_permission_test():
    request = SandboxTestRequest(test="permission_test")

    assert request.test == "permission_test"


def test_sandbox_request_accepts_tool_access_test():
    request = SandboxTestRequest(test="tool_access_test")

    assert request.test == "tool_access_test"


def test_sandbox_request_accepts_memory_access_test():
    request = SandboxTestRequest(test="memory_access_test")

    assert request.test == "memory_access_test"


def test_sandbox_request_rejects_unknown_test():
    with pytest.raises(ValidationError):
        SandboxTestRequest(test="unknown_test")


def test_sandbox_response_accepts_completed_response():
    response = SandboxTestResponse(
        status="completed",
        test="tool_access_test",
        finding="unsafe_tool_access",
        severity="high",
        evidence="Controlled permission boundary was exceeded",
    )

    assert response.status == "completed"
    assert response.test == "tool_access_test"


def test_sandbox_response_accepts_failed_response():
    response = SandboxTestResponse(
        status="failed",
        test="unknown_test",
        finding="",
        severity="unknown",
        evidence="Invalid test name",
    )

    assert response.status == "failed"
    assert response.test == "unknown_test"

def test_experiment_request_accepts_valid_data():
    request = ExperimentRequest(
        experiment_id="EXP001",
        test="tool_access_test",
    )

    assert request.experiment_id == "EXP001"
    assert request.test == "tool_access_test"


def test_experiment_request_rejects_empty_experiment_id():
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        ExperimentRequest(
            experiment_id="",
            test="tool_access_test",
        )


def test_experiment_request_rejects_empty_test():
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        ExperimentRequest(
            experiment_id="EXP001",
            test="",
        )