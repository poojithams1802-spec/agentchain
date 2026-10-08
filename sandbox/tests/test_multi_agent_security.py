from sandbox.agent.multi_agent_security import (
    CHAIN_ID,
    build_multi_agent_security_scenario,
    execute_multi_agent_security_scenario,
    run_and_validate_multi_agent_security_scenario,
    validate_multi_agent_security_scenario,
)


def test_security_scenario_registers_two_agents():
    registry = build_multi_agent_security_scenario()

    agents = registry.list_agents()

    assert len(agents) == 2
    assert agents[0]["agent_id"] == "AGENT_UNTRUSTED"
    assert agents[1]["agent_id"] == "AGENT_CONTROLLED"


def test_security_scenario_has_expected_trust_levels():
    registry = build_multi_agent_security_scenario()

    untrusted = registry.get_agent("AGENT_UNTRUSTED")
    controlled = registry.get_agent("AGENT_CONTROLLED")

    assert untrusted.trust_level == 0.2
    assert controlled.trust_level == 0.9


def test_security_scenario_communication_is_delivered():
    result = execute_multi_agent_security_scenario()

    assert result["communication"]["status"] == "delivered"


def test_security_scenario_contains_v11_and_v10():
    result = execute_multi_agent_security_scenario()

    assert result["vulnerabilities"]["V11"]["vulnerable"] is True
    assert result["vulnerabilities"]["V10"]["vulnerable"] is True


def test_security_chain_is_v11_to_v10():
    result = execute_multi_agent_security_scenario()

    assert result["chain_id"] == CHAIN_ID
    assert result["chain_triggered"] is True

    assert [
        step["vulnerability_id"]
        for step in result["chain_steps"]
    ] == ["V11", "V10"]


def test_security_chain_validation_passes():
    result = execute_multi_agent_security_scenario()

    validation = validate_multi_agent_security_scenario(result)

    assert validation["valid"] is True
    assert validation["validated_chain"] is True
    assert validation["chain_length"] == 2


def test_convenience_runner_returns_validated_chain():
    result = run_and_validate_multi_agent_security_scenario()

    assert result["validation"]["valid"] is True
    assert result["validation"]["validated_chain"] is True


def test_validation_rejects_wrong_chain_order():
    result = execute_multi_agent_security_scenario()

    result["chain_steps"] = list(
        reversed(result["chain_steps"])
    )

    validation = validate_multi_agent_security_scenario(result)

    assert validation["valid"] is False
    assert any(
        "V11 -> V10" in error
        for error in validation["errors"]
    )


def test_validation_rejects_undelivered_chain():
    result = execute_multi_agent_security_scenario()

    result["communication"]["status"] = "denied"

    validation = validate_multi_agent_security_scenario(result)

    assert validation["valid"] is False
    assert any(
        "communication" in error.lower()
        for error in validation["errors"]
    )