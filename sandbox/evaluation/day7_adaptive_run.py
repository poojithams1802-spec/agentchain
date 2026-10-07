from .adaptive_evaluation import run_adaptive_evaluation
from .day7_controlled_experiment import (
    get_day7_experiment,
    validate_day7_experiment,
)
from ..validator.chain_validator import ChainValidator


def build_day7_adaptive_evaluation(
    adaptive_result,
    experiment_id,
):
    """
    Convert the detailed P3 adaptive result into the
    P4-controlled Day 7 evaluation format.

    This function does not execute sandbox tests.
    """

    config = get_day7_experiment()

    config_validation = validate_day7_experiment(config)

    if not config_validation["valid"]:
        return {
            "status": "failed",
            "experiment_id": experiment_id,
            "error": config_validation["error"],
        }

    if not isinstance(adaptive_result, dict):
        return {
            "status": "failed",
            "experiment_id": experiment_id,
            "error": "adaptive_result must be a dictionary.",
        }

    if adaptive_result.get("status") != "completed":
        return {
            "status": "failed",
            "experiment_id": experiment_id,
            "error": "Adaptive detailed run did not complete.",
        }

    selected_tests = adaptive_result.get(
        "selected_tests",
        []
    )

    execution_results = adaptive_result.get(
        "execution_results",
        []
    )

    findings = adaptive_result.get(
        "findings",
        []
    )

    if len(selected_tests) > config["test_budget"]["adaptive"]:
        return {
            "status": "failed",
            "experiment_id": experiment_id,
            "error": "Adaptive strategy exceeded the Day 7 test budget.",
        }

    # Validate the selected sequence against the controlled chain.
    chain_id = config["scenario"]["chain_id"]

    validator = ChainValidator(experiment_id)

    validation_result = validator.validate_chain(
        chain_id,
        selected_tests,
    )

    candidate_chains = []

    if selected_tests:
        candidate_chains.append(
            selected_tests
        )

    validated_chains = []

    if validation_result["status"] == "validated":
        validated_chains.append(
            selected_tests
        )

    chain_lengths = []

    if selected_tests:
        chain_lengths.append(
            len(selected_tests)
        )

    validation_rates = []

    if selected_tests:
        validation_rates.append(
            validation_result["validation_rate"]
        )

    evaluation_result = run_adaptive_evaluation(
        experiment_id=experiment_id,
        executed_tests=selected_tests,
        findings=findings,
        candidate_chains=candidate_chains,
        validated_chains=validated_chains,
        chain_lengths=chain_lengths,
        validation_rates=validation_rates,
        execution_results=execution_results,
    )

    if evaluation_result["status"] != "completed":
        return evaluation_result

    evaluation = evaluation_result["evaluation"]

    return {
        "status": "completed",
        "experiment_id": experiment_id,
        "strategy": "adaptive",
        "experiment_version": config["experiment_version"],
        "scenario_version": config["scenario_version"],
        "random_seed": config["random_seed"],
        "test_budget": config["test_budget"]["adaptive"],
        "llm_calls": adaptive_result.get(
            "llm_calls",
            adaptive_result.get("budget_used", {}).get(
                "llm_calls",
                0,
            ),
        ),
        "fallback_used": adaptive_result.get(
            "fallback_used",
            False,
        ),
        "budget_used": adaptive_result.get(
            "budget_used",
            {},
        ),
        "planner_decisions": adaptive_result.get(
            "decisions",
            adaptive_result.get("planner_decisions", []),
        ),
        "validation": validation_result,
        "evaluation": evaluation,
    }
def run_day7_adaptive_experiment(
    adaptive_loop,
    planner_input,
    experiment_id="day7-adaptive-real-001",
):
    """
    Run the P3 adaptive loop under the P4 Day 7
    controlled experiment configuration.

    P4 owns the experiment constraints and evaluation.
    P3 owns the adaptive planner implementation.
    """

    config = get_day7_experiment()

    config_validation = validate_day7_experiment(config)

    if not config_validation["valid"]:
        return {
            "status": "failed",
            "experiment_id": experiment_id,
            "error": config_validation["error"],
        }

    budget = config["test_budget"]["adaptive"]

    # Ensure the supplied planner state uses the same
    # Day-7 sandbox-test budget.
    planner_input.testing_budget.max_tests = budget

    # Use the Day-7 controlled time budget.
    planner_input.testing_budget.max_time_seconds = 30.0

    detailed_result = adaptive_loop.run_detailed(
        planner_input=planner_input,
        experiment_id=experiment_id,
        max_tests=budget,
    )

    return build_day7_adaptive_evaluation(
        detailed_result,
        experiment_id,
    )