from sandbox.evaluation.day9_ablation_run import (
    run_day9_ablation_experiments,
)


def test_day9_prepares_four_configurations():
    result = run_day9_ablation_experiments()

    assert result["status"] == "prepared"

    assert [
        item["config_id"]
        for item in result["configurations"]
    ] == ["A", "B", "C", "D"]


def test_day9_uses_identical_initial_states():
    result = run_day9_ablation_experiments()

    inputs = [
        item["planner_input"]
        for item in result["configurations"]
    ]

    first = inputs[0]

    for planner_input in inputs[1:]:
        assert (
            planner_input.available_tests
            == first.available_tests
        )

        assert (
            planner_input.previous_tests
            == first.previous_tests
        )

        assert (
            planner_input.findings
            == first.findings
        )

        assert (
            planner_input.chain_state
            == first.chain_state
        )

        assert (
            planner_input.testing_budget
            == first.testing_budget
        )