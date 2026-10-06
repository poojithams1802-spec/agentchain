"""
Phase 3 controlled multi-step chain replay.

This module extends the Phase 2 single-test replay concept
to registered multi-step chains.

Responsibilities:
- execute the complete chain before mitigation
- validate baseline step results
- apply one approved mitigation
- replay the same chain
- identify blocked steps
- identify residual vulnerable steps
- determine chain disruption
- reset mitigation state

It does not modify ChainValidator.
"""

from ..execution.sandbox_executor import execute_sandbox_test
from ..mitigation.mitigation_executor import apply_mitigation
from ..mitigation.mitigation_state import reset_mitigations
from ..validator.chain_validator import EXPECTED_FINDINGS
from .chain_registry import get_chain


def _validate_chain_step(test_name, result):
    """
    Validate a single chain step using the existing
    expected-finding and evidence rules.
    """

    expected_finding = EXPECTED_FINDINGS.get(test_name)

    if expected_finding is None:
        return {
            "valid": False,
            "test": test_name,
            "status": result.get("status"),
            "finding": result.get("finding"),
            "expected_finding": None,
            "finding_matches": False,
            "evidence_exists": bool(result.get("evidence")),
            "error": "Unknown test.",
        }

    finding_matches = (
        result.get("finding") == expected_finding
    )

    evidence_exists = bool(
        result.get("evidence")
    )

    status_valid = (
        result.get("status") == "completed"
    )

    valid = (
        status_valid
        and finding_matches
        and evidence_exists
    )

    return {
        "valid": valid,
        "test": test_name,
        "status": result.get("status"),
        "finding": result.get("finding"),
        "expected_finding": expected_finding,
        "finding_matches": finding_matches,
        "evidence_exists": evidence_exists,
        "error": None if valid else "Chain step validation failed.",
    }


def _is_attack_blocked(result):
    """
    Determine whether a particular chain step was blocked
    by the active mitigation.
    """

    if not result:
        return False

    return (
        result.get("mitigation_applied") is True
        and isinstance(result.get("evidence"), dict)
        and result["evidence"].get("result") == "attack_blocked"
    )


def _execute_steps(experiment_id, steps):
    """
    Execute each step in the registered chain.
    """

    results = []

    for test_name in steps:
        result = execute_sandbox_test(
            experiment_id,
            test_name,
        )

        results.append(result)

    return results


def _validate_steps(step_names, results):
    """
    Validate all chain step results.
    """

    validations = []

    for test_name, result in zip(step_names, results):
        validations.append(
            _validate_chain_step(
                test_name,
                result,
            )
        )

    validated_steps = sum(
        validation["valid"]
        for validation in validations
    )

    total_steps = len(step_names)

    validation_rate = (
        validated_steps / total_steps
        if total_steps > 0
        else 0.0
    )

    return {
        "valid": (
            total_steps > 0
            and validated_steps == total_steps
        ),
        "validated_steps": validated_steps,
        "total_steps": total_steps,
        "validation_rate": validation_rate,
        "steps": validations,
    }


def _get_residual_vulnerable_steps(step_names, after_results):
    """
    Identify chain steps that remain vulnerable after mitigation.

    A step is residual when its replay was not blocked.
    """

    residual_steps = []

    for test_name, result in zip(
        step_names,
        after_results,
    ):
        if not _is_attack_blocked(result):
            residual_steps.append(test_name)

    return residual_steps


