from sandbox.vulnerabilities.v7_unsafe_file_operation import (
    run_v7_scenario,
)


def test_v7_unsafe_file_operation():
    result = run_v7_scenario()

    assert result["vulnerability_id"] == "V7"
    assert result["name"] == "unsafe_file_operation"
    assert result["test"] == "file_operation_test"

    assert result["expected"] == "file_operation_denied"
    assert result["actual"] == "file_operation_allowed"

    assert result["vulnerable"] is True
    assert result["severity"] == "high"

    assert result["evidence"]
    assert result["validation_rule"]