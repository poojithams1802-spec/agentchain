from sandbox.vulnerabilities.v10_unsafe_delegation import (
    run_v10_scenario,
)


def test_v10_unsafe_delegation():
    result = run_v10_scenario()

    assert result["vulnerability_id"] == "V10"
    assert result["name"] == "unsafe_delegation"
    assert result["test"] == "unsafe_delegation_test"

    assert result["expected"] == "delegation_denied"
    assert result["actual"] == "delegation_allowed"

    assert result["vulnerable"] is True
    assert result["severity"] == "high"

    assert result["evidence"]
    assert result["validation_rule"]