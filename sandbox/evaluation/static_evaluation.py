from ..baseline.static_baseline import validate_static_chain
from .evaluation_result import create_evaluation_result


def run_static_evaluation(experiment_id, chain_id):
    """
    Run the static baseline and convert its results
    into the standardized research evaluation format.
    """

    result = validate_static_chain(
        experiment_id,
        chain_id
    )

    if result["status"] != "completed":
        return {
            "status": "failed",
            "experiment_id": experiment_id,
            "chain_id": chain_id,
            "evaluation": None,
            "error": "Static baseline execution failed."
        }

    baseline = result["baseline"]
    validation = result["validation"]

    candidate_chains = 1

    validated_chains = (
        1
        if validation["status"] == "validated"
        else 0
    )

    evaluation = create_evaluation_result(
        mode="static",
        experiment_id=experiment_id,
        total_tests=baseline["total_tests"],
        total_findings=baseline["total_findings"],
        candidate_chains=candidate_chains,
        validated_chains=validated_chains,
        average_chain_length=validation["chain_length"],
        validation_rate=validation["validation_rate"],
        execution_cost=baseline.get("execution_cost"),
    )

    return {
        "status": "completed",
        "experiment_id": experiment_id,
        "chain_id": chain_id,
        "evaluation": evaluation
    }