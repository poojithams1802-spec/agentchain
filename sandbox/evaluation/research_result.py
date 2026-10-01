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
    mitigation_validation=False
):
    """
    Create a standardized research experiment record.

    mode:
        "static" or "adaptive"

    Mitigation fields are optional and support Phase 2
    before/after replay evaluation.
    """

    if mode not in {"static", "adaptive"}:
        raise ValueError(
            'mode must be either "static" or "adaptive"'
        )

    if residual_vulnerable_steps is None:
        residual_vulnerable_steps = []

    return {
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