from sandbox.evaluation.day7_controlled_experiment import (
    get_day7_experiment,
    validate_day7_experiment,
)


def test_day7_uses_equal_test_budget():
    config = get_day7_experiment()

    assert config["test_budget"]["static"] == 3
    assert config["test_budget"]["adaptive"] == 3


def test_day7_uses_same_scenario():
    config = get_day7_experiment()

    assert config["scenario"]["chain_id"] == "CHAIN-AUTH-TOOL-MEM"

    assert config["scenario"]["steps"] == [
        "permission_test",
        "tool_access_test",
        "memory_access_test",
    ]


def test_day7_configuration_is_valid():
    result = validate_day7_experiment()

    assert result["valid"] is True
    assert result["error"] is None


def test_day7_rejects_unequal_budget():
    config = get_day7_experiment()

    config["test_budget"]["adaptive"] = 2

    result = validate_day7_experiment(config)

    assert result["valid"] is False
    assert "equal" in result["error"]