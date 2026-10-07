def create_evaluation_result(
    mode,
    experiment_id,
    total_tests,
    total_findings,
    candidate_chains,
    validated_chains,
    average_chain_length,
    validation_rate,
    execution_cost=None,
):
    """
    Create a standardized research evaluation result.

    mode:
        "static" or "adaptive"
    """

    if mode not in {"static", "adaptive"}:
        raise ValueError(
            "mode must be either 'static' or 'adaptive'"
        )

    result = {
        "mode": mode,
        "experiment_id": experiment_id,
        "total_tests": total_tests,
        "total_findings": total_findings,
        "candidate_chains": candidate_chains,
        "validated_chains": validated_chains,
        "average_chain_length": average_chain_length,
        "validation_rate": validation_rate,
    }

    # Preserve backward compatibility.
    if execution_cost is not None:
        result["execution_cost"] = execution_cost

    return result