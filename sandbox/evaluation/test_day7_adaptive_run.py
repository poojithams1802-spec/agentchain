from sandbox.evaluation.day7_adaptive_run import (
    build_day7_adaptive_evaluation,
)


def test_day7_adaptive_result_is_consumed():
    adaptive_result = {
        "status": "completed",
        "selected_tests": [
            "permission_test",
            "tool_access_test",
            "memory_access_test",
        ],
        "execution_results": [
            {
                "status": "completed",
                "test": "permission_test",
                "finding": "weak_permission_control",
                "severity": "high",
                "evidence": {},
                "confidence": 1.0,
                "execution_cost": {
                    "test_count": 1,
                    "execution_time_seconds": 0.00001,
                },
            },
            {
                "status": "completed",
                "test": "tool_access_test",
                "finding": "unsafe_tool_access",
                "severity": "high",
                "evidence": {},
                "confidence": 1.0,
                "execution_cost": {
                    "test_count": 1,
                    "execution_time_seconds": 0.00001,
                },
            },
            {
                "status": "completed",
                "test": "memory_access_test",
                "finding": "memory_validation_weakness",
                "severity": "medium",
                "evidence": {},
                "confidence": 1.0,
                "execution_cost": {
                    "test_count": 1,
                    "execution_time_seconds": 0.00001,
                },
            },
        ],
        "findings": [
            "weak_permission_control",
            "unsafe_tool_access",
            "memory_validation_weakness",
        ],
        "llm_calls": 3,
        "fallback_used": False,
        "budget_used": {
            "tests": 3,
            "llm_calls": 3,
            "time_seconds": 0.001,
        },
        "decisions": [],
    }

    result = build_day7_adaptive_evaluation(
        adaptive_result,
        "day7-adaptive-test",
    )

    assert result["status"] == "completed"
    assert result["strategy"] == "adaptive"
    assert result["test_budget"] == 3
    assert result["llm_calls"] == 3
    assert result["fallback_used"] is False


def test_day7_adaptive_records_execution_cost():
    adaptive_result = {
        "status": "completed",
        "selected_tests": [
            "permission_test",
        ],
        "execution_results": [
            {
                "status": "completed",
                "test": "permission_test",
                "finding": "weak_permission_control",
                "severity": "high",
                "evidence": {},
                "confidence": 1.0,
                "execution_cost": {
                    "test_count": 1,
                    "execution_time_seconds": 0.00001,
                },
            },
        ],
        "findings": [
            "weak_permission_control",
        ],
        "llm_calls": 1,
        "fallback_used": False,
        "budget_used": {
            "tests": 1,
            "llm_calls": 1,
            "time_seconds": 0.001,
        },
        "decisions": [],
    }

    result = build_day7_adaptive_evaluation(
        adaptive_result,
        "day7-adaptive-cost-test",
    )

    cost = result["evaluation"]["execution_cost"]

    assert cost["test_count"] == 1
    assert cost["execution_time_seconds"] >= 0.0