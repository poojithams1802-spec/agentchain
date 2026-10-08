"""
Phase 3 Day 12 - Ablation Metrics.

Person 4 responsibility:
- validate A/B/C/D ablation result structure
- calculate comparable metrics from available evidence
- report N/A when a metric is not applicable or not measured
- never silently convert unavailable metrics to zero
"""

from __future__ import annotations

from typing import Any


EXPECTED_CONFIGURATIONS = {
    "A": {
        "name": "llm_only",
        "use_rag": False,
        "use_chain_context": False,
    },
    "B": {
        "name": "llm_rag",
        "use_rag": True,
        "use_chain_context": False,
    },
    "C": {
        "name": "llm_chain",
        "use_rag": False,
        "use_chain_context": True,
    },
    "D": {
        "name": "llm_rag_chain",
        "use_rag": True,
        "use_chain_context": True,
    },
}

NA = "N/A"


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def validate_day12_ablation_result(
    result: dict[str, Any],
) -> dict[str, Any]:
    """
    Validate the structural requirements for a comparable A/B/C/D run.

    This function does not reject a failed experiment merely because it
    failed. Failed experiments must remain represented for research
    reporting.
    """
    errors: list[str] = []

    if not isinstance(result, dict):
        return {
            "valid": False,
            "errors": ["Result must be a dictionary."],
        }

    if result.get("same_initial_state") is not True:
        errors.append("same_initial_state must be True.")

    configurations = result.get("configurations")

    if not isinstance(configurations, list):
        errors.append("configurations must be a list.")
        return {"valid": False, "errors": errors}

    if len(configurations) != 4:
        errors.append(
            f"Expected 4 configurations, found {len(configurations)}."
        )

    seen: set[str] = set()

    for entry in configurations:
        if not isinstance(entry, dict):
            errors.append("Each configuration entry must be a dictionary.")
            continue

        config = _as_dict(entry.get("configuration"))
        config_id = config.get("config_id")

        if config_id not in EXPECTED_CONFIGURATIONS:
            errors.append(
                f"Unexpected config_id: {config_id!r}."
            )
            continue

        if config_id in seen:
            errors.append(
                f"Duplicate configuration: {config_id}."
            )
        seen.add(config_id)

        expected = EXPECTED_CONFIGURATIONS[config_id]

        for field in ("name", "use_rag", "use_chain_context"):
            if config.get(field) != expected[field]:
                errors.append(
                    f"{config_id}.{field} does not match expected value."
                )

    missing = set(EXPECTED_CONFIGURATIONS) - seen

    for config_id in sorted(missing):
        errors.append(
            f"Missing configuration: {config_id}."
        )

    return {
        "valid": len(errors) == 0,
        "errors": errors,
    }


def _count_fallbacks(decisions: list[dict[str, Any]]) -> int:
    """
    Count fallback decisions using explicit metadata when present.

    Older Day 11 records may not expose a dedicated fallback boolean, so
    the reason string is used only as a compatibility fallback.
    """
    count = 0

    for decision in decisions:
        if decision.get("fallback") is True:
            count += 1
            continue

        reason = str(decision.get("reason", "")).lower()

        if "fallback" in reason:
            count += 1

    return count