def replay_chain(
    experiment_id,
    chain_id,
    control_name,
):
    """
    Replay a registered multi-step chain before and after
    applying one predefined mitigation.

    Returns:
        dict: Structured chain replay and disruption result.
    """

    if not experiment_id:
        return {
            "status": "failed",
            "experiment_id": experiment_id,
            "chain_id": chain_id,
            "control": control_name,
            "error": "experiment_id is required.",
        }

    if not chain_id:
        return {
            "status": "failed",
            "experiment_id": experiment_id,
            "chain_id": chain_id,
            "control": control_name,
            "error": "chain_id is required.",
        }

    if not control_name:
        return {
            "status": "failed",
            "experiment_id": experiment_id,
            "chain_id": chain_id,
            "control": control_name,
            "error": "control_name is required.",
        }

    chain = get_chain(chain_id)

    if chain is None:
        return {
            "status": "failed",
            "experiment_id": experiment_id,
            "chain_id": chain_id,
            "control": control_name,
            "error": f"Unknown chain: {chain_id}",
        }

    steps = chain["steps"]

    # Always begin from a clean mitigation state.
    reset_mitigations(experiment_id)

    # ---------------------------------------------------------
    # 1. Baseline execution
    # ---------------------------------------------------------

    before_results = _execute_steps(
        experiment_id,
        steps,
    )

    before_validation = _validate_steps(
        steps,
        before_results,
    )

    # ---------------------------------------------------------
    # 2. Apply mitigation
    # ---------------------------------------------------------

    activation = apply_mitigation(
        experiment_id,
        control_name,
    )

    if activation.get("status") != "applied":
        reset_result = reset_mitigations(
            experiment_id
        )

        return {
            "status": "failed",
            "experiment_id": experiment_id,
            "chain_id": chain_id,
            "control": control_name,
            "chain_name": chain["name"],
            "chain_steps": steps,
            "before": before_results,
            "before_validation": before_validation,
            "activation": activation,
            "after": None,
            "after_validation": None,
            "blocked_steps": [],
            "residual_vulnerable_steps": list(steps),
            "chain_disrupted": False,
            "validation_result": {
                "status": "failed",
                "before_valid": before_validation["valid"],
                "after_valid": False,
                "chain_disrupted": False,
                "blocked_steps": [],
                "residual_vulnerable_steps": list(steps),
                "reason": "Mitigation activation failed.",
            },
            "reset": reset_result,
        }

    # ---------------------------------------------------------
    # 3. Replay the SAME chain
    # ---------------------------------------------------------

    after_results = _execute_steps(
        experiment_id,
        steps,
    )

    after_validation = _validate_steps(
        steps,
        after_results,
    )

    # ---------------------------------------------------------
    # 4. Identify blocked and residual steps
    # ---------------------------------------------------------

    blocked_steps = [
        test_name
        for test_name, result in zip(
            steps,
            after_results,
        )
        if _is_attack_blocked(result)
    ]

    residual_vulnerable_steps = (
        _get_residual_vulnerable_steps(
            steps,
            after_results,
        )
    )

    chain_disrupted = len(blocked_steps) > 0

    # ---------------------------------------------------------
    # 5. Final chain-level validation
    # ---------------------------------------------------------

    validation_success = (
        before_validation["valid"]
        and after_validation["valid"]
        and chain_disrupted
    )

    validation_result = {
        "status": (
            "validated"
            if validation_success
            else "invalid"
        ),
        "before_valid": before_validation["valid"],
        "after_valid": after_validation["valid"],
        "chain_disrupted": chain_disrupted,
        "blocked_steps": blocked_steps,
        "residual_vulnerable_steps": residual_vulnerable_steps,
        "attack_blocked": chain_disrupted,
        "validation_rate": (
            1.0
            if validation_success
            else 0.0
        ),
    }

    # ---------------------------------------------------------
    # 6. Reset mitigation state
    # ---------------------------------------------------------

    reset_result = reset_mitigations(
        experiment_id
    )

    return {
        "status": "completed",
        "experiment_id": experiment_id,
        "chain_id": chain_id,
        "control": control_name,
        "chain_name": chain["name"],
        "chain_description": chain["description"],
        "chain_steps": steps,
        "chain_length": len(steps),

        # Before
        "before": before_results,
        "before_validation": before_validation,

        # Mitigation
        "activation": activation,

        # After
        "after": after_results,
        "after_validation": after_validation,

        # Chain disruption
        "blocked_steps": blocked_steps,
        "residual_vulnerable_steps": residual_vulnerable_steps,
        "chain_disrupted": chain_disrupted,

        # Final validation
        "validation_result": validation_result,

        # Cleanup
        "reset": reset_result,
    }