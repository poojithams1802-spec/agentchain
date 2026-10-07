from sandbox.evaluation.day8_ablation_scenario import (
    get_day8_ablation_scenario,
    validate_day8_ablation_scenario,
)


def test_day8_scenario_is_valid():
    result = validate_day8_ablation_scenario()

    assert result["valid"] is True
    assert result["error"] is None


def test_day8_uses_same_three_test_chain():
    scenario = get_day8_ablation_scenario()

    assert scenario["chain"]["chain_id"] == (
        "CHAIN-AUTH-TOOL-MEM"
    )

    assert scenario["available_tests"] == [
        "permission_test",
        "tool_access_test",
        "memory_access_test",
    ]


def test_day8_budget_is_controlled():
    scenario = get_day8_ablation_scenario()

    assert scenario["budget"]["max_tests"] == 3
    assert scenario["budget"]["max_llm_calls"] == 3
    assert scenario["budget"]["max_time_seconds"] == 30.0


def test_day8_scenario_copies_are_independent():
    first = get_day8_ablation_scenario()
    second = get_day8_ablation_scenario()

    first["available_tests"].append(
        "invented_test"
    )

    first["budget"]["max_tests"] = 99

    assert second["available_tests"] == [
        "permission_test",
        "tool_access_test",
        "memory_access_test",
    ]

    assert second["budget"]["max_tests"] == 3