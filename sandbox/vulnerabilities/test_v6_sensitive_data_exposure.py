from sandbox.vulnerabilities.v6_sensitive_data_exposure import (
    run_v6_scenario,
)


def test_v6_sensitive_data_exposure():
    result = run_v6_scenario()

    assert result["vulnerability_id"] == "V6"
    assert result["name"] == "sensitive_data_exposure"
    assert result["test"] == "sensitive_data_test"

    assert result["expected"] == "sensitive_data_protected"
    assert result["actual"] == "sensitive_data_exposed"

    assert result["vulnerable"] is True
    assert result["severity"] == "high"

    assert result["evidence"]
    assert result["validation_rule"]