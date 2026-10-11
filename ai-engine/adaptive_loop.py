
from time import perf_counter
from typing import Any

from planner import AdaptivePlanner
from sandbox_adapter import execute_planned_test
from schemas import Finding, PlannerInput


class AdaptiveLoop:
    """
    Adaptive testing loop with execution and planning measurements.

    P3 owns adaptive planning.
    P4 owns sandbox execution and validation.
    """

    def __init__(
        self,
        planner: AdaptivePlanner | None = None,
    ) -> None:
        self.planner = planner or AdaptivePlanner()

    @staticmethod
    def _validate_inputs(
        experiment_id: str,
        max_tests: int,
    ) -> None:
        if not experiment_id or not experiment_id.strip():
            raise ValueError("experiment_id must not be empty.")
        if max_tests < 1:
            raise ValueError("max_tests must be at least 1.")

    @staticmethod
    def _unexecuted_tests(
        planner_input: PlannerInput,
    ) -> list[str]:
        return [
            test
            for test in planner_input.available_tests
            if test not in planner_input.previous_tests
        ]

    @staticmethod
    def _finding_from_sandbox_result(
        sandbox_result: dict[str, Any],
    ) -> Finding:
        evidence = sandbox_result["evidence"]
        if not isinstance(evidence, str):
            evidence = str(evidence)

        return Finding(
            finding=sandbox_result["finding"],
            severity=sandbox_result["severity"],
            confidence=sandbox_result["confidence"],
            evidence=evidence,
        )

    def run(
        self,
        planner_input: PlannerInput,
        experiment_id: str,
        max_tests: int,
    ) -> list[Finding]:
        """Backward-compatible API returning only findings."""
        return self.run_detailed(
            planner_input=planner_input,
            experiment_id=experiment_id,
            max_tests=max_tests,
        )["findings"]

    def run_detailed(
        self,
        planner_input: PlannerInput,
        experiment_id: str,
        max_tests: int,
    ) -> dict[str, Any]:
        """
        Run adaptive testing and return findings, raw P4 execution
        results, budget information, and timing measurements.

        planning_latency_seconds measures the complete planner.plan()
        call, including retrieval and any LLM request.
        """

        self._validate_inputs(experiment_id, max_tests)

        total_start = perf_counter()

        findings: list[Finding] = []
        selected_tests: list[str] = []
        decisions: list[dict[str, Any]] = []
        execution_results: list[dict[str, Any]] = []
        planning_latencies: list[float] = []
        sandbox_latencies: list[float] = []

        initial_llm_calls = planner_input.budget_used.llm_calls
        initial_tests = planner_input.budget_used.tests
        fallback_used = False

        for _ in range(max_tests):
            unexecuted_tests = self._unexecuted_tests(planner_input)
            if not unexecuted_tests:
                break

            # Measure the complete planning call.
            planning_start = perf_counter()
            decision = self.planner.plan(planner_input)
            planning_seconds = perf_counter() - planning_start
            planning_latencies.append(planning_seconds)

            selected_tests.append(decision.selected_test)
            decisions.append(
                {
                    "selected_test": decision.selected_test,
                    "reason": decision.reason,
                    "priority": decision.priority,
                    "confidence": decision.confidence,
                    "planning_latency_seconds": planning_seconds,
                }
            )

            if (
                isinstance(decision.reason, str)
                and decision.reason.strip().lower().startswith("fallback")
            ):
                fallback_used = True

            # Measure the adapter call. P4's own execution_cost remains
            # preserved unchanged in the raw result.
            sandbox_start = perf_counter()
            sandbox_result = execute_planned_test(
                decision,
                experiment_id,
            )
            sandbox_elapsed = perf_counter() - sandbox_start
            sandbox_latencies.append(sandbox_elapsed)

            execution_results.append(sandbox_result)
            planner_input.previous_tests.append(decision.selected_test)

            if sandbox_result["status"] == "failed":
                continue

            finding = self._finding_from_sandbox_result(sandbox_result)
            planner_input.findings.append(finding)
            findings.append(finding)
            planner_input.budget_used.tests += 1

        total_runtime = perf_counter() - total_start

        final_llm_calls = planner_input.budget_used.llm_calls
        final_tests = planner_input.budget_used.tests

        return {
            "status": "completed",
            "experiment_id": experiment_id,
            "tests_used": len(selected_tests),
            "selected_tests": selected_tests,
            "decisions": decisions,
            "execution_results": execution_results,
            "findings": findings,
            "llm_calls_used": max(
                0, final_llm_calls - initial_llm_calls
            ),
            "llm_calls": final_llm_calls,
            "fallback_used": fallback_used,
            "budget_used": planner_input.budget_used.model_dump(),
            "budget_used_delta": {
                "tests": max(0, final_tests - initial_tests),
                "llm_calls": max(
                    0, final_llm_calls - initial_llm_calls
                ),
            },
            "timing": {
                "total_runtime_seconds": total_runtime,
                "total_planning_time_seconds": sum(planning_latencies),
                "planning_latency_seconds": planning_latencies,
                "total_sandbox_adapter_time_seconds": sum(sandbox_latencies),
                "sandbox_adapter_latency_seconds": sandbox_latencies,
            },
        }
