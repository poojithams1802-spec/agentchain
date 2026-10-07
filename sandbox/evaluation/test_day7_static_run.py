from sandbox.evaluation.day7_static_run import (
    run_day7_static_experiment,
)


def test_day7_static_run_completes():
    result = run_day7_static_experiment(
        "day7-static-test"
    )

    assert result["status"] == "completed"
    assert result["strategy"] == "static"


def test_day7_static_respects_budget():
    result = run_day7_static_experiment(
        "day7-static-budget-test"
    )

    assert result["test_budget"] == 3
    assert result["evaluation"]["total_tests"] == 3


def test_day7_static_records_execution_cost():
    result = run_day7_static_experiment(
        "day7-static-cost-test"
    )

    cost = result["evaluation"]["execution_cost"]

    assert cost["test_count"] == 3
    assert cost["execution_time_seconds"] >= 0.0


def test_day7_static_has_no_llm_calls():
    result = run_day7_static_experiment(
        "day7-static-llm-test"
    )

    assert result["llm_calls"] == 0
    assert result["fallback_used"] is False