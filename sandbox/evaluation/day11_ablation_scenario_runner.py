"""
Phase 3 Day 11 - Common Ablation Scenario Runner.

Person 4 responsibility:
- define one controlled common scenario
- build an isolated PlannerInput from that scenario
- execute the same initial scenario across A/B/C/D
- verify that scenario state is not shared between configurations

Person 3 remains responsible for planner/ablation reasoning.
This module must not duplicate planner selection logic.
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
from typing import Any


# ---------------------------------------------------------
# Make ai-engine importable when this module is run from
# the AgentChain project root.
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]
AI_ENGINE_PATH = PROJECT_ROOT / "ai-engine"

if str(AI_ENGINE_PATH) not in sys.path:
    sys.path.insert(0, str(AI_ENGINE_PATH))


from ablation import list_ablation_configurations
from planner import AdaptivePlanner
from schemas import PlannerInput, TestingBudget


# ---------------------------------------------------------
# Common controlled scenario
# ---------------------------------------------------------

DAY11_COMMON_SCENARIO: dict[str, Any] = {
    "study": "phase3_day11_ablation_framework",
    "experiment_version": "day11-v1",
    "scenario_version": "sandbox-v1",
    "scenario_id": "DAY11-COMMON-001",
    "random_seed": 42,

    # Keep this scenario deterministic and controlled.
    # Day 11 validates the framework; Day 12 performs
    # the broader ablation experiments.
    "available_tests": [
        "permission_test",
        "tool_access_test",
        "memory_access_test",
    ],

    "initial_findings": [],

    "previous_tests": [],

    "chain_state": {
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
        "validation_result": {},
    },

    "budget": {
        "max_tests": 3,
        "max_llm_calls": 3,
        "max_time_seconds": 30.0,
    },
}


# ---------------------------------------------------------
# Scenario helpers
# ---------------------------------------------------------

def get_day11_common_scenario() -> dict[str, Any]:
    """
    Return a deep copy of the common controlled scenario.

    Each caller receives independent state so that one
    ablation configuration cannot modify another.
    """

    return deepcopy(DAY11_COMMON_SCENARIO)


def validate_day11_common_scenario(
    scenario: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Validate the Day 11 common scenario definition.

    The validation is intentionally deterministic and only
    checks the controlled framework inputs.
    """

    if scenario is None:
        scenario = DAY11_COMMON_SCENARIO

    if not isinstance(scenario, dict):
        return {
            "valid": False,
            "error": "Scenario must be a dictionary.",
        }

    expected_tests = [
        "permission_test",
        "tool_access_test",
        "memory_access_test",
    ]

    if scenario.get("available_tests") != expected_tests:
        return {
            "valid": False,
            "error": (
                "Day 11 common scenario must use the approved "
                "three-test scenario."
            ),
        }

    if scenario.get("previous_tests") != []:
        return {
            "valid": False,
            "error": (
                "Day 11 common scenario must start with no "
                "previously executed tests."
            ),
        }

    chain_state = scenario.get("chain_state", {})

    if chain_state.get("chain_id") != "CHAIN-AUTH-TOOL-MEM":
        return {
            "valid": False,
            "error": "Unexpected Day 11 chain_id.",
        }

    if chain_state.get("ordered_steps") != expected_tests:
        return {
            "valid": False,
            "error": (
                "Day 11 chain steps must match "
                "available_tests."
            ),
        }

    budget = scenario.get("budget", {})

    if budget.get("max_tests") != 3:
        return {
            "valid": False,
            "error": "Day 11 requires max_tests=3.",
        }

    if budget.get("max_llm_calls") != 3:
        return {
            "valid": False,
            "error": "Day 11 requires max_llm_calls=3.",
        }

    if budget.get("max_time_seconds") != 30.0:
        return {
            "valid": False,
            "error": "Day 11 requires max_time_seconds=30.0.",
        }

    return {
        "valid": True,
        "error": None,
    }


# ---------------------------------------------------------
# PlannerInput construction
# ---------------------------------------------------------

def build_day11_planner_input(
    scenario: dict[str, Any] | None = None,
) -> PlannerInput:
    """
    Convert the controlled scenario definition into one
    PlannerInput.

    The returned object is independent from the source
    scenario.
    """

    if scenario is None:
        scenario = get_day11_common_scenario()

    validation = validate_day11_common_scenario(
        scenario
    )

    if not validation["valid"]:
        raise ValueError(
            validation["error"]
        )

    return PlannerInput(
        findings=[],
        previous_tests=list(
            scenario["previous_tests"]
        ),
        available_tests=list(
            scenario["available_tests"]
        ),
        retrieved_knowledge=[],
        chain_state=deepcopy(
            scenario["chain_state"]
        ),
        testing_budget=TestingBudget(
            max_tests=scenario["budget"]["max_tests"],
            max_llm_calls=scenario["budget"]["max_llm_calls"],
            max_time_seconds=scenario["budget"]["max_time_seconds"],
        ),
    )


def build_day11_ablation_inputs(
    scenario: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """
    Build one independent PlannerInput for each A/B/C/D
    configuration.

    Only the configuration metadata differs.
    The actual initial scenario state is identical.
    """

    if scenario is None:
        scenario = get_day11_common_scenario()

    validation = validate_day11_common_scenario(
        scenario
    )

    if not validation["valid"]:
        raise ValueError(
            validation["error"]
        )

    results = []

    for configuration in list_ablation_configurations():
        results.append(
            {
                "config_id": configuration.config_id,
                "name": configuration.name,
                "use_rag": configuration.use_rag,
                "use_chain_context": (
                    configuration.use_chain_context
                ),
                "planner_input": (
                    build_day11_planner_input(
                        scenario
                    )
                ),
            }
        )

    return results


# ---------------------------------------------------------
# Common scenario runner
# ---------------------------------------------------------

def run_day11_common_scenario(
    scenario: dict[str, Any] | None = None,
    max_steps: int = 1,
    planner: AdaptivePlanner | None = None,
) -> dict[str, Any]:
    """
    Run the same initial controlled scenario through all
    four ablation configurations.

    Person 3's AdaptivePlanner owns the planner-level
    ablation behavior. Person 4 owns the common scenario
    definition and execution boundary.

    The planner receives one fresh PlannerInput containing
    the same initial state for A/B/C/D.
    """

    if not isinstance(max_steps, int):
        raise TypeError(
            "max_steps must be an integer."
        )

    if max_steps < 0:
        raise ValueError(
            "max_steps must be greater than or equal to 0."
        )

    if scenario is None:
        scenario = get_day11_common_scenario()

    validation = validate_day11_common_scenario(
        scenario
    )

    if not validation["valid"]:
        raise ValueError(
            validation["error"]
        )

    base_input = build_day11_planner_input(
        scenario
    )

    if planner is None:
        planner = AdaptivePlanner()

    result = planner.run_ablation_suite(
        base_input,
        max_steps=max_steps,
    )

    return {
        "study": "phase3_day11_ablation_framework",
        "status": "completed",
        "scenario_id": scenario["scenario_id"],
        "experiment_version": scenario["experiment_version"],
        "scenario_version": scenario["scenario_version"],
        "random_seed": scenario["random_seed"],
        "same_initial_state": True,
        "runner_scope": "common_scenario",
        "max_steps": max_steps,
        "configurations": result["configurations"],
    }