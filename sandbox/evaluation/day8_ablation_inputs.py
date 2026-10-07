import sys

sys.path.insert(0, "ai-engine")

from schemas import PlannerInput, TestingBudget

from .day8_ablation_scenario import (
    get_day8_ablation_scenario,
    validate_day8_ablation_scenario,
)


ABLATION_CONFIGURATIONS = {
    "A": {
        "name": "LLM only",
        "use_rag": False,
        "use_chain_context": False,
    },
    "B": {
        "name": "LLM + RAG",
        "use_rag": True,
        "use_chain_context": False,
    },
    "C": {
        "name": "LLM + attack-chain context",
        "use_rag": False,
        "use_chain_context": True,
    },
    "D": {
        "name": "LLM + RAG + attack-chain context",
        "use_rag": True,
        "use_chain_context": True,
    },
}


def build_day8_planner_input(scenario=None):
    """
    Build one independent PlannerInput from the shared
    Day-8 P4 scenario.

    This function does not execute the planner.
    """

    if scenario is None:
        scenario = get_day8_ablation_scenario()

    validation = validate_day8_ablation_scenario(
        scenario
    )

    if not validation["valid"]:
        raise ValueError(
            validation["error"]
        )

    return PlannerInput(
        findings=[],
        previous_tests=scenario["previous_tests"].copy(),
        available_tests=scenario["available_tests"].copy(),
        retrieved_knowledge=[],
        chain_state={
            "chain_id": scenario["chain"]["chain_id"],
            "ordered_steps": scenario["chain"]["ordered_steps"].copy(),
            "dependencies": {
                key: value.copy()
                for key, value in scenario["chain"]["dependencies"].items()
            },
            "validation_result": {},
        },
        testing_budget=TestingBudget(
            max_tests=scenario["budget"]["max_tests"],
            max_llm_calls=scenario["budget"]["max_llm_calls"],
            max_time_seconds=scenario["budget"]["max_time_seconds"],
        ),
    )


def build_day8_ablation_inputs(scenario=None):
    """
    Build four independent initial planner states.

    Every configuration receives identical P4 scenario data.
    Only the ablation configuration metadata differs.
    """

    if scenario is None:
        scenario = get_day8_ablation_scenario()

    validation = validate_day8_ablation_scenario(
        scenario
    )

    if not validation["valid"]:
        raise ValueError(
            validation["error"]
        )

    results = []

    for config_id, config in ABLATION_CONFIGURATIONS.items():
        planner_input = build_day8_planner_input(
            scenario
        )

        results.append(
            {
                "config_id": config_id,
                "name": config["name"],
                "use_rag": config["use_rag"],
                "use_chain_context": config["use_chain_context"],
                "planner_input": planner_input,
            }
        )

    return results