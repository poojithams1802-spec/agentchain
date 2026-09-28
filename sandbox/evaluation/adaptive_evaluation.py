from .evaluation_result import create_evaluation_result


def run_adaptive_evaluation(
    experiment_id,
    executed_tests,
    findings,
    candidate_chains,
    validated_chains,
    chain_lengths,
    validation_rates
):
    """
    Convert actual adaptive experiment outputs into the
    standardized P4 evaluation format.

    The values passed to this function must come from the
    actual P2/P3 experiment results.
    """

    if not experiment_id:
        return {
            "status": "failed",
            "experiment_id": experiment_id,
            "evaluation": None,
            "error": "experiment_id is required."
        }

    total_tests = len(executed_tests)
    total_findings = len(findings)
    total_candidate_chains = len(candidate_chains)
    total_validated_chains = len(validated_chains)

    average_chain_length = (
        sum(chain_lengths) / len(chain_lengths)
        if chain_lengths
        else 0.0
    )

    validation_rate = (
        sum(validation_rates) / len(validation_rates)
        if validation_rates
        else 0.0
    )

    evaluation = create_evaluation_result(
        mode="adaptive",
        experiment_id=experiment_id,
        total_tests=total_tests,
        total_findings=total_findings,
        candidate_chains=total_candidate_chains,
        validated_chains=total_validated_chains,
        average_chain_length=average_chain_length,
        validation_rate=validation_rate
    )

    return {
        "status": "completed",
        "experiment_id": experiment_id,
        "adaptive_sequence": executed_tests,
        "evaluation": evaluation
    }