"""
Day 7 controlled experiment configuration.

Defines the common scenario and equal test budget used
for static vs adaptive comparison.
"""


DAY7_EXPERIMENT = {
    "experiment_version": "day7-v1",
    "scenario_version": "sandbox-v1",

    # Both strategies receive the same maximum number
    # of sandbox security tests.
    "test_budget": {
        "static": 3,
        "adaptive": 3,
    },

    # Reproducibility metadata.
    "random_seed": 42,

    # Same controlled scenario for both strategies.
    "scenario": {
        "chain_id": "CHAIN-AUTH-TOOL-MEM",
        "steps": [
            "permission_test",
            "tool_access_test",
            "memory_access_test",
        ],
    },

    # LLM usage is measured independently rather than
    # being treated as an equivalent test budget.
    "llm_budget": {
        "static": None,
        "adaptive": None,
    },
}


def get_day7_experiment():
    """
    Return a copy of the Day 7 controlled experiment
    configuration.
    """
    return {
        **DAY7_EXPERIMENT,
        "test_budget": DAY7_EXPERIMENT["test_budget"].copy(),
        "scenario": {
            **DAY7_EXPERIMENT["scenario"],
            "steps": DAY7_EXPERIMENT["scenario"]["steps"].copy(),
        },
        "llm_budget": DAY7_EXPERIMENT["llm_budget"].copy(),
    }


def validate_day7_experiment(config=None):
    """
    Validate the Day 7 controlled experiment configuration.
    """

    if config is None:
        config = DAY7_EXPERIMENT

    if not isinstance(config, dict):
        return {
            "valid": False,
            "error": "Experiment configuration must be a dictionary.",
        }

    test_budget = config.get("test_budget", {})

    if test_budget.get("static") != test_budget.get("adaptive"):
        return {
            "valid": False,
            "error": "Static and adaptive test budgets must be equal.",
        }

    if test_budget.get("static", 0) <= 0:
        return {
            "valid": False,
            "error": "Test budget must be greater than zero.",
        }

    scenario = config.get("scenario", {})
    steps = scenario.get("steps", [])

    if not scenario.get("chain_id"):
        return {
            "valid": False,
            "error": "Scenario chain_id is required.",
        }

    if not steps:
        return {
            "valid": False,
            "error": "Scenario must contain at least one step.",
        }

    return {
        "valid": True,
        "error": None,
    }