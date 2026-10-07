from .day7_controlled_experiment import (
    get_day7_experiment,
    validate_day7_experiment,
)
from .static_evaluation import run_static_evaluation


def run_day7_static_experiment(experiment_id="day7-static-001"):
    """
    Execute the static strategy under the Day 7
    controlled experiment configuration.
    """

    config = get_day7_experiment()

    validation = validate_day7_experiment(config)

    if not validation["valid"]:
        return {
            "status": "failed",
            "experiment_id": experiment_id,
            "error": validation["error"],
        }

    chain_id = config["scenario"]["chain_id"]
    budget = config["test_budget"]["static"]

    result = run_static_evaluation(
        experiment_id,
        chain_id
    )

    if result["status"] != "completed":
        return result

    evaluation = result["evaluation"]

    # Enforce the Day 7 equal-test-budget condition.
    if evaluation["total_tests"] > budget:
        return {
            "status": "failed",
            "experiment_id": experiment_id,
            "error": "Static strategy exceeded the Day 7 test budget.",
            "evaluation": evaluation,
        }

    return {
        "status": "completed",
        "experiment_id": experiment_id,
        "strategy": "static",
        "experiment_version": config["experiment_version"],
        "scenario_version": config["scenario_version"],
        "random_seed": config["random_seed"],
        "test_budget": budget,
        "llm_calls": 0,
        "fallback_used": False,
        "evaluation": evaluation,
    }