def calculate_configuration_metrics(
    configuration_result: dict[str, Any],
    expected_tests: list[str] | None = None,
) -> dict[str, Any]:
    """
    Calculate metrics that can be supported by a planner result.

    Metrics requiring actual sandbox execution are deliberately reported
    as N/A until execution evidence is supplied.
    """
    config = _as_dict(configuration_result.get("configuration"))

    selected_tests = configuration_result.get("selected_tests", [])
    if not isinstance(selected_tests, list):
        selected_tests = []

    decisions = configuration_result.get("decisions", [])
    if not isinstance(decisions, list):
        decisions = []

    budget_used = _as_dict(
        configuration_result.get("budget_used")
    )

    remaining_budget = _as_dict(
        configuration_result.get("remaining_budget")
    )

    tests_used = budget_used.get("tests")
    llm_calls = budget_used.get("llm_calls")
    time_seconds = budget_used.get("time_seconds")

    metrics: dict[str, Any] = {
        "config_id": config.get("config_id", NA),
        "name": config.get("name", NA),

        # Ablation configuration
        "use_rag": config.get("use_rag", NA),
        "use_chain_context": config.get(
            "use_chain_context",
            NA,
        ),

        # Planner-level metrics
        "tests_requested": configuration_result.get(
            "tests_requested",
            NA,
        ),
        "tests_selected": configuration_result.get(
            "tests_selected",
            len(selected_tests),
        ),
        "tests_to_discovery": NA,
        "llm_calls": llm_calls if llm_calls is not None else NA,
        "fallback_count": _count_fallbacks(decisions),

        # Budget
        "budget_tests_used": tests_used if tests_used is not None else NA,
        "budget_llm_calls_used": (
            llm_calls if llm_calls is not None else NA
        ),
        "budget_time_used_seconds": (
            time_seconds if time_seconds is not None else NA
        ),
        "remaining_tests": remaining_budget.get(
            "tests",
            NA,
        ),
        "remaining_llm_calls": remaining_budget.get(
            "llm_calls",
            NA,
        ),
        "remaining_time_seconds": remaining_budget.get(
            "time_seconds",
            NA,
        ),

        # Selection accuracy
        "adaptive_selection_accuracy": NA,

        # Discovery metrics
        "tests_executed": NA,
        "vulnerabilities_discovered": NA,
        "chains_discovered": NA,
        "validated_chains": NA,
        "average_chain_length": NA,
        "maximum_chain_depth": NA,

        # Mitigation metrics
        "mitigation_selection_accuracy": NA,
        "mitigation_success": NA,
        "attack_success_before": NA,
        "attack_success_after": NA,
        "chain_disruption_rate": NA,
        "mitigation_validation_rate": NA,
        "residual_vulnerable_steps": NA,
        "residual_chain_length": NA,

        # Performance metrics
        "rag_time_seconds": NA,
        "prompt_build_time_seconds": NA,
        "llm_time_seconds": NA,
        "total_selection_time_seconds": NA,
        "replay_time_seconds": NA,
        "end_to_end_experiment_time_seconds": NA,

        # Execution state
        "status": configuration_result.get(
            "status",
            NA,
        ),
    }

    # Calculate selection accuracy only when an explicit ground truth
    # sequence is supplied.
    if expected_tests:
        comparisons = min(
            len(expected_tests),
            len(selected_tests),
        )

        if comparisons > 0:
            correct = sum(
                1
                for index in range(comparisons)
                if selected_tests[index]
                == expected_tests[index]
            )

            metrics["adaptive_selection_accuracy"] = (
                correct / comparisons
            )

    return metrics


def calculate_day12_ablation_metrics(
    result: dict[str, Any],
    expected_tests: list[str] | None = None,
) -> dict[str, Any]:
    """
    Calculate comparable Day 12 metrics for A/B/C/D.
    """
    validation = validate_day12_ablation_result(result)

    configurations = result.get("configurations", [])

    calculated = []

    if isinstance(configurations, list):
        for entry in configurations:
            if isinstance(entry, dict):
                calculated.append(
                    calculate_configuration_metrics(
                        entry,
                        expected_tests=expected_tests,
                    )
                )

    return {
        "study": "phase3_day12_ablation_experiments",
        "status": "completed",
        "validation": validation,
        "scenario_id": result.get(
            "scenario_id",
            NA,
        ),
        "experiment_version": result.get(
            "experiment_version",
            NA,
        ),
        "scenario_version": result.get(
            "scenario_version",
            NA,
        ),
        "random_seed": result.get(
            "random_seed",
            NA,
        ),
        "same_initial_state": result.get(
            "same_initial_state",
            False,
        ),
        "configurations": calculated,
    }