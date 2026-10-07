from ..execution.sandbox_executor import execute_sandbox_test
from ..validator.chain_validator import ChainValidator


STATIC_TEST_SEQUENCE = [
    "permission_test",
    "tool_access_test",
    "memory_access_test",
]


def run_static_baseline(experiment_id):
    """
    Execute the predefined static testing sequence.

    The static baseline does not use the adaptive planner.
    It follows a fixed sequence of allowed sandbox tests.
    """

    if not experiment_id:
        return {
            "status": "failed",
            "experiment_id": experiment_id,
            "tests": [],
            "findings": [],
            "total_tests": 0,
            "total_findings": 0,
            "average_confidence": 0.0,
            "test_sequence": [],
            "execution_cost": {
                "test_count": 0,
                "execution_time_seconds": 0.0,
            },
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

    confidences = [
        result["confidence"]
        for result in results
        if result["status"] == "completed"
    ]

    average_confidence = (
        sum(confidences) / len(confidences)
        if confidences
        else 0.0
    )

    # Aggregate execution cost from all executed tests.
    total_execution_time = sum(
        result.get("execution_cost", {}).get(
            "execution_time_seconds", 0.0
        )
        for result in results
        if isinstance(result.get("execution_cost"), dict)
    )

    execution_cost = {
        "test_count": len(results),
        "execution_time_seconds": total_execution_time,
    }

    return {
        "status": "completed",
        "experiment_id": experiment_id,
        "tests": results,
        "findings": findings,
        "total_tests": len(results),
        "total_findings": len(findings),
        "average_confidence": average_confidence,
        "test_sequence": STATIC_TEST_SEQUENCE.copy(),
        "execution_cost": execution_cost,
    }


def validate_static_chain(experiment_id, chain_id):
    """
    Execute the static baseline and validate the resulting
    fixed test sequence using the shared ChainValidator.
    """

    baseline_result = run_static_baseline(experiment_id)

    if baseline_result["status"] != "completed":
        return {
            "status": "failed",
            "experiment_id": experiment_id,
            "chain_id": chain_id,
            "baseline": baseline_result,
            "validation": None
        }

    candidate_chain = baseline_result["test_sequence"]

    validator = ChainValidator(experiment_id)

    validation_result = validator.validate_chain(
        chain_id,
        candidate_chain
    )

    return {
        "status": "completed",
        "experiment_id": experiment_id,
        "chain_id": chain_id,
        "baseline": baseline_result,
        "candidate_chain": candidate_chain,
        "validation": validation_result
    }