"""
Phase 3 controlled multi-step chain executor.

The executor is intentionally thin:
- retrieves a registered chain
- validates the chain definition
- delegates actual execution/validation to ChainValidator
- enriches the result with chain metadata
- converts an already-produced chain result into a research result

It does not duplicate sandbox or validation logic.
"""

from ..validator.chain_validator import ChainValidator
from ..evaluation.experiment_record import record_experiment_result
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


def chain_result_to_research_result(
    chain_result,
    mode="adaptive",
    llm_calls=0,
    fallback_used=False,
):
    """
    Convert an already-produced chain execution result into
    the standardized research-result structure.

    Important:
        This function does NOT execute the chain.

    It is intended for callers such as P2 that already have
    a chain_result and need to persist the standardized
    research-result representation.
    """

    if not isinstance(chain_result, dict):
        raise TypeError(
            "chain_result must be a dictionary."
        )

    chain_id = chain_result.get("chain_id")

    steps = chain_result.get("steps", [])

    executed_tests = [
        step["test"]
        for step in steps
        if "test" in step
    ]

    findings = [
        step["finding"]
        for step in steps
        if step.get("finding") is not None
    ]

    candidate_chains = []

    if chain_id:
        candidate_chains.append(chain_id)

    validated_chains = []

    if (
        chain_result.get("status") == "validated"
        and chain_result.get("all_findings_reproduced") is True
    ):
        validated_chains.append(chain_id)

    return record_experiment_result(
        experiment_id=chain_result.get("experiment_id"),
        mode=mode,
        executed_tests=executed_tests,
        findings=findings,
        candidate_chains=candidate_chains,
        validated_chains=validated_chains,
        average_chain_length=chain_result.get(
            "chain_length",
            0.0,
        ),
        validation_rate=chain_result.get(
            "validation_rate",
            0.0,
        ),
        execution_count=chain_result.get(
            "total_steps",
            len(executed_tests),
        ),
        llm_calls=llm_calls,
        fallback_used=fallback_used,

        # Phase 3 chain data
        chain_id=chain_id,
        chain_name=chain_result.get("name"),
        chain_steps=executed_tests,
        chain_length=chain_result.get("chain_length"),
        validated_steps=chain_result.get("validated_steps"),
        chain_validation_rate=chain_result.get(
            "validation_rate"
        ),
        all_findings_reproduced=chain_result.get(
            "all_findings_reproduced"
        ),
        chain_status=chain_result.get("status"),
    )


def execute_chain_as_research_result(
    experiment_id,
    chain_id,
    mode="adaptive",
    llm_calls=0,
    fallback_used=False,
):
    """
    Execute a controlled chain exactly once and convert
    the resulting chain result into the standardized
    research-result structure.

    This remains backward-compatible with the previous
    public helper.
    """

    chain_result = execute_chain(
        experiment_id,
        chain_id,
    )

    return chain_result_to_research_result(
        chain_result,
        mode=mode,
        llm_calls=llm_calls,
        fallback_used=fallback_used,
    )