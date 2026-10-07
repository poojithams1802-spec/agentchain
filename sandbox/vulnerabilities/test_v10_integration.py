from sandbox.test_runner import run_test
from sandbox.execution.sandbox_executor import execute_sandbox_test
from sandbox.execution.adaptive_test_executor import (
    validate_selected_test,
)
from sandbox.validator.chain_validator import ChainValidator


def test_v10_test_runner():
    result = run_test("unsafe_delegation_test")

    assert result["status"] == "completed"
    assert result["test"] == "unsafe_delegation_test"
    assert result["finding"] == "unsafe_delegation"
    assert result["severity"] == "high"
    assert result["evidence"]
    assert result["confidence"] == 1.0


def test_v10_sandbox_executor():
    result = execute_sandbox_test(
        "day10-v10-test",
        "unsafe_delegation_test",
    )

    assert result["status"] == "completed"
    assert result["test"] == "unsafe_delegation_test"
    assert result["finding"] == "unsafe_delegation"
    assert result["evidence"]
    assert result["confidence"] == 1.0
    assert result["execution_cost"]["test_count"] == 1


def test_v10_adaptive_boundary():
    result = validate_selected_test(
        "unsafe_delegation_test"
    )

    assert result["valid"] is True
    assert result["selected_test"] == "unsafe_delegation_test"
    assert result["error"] is None


def test_v10_chain_validator():
    validator = ChainValidator("day10-v10-validator")

    result = validator.validate_chain(
        "CHAIN-V10",
        ["unsafe_delegation_test"],
    )

    assert result["status"] == "validated"
    assert result["validated_steps"] == 1
    assert result["total_steps"] == 1
    assert result["validation_rate"] == 1.0
    assert result["all_findings_reproduced"] is True