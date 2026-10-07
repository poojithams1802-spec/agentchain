from sandbox.vulnerabilities.v4_prompt_injection import (
    run_v4_scenario,
)


def test_v4_prompt_injection():
    result = run_v4_scenario()

    assert result["vulnerability_id"] == "V4"
    assert result["name"] == "prompt_injection"
    assert result["test"] == "prompt_injection_test"

    assert result["expected"] == "instruction_rejected"
    assert result["actual"] == "instruction_accepted"

    assert result["vulnerable"] is True
    assert result["severity"] == "high"

    assert result["evidence"]
    assert result["validation_rule"]