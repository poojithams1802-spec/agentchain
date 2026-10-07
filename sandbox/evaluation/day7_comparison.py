from .day7_controlled_experiment import (
    get_day7_experiment,
    validate_day7_experiment,
)


def compare_day7_runs(
    static_result,
    adaptive_result,
):
    """
    Compare the static and adaptive Day-7 controlled runs.

    Both strategies must use the same controlled test budget.
    """

    config = get_day7_experiment()

    validation = validate_day7_experiment(config)

    if not validation["valid"]:
        return {
            "status": "failed",
            "error": validation["error"],
        }

    if static_result.get("status") != "completed":
        return {
            "status": "failed",
            "error": "Static experiment did not complete.",
        }

    if adaptive_result.get("status") != "completed":
        return {
            "status": "failed",
            "error": "Adaptive experiment did not complete.",
        }

    static_budget = static_result["test_budget"]
    adaptive_budget = adaptive_result["test_budget"]

    if static_budget != adaptive_budget:
        return {
            "status": "failed",
            "error": "Static and adaptive test budgets are not equal.",
        }

    static_eval = static_result["evaluation"]
    adaptive_eval = adaptive_result["evaluation"]

    static_time = (
        static_eval
        .get("execution_cost", {})
        .get("execution_time_seconds", 0.0)
    )

    adaptive_time = (
        adaptive_eval
        .get("execution_cost", {})
        .get("execution_time_seconds", 0.0)
    )

    return {
        "status": "completed",

        "experiment_version": config["experiment_version"],
        "scenario_version": config["scenario_version"],
        "random_seed": config["random_seed"],

        "equal_test_budget": True,
        "test_budget": static_budget,

        "static": {
            "tests": static_eval["total_tests"],
            "findings": static_eval["total_findings"],
            "candidate_chains": static_eval["candidate_chains"],
            "validated_chains": static_eval["validated_chains"],
            "average_chain_length": static_eval["average_chain_length"],
            "validation_rate": static_eval["validation_rate"],
            "execution_time_seconds": static_time,
            "llm_calls": static_result["llm_calls"],
            "fallback_used": static_result["fallback_used"],
        },

        "adaptive": {
            "tests": adaptive_eval["total_tests"],
            "findings": adaptive_eval["total_findings"],
            "candidate_chains": adaptive_eval["candidate_chains"],
            "validated_chains": adaptive_eval["validated_chains"],
            "average_chain_length": adaptive_eval["average_chain_length"],
            "validation_rate": adaptive_eval["validation_rate"],
            "execution_time_seconds": adaptive_time,
            "llm_calls": adaptive_result["llm_calls"],
            "fallback_used": adaptive_result["fallback_used"],
        },

        "difference": {
            "tests": (
                adaptive_eval["total_tests"]
                - static_eval["total_tests"]
            ),
            "findings": (
                adaptive_eval["total_findings"]
                - static_eval["total_findings"]
            ),
            "candidate_chains": (
                adaptive_eval["candidate_chains"]
                - static_eval["candidate_chains"]
            ),
            "validated_chains": (
                adaptive_eval["validated_chains"]
                - static_eval["validated_chains"]
            ),
            "average_chain_length": (
                adaptive_eval["average_chain_length"]
                - static_eval["average_chain_length"]
            ),
            "validation_rate": (
                adaptive_eval["validation_rate"]
                - static_eval["validation_rate"]
            ),
            "execution_time_seconds": (
                adaptive_time - static_time
            ),
            "llm_calls": (
                adaptive_result["llm_calls"]
                - static_result["llm_calls"]
            ),
        },
    }