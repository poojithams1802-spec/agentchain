from .research_result import create_research_result


def record_experiment_result(
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
    Convert an experiment's recorded results into
    the standardized research-result structure.

    The mitigation-related parameters are optional so that
    existing Phase 1/static/adaptive experiment records
    remain backward compatible.
    """

    return create_research_result(
        experiment_id=experiment_id,
        mode=mode,
        executed_tests=executed_tests,
        findings=findings,
        candidate_chains=candidate_chains,
        validated_chains=validated_chains,
        average_chain_length=average_chain_length,
        validation_rate=validation_rate,
        execution_count=execution_count,
        llm_calls=llm_calls,
        fallback_used=fallback_used,

        # Phase 2 mitigation/replay data
        mitigation_control=mitigation_control,
        mitigation_selected=mitigation_selected,
        mitigation_applied=mitigation_applied,
        attack_success_before=attack_success_before,
        attack_success_after=attack_success_after,
        chain_disrupted=chain_disrupted,
        residual_vulnerable_steps=residual_vulnerable_steps,
        mitigation_validation=mitigation_validation
    )