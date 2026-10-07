from sandbox.test_runner import run_test
from sandbox.execution.sandbox_executor import execute_sandbox_test
from sandbox.validator.chain_validator import ChainValidator


def test_v4_test_runner():
    result = run_test("prompt_injection_test")

    assert result["status"] == "completed"
    assert result["test"] == "prompt_injection_test"
    assert result["finding"] == "prompt_injection"
    assert result["severity"] == "high"
    assert result["evidence"]
    assert result["confidence"] == 1.0


def test_v4_sandbox_executor():
    result = execute_sandbox_test(
        "day8-v4-test",
        "prompt_injection_test",
    )

    assert result["status"] == "completed"
    assert result["test"] == "prompt_injection_test"
    assert result["finding"] == "prompt_injection"
    assert result["evidence"]
    assert result["confidence"] == 1.0
    assert result["execution_cost"]["test_count"] == 1


def test_v4_chain_validator():
    validator = ChainValidator("day8-v4-validator")

    result = validator.validate_chain(
        "CHAIN-V4",
        ["prompt_injection_test"],
    )

    assert result["status"] == "validated"
    assert result["validated_steps"] == 1
    assert result["total_steps"] == 1
    assert result["validation_rate"] == 1.0
    assert result["all_findings_reproduced"] is True