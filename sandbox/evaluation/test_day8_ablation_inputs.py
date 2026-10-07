from sandbox.evaluation.day8_ablation_inputs import (
    ABLATION_CONFIGURATIONS,
    build_day8_ablation_inputs,
)


def test_day8_has_four_ablation_configurations():
    assert list(
        ABLATION_CONFIGURATIONS.keys()
    ) == ["A", "B", "C", "D"]


def test_all_ablation_inputs_use_same_scenario():
    results = build_day8_ablation_inputs()

    assert len(results) == 4

    first = results[0]["planner_input"]

    for result in results[1:]:
        planner_input = result["planner_input"]

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


def test_ablation_inputs_are_independent():
    results = build_day8_ablation_inputs()

    first = results[0]["planner_input"]
    second = results[1]["planner_input"]

    first.previous_tests.append(
        "permission_test"
    )

    first.available_tests.append(
        "invented_test"
    )

    assert second.previous_tests == []

    assert second.available_tests == [
        "permission_test",
        "tool_access_test",
        "memory_access_test",
    ]


def test_ablation_metadata_matches_required_modes():
    results = build_day8_ablation_inputs()

    assert results[0]["config_id"] == "A"
    assert results[0]["use_rag"] is False
    assert results[0]["use_chain_context"] is False

    assert results[1]["config_id"] == "B"
    assert results[1]["use_rag"] is True
    assert results[1]["use_chain_context"] is False

    assert results[2]["config_id"] == "C"
    assert results[2]["use_rag"] is False
    assert results[2]["use_chain_context"] is True

    assert results[3]["config_id"] == "D"
    assert results[3]["use_rag"] is True
    assert results[3]["use_chain_context"] is True