def build_mitigation_experiment_record(
    replay_result,
    mode="adaptive",
    mitigation_selected=True,
    llm_calls=0,
    fallback_used=False
):
    """
    Convert a replay_attack() result into a standardized
    Phase 2 research experiment record.

    This function does not execute or replay the attack.
    It only transforms the existing replay evidence into
    evaluation data.
    """

    if not isinstance(replay_result, dict):
        raise ValueError(
            "replay_result must be a dictionary"
        )

    if replay_result.get("status") != "completed":
        raise ValueError(
            "replay_result must have status='completed'"
        )

    experiment_id = replay_result.get(
        "experiment_id"
    )

    test_name = replay_result.get(
        "test"
    )

    control_name = replay_result.get(
        "control"
    )

    before = replay_result.get(
        "before",
        {}
    )

    after = replay_result.get(
        "after",
        {}
    )

    before_validation = replay_result.get(
        "before_validation",
        {}
    )

    after_validation = replay_result.get(
        "after_validation",
        {}
    )

    disrupted = replay_result.get(
        "disrupted",
        False
    )

    residual_vulnerable_steps = replay_result.get(
        "residual_vulnerable_steps",
        []
    )

    validation_result = replay_result.get(
        "validation_result",
        {}
    )

    # ------------------------------------------------------
    # Attack success
    # ------------------------------------------------------

    attack_success_before = (
        before.get("status") == "completed"
        and bool(before.get("finding"))
    )

    attack_success_after = (
        after.get("status") == "completed"
        and not disrupted
    )

    # ------------------------------------------------------
    # Mitigation application
    # ------------------------------------------------------

    activation = replay_result.get(
        "activation",
        {}
    )

    mitigation_applied = (
        activation.get("status") == "applied"
    )

    # ------------------------------------------------------
    # Mitigation validation
    # ------------------------------------------------------

    mitigation_validation = (
        validation_result.get("status")
        == "validated"
    )

    # ------------------------------------------------------
    # Build standardized research record
    # ------------------------------------------------------

    return {
        "experiment_id": experiment_id,
        "mode": mode,

        "executed_tests": [
            test_name
        ],

        "findings": (
            [before.get("finding")]
            if before.get("finding")
            else []
        ),

        "candidate_chains": [],

        "validated_chains": [],

        "average_chain_length": 1.0,

        "validation_rate": validation_result.get(
            "validation_rate",
            0.0
        ),

        "execution_count": 2,

        "llm_calls": llm_calls,

        "fallback_used": fallback_used,

        # --------------------------------------------------
        # Phase 2 mitigation fields
        # --------------------------------------------------

        "mitigation_control": control_name,

        "mitigation_selected": (
            mitigation_selected
        ),

        "mitigation_applied": (
            mitigation_applied
        ),

        "attack_success_before": (
            attack_success_before
        ),

        "attack_success_after": (
            attack_success_after
        ),

        "chain_disrupted": (
            disrupted
        ),

        "residual_vulnerable_steps": (
            residual_vulnerable_steps
        ),

        "mitigation_validation": (
            mitigation_validation
        ),

        # --------------------------------------------------
        # Replay validation evidence
        # --------------------------------------------------

        "before_validation": before_validation,

        "after_validation": after_validation,

        "validation_result": validation_result
    }