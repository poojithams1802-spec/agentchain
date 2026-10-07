from sandbox.vulnerabilities.v11_cross_agent_trust import (
    run_v11_scenario,
)


def test_v11_cross_agent_trust():
    result = run_v11_scenario()

    assert result["vulnerability_id"] == "V11"
    assert result["name"] == "cross_agent_trust_weakness"
    assert result["test"] == "cross_agent_trust_test"

    assert result["expected"] == "untrusted_agent_rejected"
    assert result["actual"] == "untrusted_agent_trusted"

    assert result["vulnerable"] is True
    assert result["severity"] == "high"

    assert result["evidence"]
    assert result["validation_rule"]