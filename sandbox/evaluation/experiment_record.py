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
    Convert an experiment's recorded results into
    the standardized research-result structure.

    Phase 1 and Phase 2 parameters remain backward compatible.

    Phase 3 chain parameters are optional and are forwarded
    only when chain information is provided.
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
        mitigation_validation=mitigation_validation,

        # Phase 3 chain data
        chain_id=chain_id,
        chain_name=chain_name,
        chain_steps=chain_steps,
        chain_length=chain_length,
        validated_steps=validated_steps,
        chain_validation_rate=chain_validation_rate,
        all_findings_reproduced=all_findings_reproduced,
        chain_status=chain_status
    )