from sandbox.vulnerabilities.v9_privilege_propagation import (
    run_v9_scenario,
)


def test_v9_privilege_propagation():
    result = run_v9_scenario()

    assert result["vulnerability_id"] == "V9"
    assert result["name"] == "privilege_propagation"
    assert result["test"] == "privilege_propagation_test"

    assert result["expected"] == "privilege_not_propagated"
    assert result["actual"] == "privilege_propagated"

    assert result["vulnerable"] is True
    assert result["severity"] == "high"

    assert result["evidence"]
    assert result["validation_rule"]