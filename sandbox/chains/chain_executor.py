"""
Phase 3 controlled multi-step chain executor.

The executor is intentionally thin:
- retrieves a registered chain
- validates the chain definition
- delegates actual execution/validation to ChainValidator
- enriches the result with chain metadata

It does not duplicate sandbox or validation logic.
"""

from ..validator.chain_validator import ChainValidator
from .chain_registry import get_chain


def execute_chain(experiment_id, chain_id):
    """
    Execute a registered controlled attack chain.

    Args:
        experiment_id (str): Experiment identifier.
        chain_id (str): Registered chain identifier.

    Returns:
        dict: Structured chain execution result.
    """

    if not experiment_id:
        return {
            "status": "invalid",
            "experiment_id": experiment_id,
            "chain_id": chain_id,
            "chain_length": 0,
            "validated_steps": 0,
            "total_steps": 0,
            "validation_rate": 0.0,
            "steps": [],
            "error": "experiment_id is required.",
        }

    if not chain_id:
        return {
            "status": "invalid",
            "experiment_id": experiment_id,
            "chain_id": chain_id,
            "chain_length": 0,
            "validated_steps": 0,
            "total_steps": 0,
            "validation_rate": 0.0,
            "steps": [],
            "error": "chain_id is required.",
        }

    chain = get_chain(chain_id)

    if chain is None:
        return {
            "status": "invalid",
            "experiment_id": experiment_id,
            "chain_id": chain_id,
            "chain_length": 0,
            "validated_steps": 0,
            "total_steps": 0,
            "validation_rate": 0.0,
            "steps": [],
            "error": f"Unknown chain: {chain_id}",
        }

    validator = ChainValidator(experiment_id)

    validation_result = validator.validate_chain(
        chain_id,
        chain["steps"],
    )

    return {
        "status": validation_result["status"],
        "experiment_id": experiment_id,
        "chain_id": chain_id,
        "name": chain["name"],
        "description": chain["description"],
        "steps": validation_result["steps"],
        "chain_length": validation_result["chain_length"],
        "validated_steps": validation_result["validated_steps"],
        "total_steps": validation_result["total_steps"],
        "validation_rate": validation_result["validation_rate"],
        "all_findings_reproduced": validation_result[
            "all_findings_reproduced"
        ],
        "error": validation_result.get("error"),
    }