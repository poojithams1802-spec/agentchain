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
    fallback_used=False
):
    """
    Convert an experiment's recorded results into
    the standardized research-result structure.
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
        fallback_used=fallback_used
    )