def create_research_result(
    experiment_id,
    mode,
    executed_tests,
    findings,
    candidate_chains,
    validated_chains,
    average_chain_length,
    validation_rate,
    execution_count,
    llm_calls=0,
    fallback_used=False,
    mitigation_control=None,
    mitigation_selected=None,
    mitigation_applied=False,
    attack_success_before=None,
    attack_success_after=None,
    chain_disrupted=False,
    residual_vulnerable_steps=None,
    mitigation_validation=False,
    chain_id=None,
    chain_name=None,
    chain_steps=None,
    chain_length=None,
    validated_steps=None,
    chain_validation_rate=None,
    all_findings_reproduced=None,
    chain_status=None
):
    """
    Create a standardized research experiment record.

    mode:
        "static" or "adaptive"

    Mitigation fields are optional and support Phase 2
    before/after replay evaluation.

    Chain fields are optional and support Phase 3
    multi-step attack-chain execution.
    """

    if mode not in {"static", "adaptive"}:
        raise ValueError(
            'mode must be either "static" or "adaptive"'
        )

    if residual_vulnerable_steps is None:
        residual_vulnerable_steps = []

    result = {
        "experiment_id": experiment_id,
        "mode": mode,
        "executed_tests": executed_tests,
        "findings": findings,
        "candidate_chains": candidate_chains,
        "validated_chains": validated_chains,
        "average_chain_length": average_chain_length,
        "validation_rate": validation_rate,
        "execution_count": execution_count,
        "llm_calls": llm_calls,
        "fallback_used": fallback_used,

        # Phase 2 mitigation/replay fields
        "mitigation_control": mitigation_control,
        "mitigation_selected": mitigation_selected,
        "mitigation_applied": mitigation_applied,
        "attack_success_before": attack_success_before,
        "attack_success_after": attack_success_after,
        "chain_disrupted": chain_disrupted,
        "residual_vulnerable_steps": residual_vulnerable_steps,
        "mitigation_validation": mitigation_validation
    }

    # ---------------------------------------------------------
    # Phase 3 multi-step chain fields
    #
    # Add these only when a chain is actually being recorded.
    # This keeps existing Phase 1/Phase 2 result structures
    # backward compatible.
    # ---------------------------------------------------------
    if chain_id is not None:
        if chain_steps is None:
            chain_steps = []

        result.update({
            "chain_id": chain_id,
            "chain_name": chain_name,
            "chain_steps": list(chain_steps),
            "chain_length": (
                chain_length
                if chain_length is not None
                else len(chain_steps)
            ),
            "validated_steps": (
                validated_steps
                if validated_steps is not None
                else 0
            ),
            "chain_validation_rate": (
                chain_validation_rate
                if chain_validation_rate is not None
                else 0.0
            ),
            "all_findings_reproduced": (
                all_findings_reproduced
                if all_findings_reproduced is not None
                else False
            ),
            "chain_status": chain_status
        })

    return result