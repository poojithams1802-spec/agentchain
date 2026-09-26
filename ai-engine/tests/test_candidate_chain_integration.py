from sandbox.validator.chain_validator import ChainValidator


def test_p3_candidate_chain_validates_with_p4():
    experiment_id = "day7-candidate-chain"
    chain_id = "CHAIN_P3_P4_001"

    candidate_chain = [
        "permission_test",
        "tool_access_test",
    ]

    validator = ChainValidator(experiment_id)

    result = validator.validate_chain(
        chain_id,
        candidate_chain,
    )

    assert result["status"] == "validated"
    assert result["validated_steps"] == 2
    assert result["total_steps"] == 2

    assert result["steps"][0]["test"] == "permission_test"
    assert result["steps"][0]["valid"] is True

    assert result["steps"][1]["test"] == "tool_access_test"
    assert result["steps"][1]["valid"] is True