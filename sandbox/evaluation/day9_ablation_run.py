import sys

sys.path.insert(0, "ai-engine")

from schemas import Finding

from planner import AdaptivePlanner
from sandbox_adapter import execute_planned_test

from .day8_ablation_inputs import (
    ABLATION_CONFIGURATIONS,
    build_day8_ablation_inputs,
)


def run_single_ablation_configuration(
    config_id,
    planner_input,
    experiment_id,
    max_tests=3,
):
    """
    Run one P3 ablation configuration through the
    real P4 controlled sandbox.

    P3 owns reasoning/configuration.
    P4 owns controlled execution and evaluation data.
    """

    if config_id not in ABLATION_CONFIGURATIONS:
        raise ValueError(
            "config_id must be one of A, B, C, or D."
        )

    if max_tests < 1:
        raise ValueError(
            "max_tests must be at least 1."
        )

    planner = AdaptivePlanner()

    selected_tests = []
    decisions = []
    execution_results = []
    findings = []

    fallback_count = 0
    initial_llm_calls = planner_input.budget_used.llm_calls

    for _ in range(max_tests):
        unexecuted_tests = [
            test
            for test in planner_input.available_tests
            if test not in planner_input.previous_tests
        ]

        if not unexecuted_tests:
            break

        decision = planner.plan(
            planner_input,
            configuration=config_id,
        )

        selected_tests.append(
            decision.selected_test
        )

        decisions.append(
            {
                "selected_test": decision.selected_test,
                "reason": decision.reason,
                "priority": decision.priority,
                "confidence": decision.confidence,
            }
        )

        if (
            isinstance(decision.reason, str)
            and decision.reason.strip().lower().startswith(
                "fallback"
            )
        ):
            fallback_count += 1

        sandbox_result = execute_planned_test(
            decision,
            experiment_id,
        )

        execution_results.append(
            sandbox_result
        )

        planner_input.previous_tests.append(
            decision.selected_test
        )

        if sandbox_result["status"] == "failed":
            continue

        evidence = sandbox_result["evidence"]

        if not isinstance(evidence, str):
            evidence = str(evidence)

        finding = Finding(
            finding=sandbox_result["finding"],
            severity=sandbox_result["severity"],
            confidence=sandbox_result["confidence"],
            evidence=evidence,
        )

        planner_input.findings.append(
            finding
        )

        findings.append(
            finding
        )

        planner_input.budget_used.tests += 1

    final_llm_calls = planner_input.budget_used.llm_calls

    return {
        "status": "completed",
        "experiment_id": experiment_id,
        "config_id": config_id,
        "configuration": {
            "name": ABLATION_CONFIGURATIONS[config_id]["name"]
            if isinstance(
                ABLATION_CONFIGURATIONS[config_id],
                dict,
            )
            else ABLATION_CONFIGURATIONS[config_id].name,
        },
        "selected_tests": selected_tests,
        "decisions": decisions,
        "execution_results": execution_results,
        "findings": findings,
        "tests_used": len(selected_tests),
        "llm_calls_used": max(
            0,
            final_llm_calls - initial_llm_calls,
        ),
        "fallback_count": fallback_count,
        "budget_used": planner_input.budget_used.model_dump(),
    }


def run_day9_ablation_experiments():
    """
    Prepare independent A/B/C/D states.

    This function currently returns the prepared inputs rather
    than immediately making four uncontrolled LLM runs.
    """

    inputs = build_day8_ablation_inputs()

    return {
        "study": "phase3_day9_ablation",
        "status": "prepared",
        "configurations": [
            {
                "config_id": item["config_id"],
                "name": item["name"],
                "use_rag": item["use_rag"],
                "use_chain_context": item["use_chain_context"],
                "planner_input": item["planner_input"],
            }
            for item in inputs
        ],
    }