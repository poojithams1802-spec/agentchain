from sandbox.vulnerabilities.v5_indirect_prompt_injection import (
    run_v5_scenario,
)


def test_v5_indirect_prompt_injection():
    result = run_v5_scenario()

    assert result["vulnerability_id"] == "V5"
    assert result["name"] == "indirect_prompt_injection"
    assert result["test"] == "indirect_prompt_injection_test"

    assert result["expected"] == "external_instruction_ignored"
    assert result["actual"] == "external_instruction_followed"

    assert result["vulnerable"] is True
    assert result["severity"] == "high"

    assert result["evidence"]
    assert result["validation_rule"]