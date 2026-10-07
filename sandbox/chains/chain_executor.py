"""
Phase 3 controlled multi-step chain executor.

Responsibilities:
- retrieve a registered chain
- validate and execute the chain
- enrich results with chain metadata
- aggregate execution-cost metadata
- convert chain results into research results

The existing execution interface remains backward-compatible.
"""

from ..validator.chain_validator import ChainValidator
from ..evaluation.experiment_record import (
    record_experiment_result,
)
from .chain_registry import get_chain


def execute_chain(
    experiment_id,
    chain_id,
):
    """
    Execute a registered controlled attack chain.
    """

    # =========================================================
    # INPUT VALIDATION
    # =========================================================

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

    # =========================================================
    # GET CHAIN
    # =========================================================

    chain = get_chain(
        chain_id
    )

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
            "error": (
                f"Unknown chain: {chain_id}"
            ),
        }

    # =========================================================
    # VALIDATE / EXECUTE
    # =========================================================

    validator = ChainValidator(
        experiment_id
    )

    validation_result = (
        validator.validate_chain(
            chain_id,
            chain["steps"],
        )
    )

    # =========================================================
    # EXECUTION COST
    # =========================================================

    step_results = validation_result[
        "steps"
    ]

    total_test_count = sum(
        step.get(
            "execution_cost",
            {},
        ).get(
            "test_count",
            0,
        )
        for step in step_results
        if isinstance(
            step.get("execution_cost"),
            dict,
        )
    )

    total_execution_time_seconds = sum(
        step.get(
            "execution_cost",
            {},
        ).get(
            "execution_time_seconds",
            0.0,
        )
        for step in step_results
        if isinstance(
            step.get("execution_cost"),
            dict,
        )
    )

    execution_cost = {
        "test_count": total_test_count,
        "execution_time_seconds": (
            total_execution_time_seconds
        ),
    }

    # =========================================================
    # RETURN EXISTING + NEW P3 METADATA
    # =========================================================

    return {
        "status": validation_result[
            "status"
        ],
        "experiment_id": experiment_id,
        "chain_id": chain_id,

        # Existing interface
        "name": chain["name"],
        "description": chain["description"],
        "steps": validation_result[
            "steps"
        ],
        "chain_length": validation_result[
            "chain_length"
        ],
        "validated_steps": validation_result[
            "validated_steps"
        ],
        "total_steps": validation_result[
            "total_steps"
        ],
        "validation_rate": validation_result[
            "validation_rate"
        ],
        "all_findings_reproduced": (
            validation_result[
                "all_findings_reproduced"
            ]
        ),

        # New P3 metadata
        "chain_name": chain.get(
            "chain_name",
            chain["name"],
        ),
        "ordered_steps": chain.get(
            "ordered_steps",
            chain["steps"],
        ),
        "vulnerability_ids": chain.get(
            "vulnerability_ids",
            [],
        ),
        "entry_condition": chain.get(
            "entry_condition"
        ),
        "expected_goal": chain.get(
            "expected_goal"
        ),

        # Phase 3 execution cost
        "execution_cost": execution_cost,

        "error": validation_result.get(
            "error"
        ),
    }


def chain_result_to_research_result(
    chain_result,
    mode="adaptive",
    llm_calls=0,
    fallback_used=False,
):
    """
    Convert an already-produced chain result into
    the standardized research-result structure.

    This function does NOT execute the chain.
    """

    if not isinstance(
        chain_result,
        dict,
    ):
        raise TypeError(
            "chain_result must be a dictionary."
        )

    chain_id = chain_result.get(
        "chain_id"
    )

    steps = chain_result.get(
        "steps",
        [],
    )

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
        candidate_chains.append(
            chain_id
        )

    validated_chains = []

    if (
        chain_result.get("status")
        == "validated"
        and chain_result.get(
            "all_findings_reproduced"
        )
        is True
    ):
        validated_chains.append(
            chain_id
        )

    return record_experiment_result(
        experiment_id=chain_result.get(
            "experiment_id"
        ),
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

        # Existing Phase 3 chain data
        chain_id=chain_id,
        chain_name=chain_result.get(
            "chain_name",
            chain_result.get("name"),
        ),
        chain_steps=chain_result.get(
            "ordered_steps",
            executed_tests,
        ),
        chain_length=chain_result.get(
            "chain_length"
        ),
        validated_steps=chain_result.get(
            "validated_steps"
        ),
        chain_validation_rate=chain_result.get(
            "validation_rate"
        ),
        all_findings_reproduced=chain_result.get(
            "all_findings_reproduced"
        ),
        chain_status=chain_result.get(
            "status"
        ),
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
    the result into the standardized research-result structure.
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