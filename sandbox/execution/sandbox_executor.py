from time import perf_counter

from ..test_runner import run_test
from ..mitigation.mitigation_state import is_mitigation_active

ALLOWED_TESTS = {
    "permission_test",
    "tool_access_test",
    "memory_access_test",
    "prompt_injection_test",
    "indirect_prompt_injection_test",
    "sensitive_data_test",
    "file_operation_test",
    "context_manipulation_test",
    "privilege_propagation_test",
    "unsafe_delegation_test",
    "cross_agent_trust_test",
    "tool_parameter_validation_test",
}



# Maps each security test to its corresponding defensive control.
TEST_MITIGATION_MAP = {
    "permission_test": "authorization_gate",
    "tool_access_test": "tool_allowlist",
    "memory_access_test": "memory_validation",
    "sensitive_data_test": "sensitive_data_exposure",
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

    Phase 3:
    Execution-cost metadata is recorded for each test execution.
    """

    # ---------------------------------------------------------
    # 1. Validate experiment ID
    # ---------------------------------------------------------
    if not experiment_id:
        return {
            "status": "failed",
            "test": test_name,
            "finding": None,
            "severity": None,
            "evidence": "experiment_id is required.",
            "confidence": 0.0,  # Added for P3 adapter contract
        }

    # ---------------------------------------------------------
    # 2. Validate the requested sandbox test
    # ---------------------------------------------------------
    if test_name not in ALLOWED_TESTS:
        return {
            "status": "failed",
            "test": test_name,
            "finding": None,
            "severity": None,
            "evidence": f"Unknown test: {test_name}",
            "confidence": 0.0,  # Added for P3 adapter contract
        }

    # ---------------------------------------------------------
    # 3. Execute the deterministic vulnerability scenario
    # ---------------------------------------------------------
    start_time = perf_counter()

    result = run_test(test_name)

    execution_time_seconds = perf_counter() - start_time

    execution_cost = {
        "test_count": 1,
        "execution_time_seconds": execution_time_seconds,
    }

    # Copy the result before attaching execution metadata.
    result = dict(result)
    result["execution_cost"] = execution_cost

    # ---------------------------------------------------------
    # 4. Find the defensive control associated with this test
    # ---------------------------------------------------------
    mitigation_control = TEST_MITIGATION_MAP.get(test_name)

    # ---------------------------------------------------------
    # 5. Check whether the corresponding mitigation is active
    # ---------------------------------------------------------
    mitigation_active = (
        mitigation_control is not None
        and is_mitigation_active(
            experiment_id,
            mitigation_control,
        )
    )

    # ---------------------------------------------------------
    # 6. Return the original result when no mitigation is active
    # ---------------------------------------------------------
    if not mitigation_active:
        return result

    # ---------------------------------------------------------
    # 7. Return the protected result when mitigation is active
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
            "result": "attack_blocked",
        },
        "confidence": 1.0,
        "mitigation_applied": True,
        "mitigation_control": mitigation_control,

        # Phase 3 execution-cost metadata
        "execution_cost": result["execution_cost"],
    }
    return {
        "status": "completed",
        "test": test_name,
        "finding": result["finding"],
        "severity": result["severity"],
        "evidence": {
            "original": result["evidence"],
            "mitigation": mitigation_control,
            "mitigation_status": "active",
            "result": "attack_blocked",
        },
        "confidence": 1.0,
        "mitigation_applied": True,
        "mitigation_control": mitigation_control,

        # Phase 3 execution-cost metadata
        "execution_cost": result["execution_cost"],
    }