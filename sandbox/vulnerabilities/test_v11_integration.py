from sandbox.test_runner import run_test
from sandbox.execution.sandbox_executor import execute_sandbox_test
from sandbox.execution.adaptive_test_executor import (
    validate_selected_test,
)
from sandbox.validator.chain_validator import ChainValidator


def test_v11_test_runner():
    result = run_test("cross_agent_trust_test")

    assert result["status"] == "completed"
    assert result["test"] == "cross_agent_trust_test"
    assert result["finding"] == "cross_agent_trust_weakness"
    assert result["severity"] == "high"
    assert result["evidence"]
    assert result["confidence"] == 1.0


def test_v11_sandbox_executor():
    result = execute_sandbox_test(
        "day10-v11-test",
        "cross_agent_trust_test",
    )

    assert result["status"] == "completed"
    assert result["test"] == "cross_agent_trust_test"
    assert result["finding"] == "cross_agent_trust_weakness"
    assert result["evidence"]
    assert result["confidence"] == 1.0
    assert result["execution_cost"]["test_count"] == 1


def test_v11_adaptive_boundary():
    result = validate_selected_test(
        "cross_agent_trust_test"
    )

    assert result["valid"] is True
    assert result["selected_test"] == "cross_agent_trust_test"
    assert result["error"] is None


def test_v11_chain_validator():
    validator = ChainValidator("day10-v11-validator")

    result = validator.validate_chain(
        "CHAIN-V11",
        ["cross_agent_trust_test"],
    )

    assert result["status"] == "validated"
    assert result["validated_steps"] == 1
    assert result["total_steps"] == 1
    assert result["validation_rate"] == 1.0
    assert result["all_findings_reproduced"] is True