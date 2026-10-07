"""
Day 8 P4 controlled ablation scenario.

Every ablation configuration (A, B, C, D) must receive
the same initial security scenario, available tests,
chain definition, and testing budget.

P4 owns the controlled scenario definition.
"""


DAY8_ABLATION_SCENARIO = {
    "experiment_version": "day8-v1",
    "scenario_version": "sandbox-v1",

    "scenario_id": "DAY8-IDENTICAL-001",

    "chain": {
        "chain_id": "CHAIN-AUTH-TOOL-MEM",
        "ordered_steps": [
            "permission_test",
            "tool_access_test",
            "memory_access_test",
        ],
        "dependencies": {
            "permission_test": [],
            "tool_access_test": [
                "permission_test",
            ],
            "memory_access_test": [
                "tool_access_test",
            ],
        },
    },

    "available_tests": [
        "permission_test",
        "tool_access_test",
        "memory_access_test",
    ],

    "initial_findings": [],

    "previous_tests": [],

    "budget": {
        "max_tests": 3,
        "max_llm_calls": 3,
        "max_time_seconds": 30.0,
    },

    "random_seed": 42,
}


def get_day8_ablation_scenario():
    """
    Return an independent copy of the same controlled scenario.

    Each ablation configuration gets its own copy so that
    execution state cannot leak between configurations.
    """

    return {
        **DAY8_ABLATION_SCENARIO,
        "chain": {
            **DAY8_ABLATION_SCENARIO["chain"],
            "ordered_steps": (
                DAY8_ABLATION_SCENARIO["chain"]["ordered_steps"].copy()
            ),
            "dependencies": {
                key: value.copy()
                for key, value in (
                    DAY8_ABLATION_SCENARIO["chain"]["dependencies"]
                    .items()
                )
            },
        },
        "available_tests": (
            DAY8_ABLATION_SCENARIO["available_tests"].copy()
        ),
        "initial_findings": (
            DAY8_ABLATION_SCENARIO["initial_findings"].copy()
        ),
        "previous_tests": (
            DAY8_ABLATION_SCENARIO["previous_tests"].copy()
        ),
        "budget": DAY8_ABLATION_SCENARIO["budget"].copy(),
    }


def validate_day8_ablation_scenario(
    scenario=None,
):
    """
    Validate the controlled Day 8 scenario.
    """

    if scenario is None:
        scenario = DAY8_ABLATION_SCENARIO

    if not isinstance(scenario, dict):
        return {
            "valid": False,
            "error": "Scenario must be a dictionary.",
        }

    required_tests = [
        "permission_test",
        "tool_access_test",
        "memory_access_test",
    ]

    if scenario.get("available_tests") != required_tests:
        return {
            "valid": False,
            "error": "Day 8 must use the approved three-test scenario.",
        }

    chain = scenario.get("chain", {})

    if chain.get("chain_id") != "CHAIN-AUTH-TOOL-MEM":
        return {
            "valid": False,
            "error": "Unexpected Day 8 chain_id.",
        }

    if chain.get("ordered_steps") != required_tests:
        return {
            "valid": False,
            "error": "Chain steps must match the approved test sequence.",
        }

    budget = scenario.get("budget", {})

    if budget.get("max_tests") != 3:
        return {
            "valid": False,
            "error": "All Day 8 configurations must use max_tests=3.",
        }

    if budget.get("max_llm_calls") != 3:
        return {
            "valid": False,
            "error": "All Day 8 configurations must use max_llm_calls=3.",
        }

    return {
        "valid": True,
        "error": None,
    }