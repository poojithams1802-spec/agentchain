from ..execution.sandbox_executor import execute_sandbox_test
from ..validator.chain_validator import EXPECTED_FINDINGS
from .mitigation_executor import apply_mitigation
from .mitigation_state import reset_mitigations


def _validate_replay_result(test_name, result):
    """
    Validate a single sandbox replay result.

    This performs the validation needed by the replay boundary
    without executing the sandbox test a second time.
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
            "error": "Unknown test."
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
        "error": None if valid else "Replay validation failed."
    }


def _is_attack_blocked(result):
    """
    Determine whether the mitigation actually disrupted
    the attack during the replay.
    """

    if not result:
        return False

    return (
        result.get("mitigation_applied") is True
        and isinstance(result.get("evidence"), dict)
        and result["evidence"].get("result") == "attack_blocked"
    )


def _get_residual_vulnerable_steps(
    test_name,
    after_result,
    disrupted
):
    """
    Determine which replay steps remain vulnerable after
    mitigation.

    For the current Phase 2 replay boundary, replay_attack()
    receives one test_name, so the residual list contains
    either zero or one step.
    """

    if disrupted:
        return []

    after_blocked = _is_attack_blocked(
        after_result
    )

    if not after_blocked:
        return [test_name]

    return []


def replay_attack(
    experiment_id,
    test_name,
    control_name
):
    """
    Execute the same controlled attack before and after
    mitigation.

    P4 public boundary:

        replay_attack(
            experiment_id,
            test_name,
            control_name
        )

    Workflow:

        1. Reset previous mitigation state.
        2. Execute baseline attack.
        3. Validate baseline result.
        4. Apply predefined mitigation.
        5. Execute the SAME attack again.
        6. Validate replay result.
        7. Determine disruption.
        8. Determine residual vulnerable steps.
        9. Produce validation result.
        10. Reset mitigation state.
    """

    # ---------------------------------------------------------
    # Input validation
    # ---------------------------------------------------------

    if not experiment_id:
        return {
            "status": "failed",
            "experiment_id": experiment_id,
            "test": test_name,
            "control": control_name,
            "evidence": "experiment_id is required."
        }

    if not test_name:
        return {
            "status": "failed",
            "experiment_id": experiment_id,
            "test": test_name,
            "control": control_name,
            "evidence": "test_name is required."
        }

    if not control_name:
        return {
            "status": "failed",
            "experiment_id": experiment_id,
            "test": test_name,
            "control": control_name,
            "evidence": "control_name is required."
        }

    # ---------------------------------------------------------
    # Ensure a clean experiment state
    # ---------------------------------------------------------

    reset_mitigations(
        experiment_id
    )

    # ---------------------------------------------------------
    # 1. Baseline execution
    # ---------------------------------------------------------

    before = execute_sandbox_test(
        experiment_id,
        test_name
    )

    # ---------------------------------------------------------
    # 2. Validate baseline
    # ---------------------------------------------------------

    before_validation = _validate_replay_result(
        test_name,
        before
    )

    # ---------------------------------------------------------
    # 3. Apply predefined mitigation
    # ---------------------------------------------------------

    activation = apply_mitigation(
        experiment_id,
        control_name
    )

    if activation.get("status") != "applied":
        reset_result = reset_mitigations(
            experiment_id
        )

        return {
            "status": "failed",
            "experiment_id": experiment_id,
            "test": test_name,
            "control": control_name,

            "before": before,
            "before_validation": before_validation,

            "activation": activation,

            "after": None,
            "after_validation": None,

            "attack_disrupted": False,
            "disrupted": False,

            "residual_vulnerable_steps": [
                test_name
            ],

            "validation_result": {
                "status": "failed",
                "before_valid": before_validation["valid"],
                "after_valid": False,
                "disrupted": False,
                "residual_vulnerable_steps": [
                    test_name
                ],
                "reason": "Mitigation activation failed."
            },

            "reset": reset_result,

            "evidence": "Mitigation activation failed."
        }

    # ---------------------------------------------------------
    # 4. SAME attack replay
    # ---------------------------------------------------------

    after = execute_sandbox_test(
        experiment_id,
        test_name
    )

    # ---------------------------------------------------------
    # 5. Validate after result
    # ---------------------------------------------------------

    after_validation = _validate_replay_result(
        test_name,
        after
    )

    # ---------------------------------------------------------
    # 6. Determine whether attack was disrupted
    # ---------------------------------------------------------

    disrupted = _is_attack_blocked(
        after
    )

    # ---------------------------------------------------------
    # 7. Determine residual vulnerable steps
    # ---------------------------------------------------------

    residual_vulnerable_steps = (
        _get_residual_vulnerable_steps(
            test_name,
            after,
            disrupted
        )
    )

    # ---------------------------------------------------------
    # 8. Overall validation result
    # ---------------------------------------------------------

    validation_success = (
        before_validation["valid"]
        and after_validation["valid"]
        and disrupted
        and len(residual_vulnerable_steps) == 0
    )

    validation_result = {
        "status": (
            "validated"
            if validation_success
            else "invalid"
        ),
        "before_valid": before_validation["valid"],
        "after_valid": after_validation["valid"],
        "disrupted": disrupted,
        "residual_vulnerable_steps": (
            residual_vulnerable_steps
        ),
        "attack_blocked": disrupted,
        "validation_rate": (
            1.0
            if validation_success
            else 0.0
        )
    }

    # ---------------------------------------------------------
    # 9. Reset mitigation state
    # ---------------------------------------------------------

    reset_result = reset_mitigations(
        experiment_id
    )

    # ---------------------------------------------------------
    # 10. Final response
    # ---------------------------------------------------------

    return {
        "status": "completed",
        "experiment_id": experiment_id,
        "test": test_name,
        "control": control_name,

        # Backward-compatible fields
        "before": before,
        "activation": activation,
        "after": after,
        "attack_disrupted": disrupted,

        # Final Phase 2 P2 contract
        "before_validation": before_validation,
        "after_validation": after_validation,
        "disrupted": disrupted,
        "residual_vulnerable_steps": (
            residual_vulnerable_steps
        ),
        "validation_result": validation_result,

        # Cleanup result
        "reset": reset_result
    }