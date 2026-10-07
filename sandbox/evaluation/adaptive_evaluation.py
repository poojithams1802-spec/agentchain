from .evaluation_result import create_evaluation_result


def _aggregate_execution_cost(execution_results):
    """
    Aggregate execution-cost metadata from adaptive sandbox results.
    """

    if not execution_results:
        return {
            "test_count": 0,
            "execution_time_seconds": 0.0,
        }

    total_time = 0.0
    test_count = 0

    for result in execution_results:
        if not isinstance(result, dict):
            continue

        cost = result.get("execution_cost")

        if not isinstance(cost, dict):
            continue

        test_count += cost.get("test_count", 0)
        total_time += cost.get(
            "execution_time_seconds",
            0.0
        )

    return {
        "test_count": test_count,
        "execution_time_seconds": total_time,
    }


def run_adaptive_evaluation(
    experiment_id,
    executed_tests,
    findings,
    candidate_chains,
    validated_chains,
    chain_lengths,
    validation_rates,
    execution_results=None,
):
    """
    Convert adaptive execution results into the
    standardized research evaluation format.

    execution_results is optional so existing callers
    remain backward compatible.
    """

    if not experiment_id:
        return {
            "status": "failed",
            "experiment_id": experiment_id,
            "evaluation": None,
            "error": "experiment_id is required.",
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

    execution_cost = _aggregate_execution_cost(
        execution_results
    )

    evaluation = create_evaluation_result(
        mode="adaptive",
        experiment_id=experiment_id,
        total_tests=total_tests,
        total_findings=total_findings,
        candidate_chains=total_candidate_chains,
        validated_chains=total_validated_chains,
        average_chain_length=average_chain_length,
        validation_rate=validation_rate,
        execution_cost=execution_cost,
    )

    return {
        "status": "completed",
        "experiment_id": experiment_id,
        "adaptive_sequence": executed_tests,
        "evaluation": evaluation,
    }