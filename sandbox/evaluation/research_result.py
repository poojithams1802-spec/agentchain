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
    fallback_used=False
):
    """
    Create a standardized research experiment record.

    mode:
        "static" or "adaptive"
    """

    if mode not in {"static", "adaptive"}:
        raise ValueError(
            "mode must be either 'static' or 'adaptive'"
        )

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
        "fallback_used": fallback_used
    }