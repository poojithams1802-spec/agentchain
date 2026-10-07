from sandbox.evaluation.day7_experiment import (
    run_day7_experiment,
)


def test_day7_experiment_runner():
    adaptive_responses = [
        {
            "selected_test": "permission_test",
            "reason": "Check authorization first.",
            "priority": 0.9,
            "confidence": 0.9,
        },
        {
            "selected_test": "tool_access_test",
            "reason": "Follow the authorization finding.",
            "priority": 0.9,
            "confidence": 0.9,
        },
        {
            "selected_test": "memory_access_test",
            "reason": "Continue to the dependent memory step.",
            "priority": 0.8,
            "confidence": 0.9,
        },
    ]

    result = run_day7_experiment(
        adaptive_responses
    )

    assert result["status"] == "completed"

    comparison = result["comparison"]

    assert comparison["equal_test_budget"] is True
    assert comparison["test_budget"] == 3

    assert comparison["static"]["tests"] == 3
    assert comparison["adaptive"]["tests"] == 3

    assert comparison["static"]["findings"] == 3
    assert comparison["adaptive"]["findings"] == 3

    assert comparison["static"]["validated_chains"] == 1
    assert comparison["adaptive"]["validated_chains"] == 1

    assert comparison["static"]["llm_calls"] == 0
    assert comparison["adaptive"]["llm_calls"] == 3