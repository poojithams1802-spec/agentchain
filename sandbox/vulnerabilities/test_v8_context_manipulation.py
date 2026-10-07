from sandbox.vulnerabilities.v8_context_manipulation import (
    run_v8_scenario,
)


def test_v8_context_manipulation():
    result = run_v8_scenario()

    assert result["vulnerability_id"] == "V8"
    assert result["name"] == "context_manipulation"
    assert result["test"] == "context_manipulation_test"

    assert result["expected"] == "untrusted_context_rejected"
    assert result["actual"] == "untrusted_context_accepted"

    assert result["vulnerable"] is True
    assert result["severity"] == "high"

    assert result["evidence"]
    assert result["validation_rule"]