from sandbox.evaluation.day7_comparison import (
    compare_day7_runs,
)


def _static_result():
    return {
        "status": "completed",
        "test_budget": 3,
        "llm_calls": 0,
        "fallback_used": False,
        "evaluation": {
            "total_tests": 3,
            "total_findings": 3,
            "candidate_chains": 1,
            "validated_chains": 1,
            "average_chain_length": 3,
            "validation_rate": 1.0,
            "execution_cost": {
                "test_count": 3,
                "execution_time_seconds": 0.001,
            },
        },
    }


def _adaptive_result():
    return {
        "status": "completed",
        "test_budget": 3,
        "llm_calls": 3,
        "fallback_used": False,
        "evaluation": {
            "total_tests": 3,
            "total_findings": 3,
            "candidate_chains": 1,
            "validated_chains": 1,
            "average_chain_length": 3,
            "validation_rate": 1.0,
            "execution_cost": {
                "test_count": 3,
                "execution_time_seconds": 0.002,
            },
        },
    }


def test_day7_comparison_accepts_equal_budget():
    result = compare_day7_runs(
        _static_result(),
        _adaptive_result(),
    )

    assert result["status"] == "completed"
    assert result["equal_test_budget"] is True
    assert result["test_budget"] == 3


def test_day7_comparison_records_llm_usage():
    result = compare_day7_runs(
        _static_result(),
        _adaptive_result(),
    )

    assert result["static"]["llm_calls"] == 0
    assert result["adaptive"]["llm_calls"] == 3
    assert result["difference"]["llm_calls"] == 3


def test_day7_comparison_records_execution_time():
    result = compare_day7_runs(
        _static_result(),
        _adaptive_result(),
    )

    assert result["static"]["execution_time_seconds"] == 0.001
    assert result["adaptive"]["execution_time_seconds"] == 0.002
    assert result["difference"]["execution_time_seconds"] == 0.001


def test_day7_comparison_rejects_unequal_budget():
    adaptive = _adaptive_result()
    adaptive["test_budget"] = 2

    result = compare_day7_runs(
        _static_result(),
        adaptive,
    )

    assert result["status"] == "failed"
    assert "budget" in result["error"].lower()