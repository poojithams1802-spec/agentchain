from sandbox.vulnerabilities.v12_tool_parameter_validation import (
    run_v12_scenario,
)


def test_v12_tool_parameter_validation():
    result = run_v12_scenario()

    assert result["vulnerability_id"] == "V12"
    assert result["name"] == "tool_parameter_validation_weakness"
    assert result["test"] == "tool_parameter_validation_test"

    assert result["expected"] == "invalid_parameter_rejected"
    assert result["actual"] == "invalid_parameter_accepted"

    assert result["vulnerable"] is True
    assert result["severity"] == "high"

    assert result["evidence"]
    assert result["validation_rule"]