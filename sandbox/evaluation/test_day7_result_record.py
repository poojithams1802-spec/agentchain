from sandbox.evaluation.day7_result_record import (
    build_day7_result_record,
)


def test_day7_result_record():
    experiment_result = {
        "status": "completed",
        "study": "phase3_day7_static_vs_adaptive",
        "comparison": {
            "experiment_version": "day7-v1",
            "scenario_version": "sandbox-v1",
            "random_seed": 42,
            "equal_test_budget": True,
            "test_budget": 3,
            "static": {
                "tests": 3,
                "findings": 3,
            },
            "adaptive": {
                "tests": 3,
                "findings": 3,
            },
            "difference": {
                "tests": 0,
                "findings": 0,
            },
        },
    }

    record = build_day7_result_record(
        experiment_result
    )

    assert record["study"] == (
        "phase3_day7_static_vs_adaptive"
    )

    assert record["equal_test_budget"] is True
    assert record["test_budget"] == 3
    assert record["static"]["tests"] == 3
    assert record["adaptive"]["tests"] == 3