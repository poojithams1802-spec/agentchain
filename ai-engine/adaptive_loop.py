from typing import Any

from planner import AdaptivePlanner
from sandbox_adapter import execute_planned_test
from schemas import Finding, PlannerInput


class AdaptiveLoop:
    """
    Day-7 adaptive testing loop.

    Flow:
        PlannerInput
            ↓
        AdaptivePlanner
            ↓
        PlannerDecision
            ↓
        Sandbox execution
            ↓
        Finding
            ↓
        Updated planner state
            ↓
        Next planning iteration

    Person 3 owns the adaptive planning loop.
    Person 4 owns sandbox execution.
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
    def _unexecuted_tests(planner_input: PlannerInput) -> list[str]:
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
        """
        Run adaptive testing and return only findings.

        This is the original public API and remains backward-compatible.
        """

        self._validate_inputs(experiment_id, max_tests)

        findings: list[Finding] = []

        for _ in range(max_tests):
            unexecuted_tests = self._unexecuted_tests(planner_input)

            if not unexecuted_tests:
                break

            # Ask the adaptive planner for the next test.
            decision = self.planner.plan(planner_input)

            # Execute the selected test through Person 4's adapter.
            sandbox_result = execute_planned_test(
                decision,
                experiment_id,
            )

            # Record the attempted test.
            planner_input.previous_tests.append(
                decision.selected_test
            )

            # A failed sandbox execution does not produce a finding.
            if sandbox_result["status"] == "failed":
                continue

            finding = self._finding_from_sandbox_result(
                sandbox_result
            )

            # Add the new finding to the planner state.
            planner_input.findings.append(finding)

            # Keep the result in a local list for the caller.
            findings.append(finding)

        return findings

    def run_detailed(
        self,
        planner_input: PlannerInput,
        experiment_id: str,
        max_tests: int,
    ) -> dict[str, Any]:
        """
        Run adaptive testing while retaining the execution details
        required by the Day-7 static-vs-adaptive evaluation.

        This method is additive. Existing callers can continue using
        run(), which still returns list[Finding].

        P3 exposes the adaptive decisions and raw P4 execution results.
        P4 remains responsible for controlled execution, validation,
        execution-cost aggregation, and final comparison metrics.
        """

        self._validate_inputs(experiment_id, max_tests)

        findings: list[Finding] = []
        selected_tests: list[str] = []
        decisions: list[dict[str, Any]] = []
        execution_results: list[dict[str, Any]] = []

        # Capture the starting counters so this result reports usage
        # caused by this adaptive run, rather than pre-existing usage.
        initial_llm_calls = planner_input.budget_used.llm_calls
        initial_tests = planner_input.budget_used.tests

        fallback_used = False

        for _ in range(max_tests):
            unexecuted_tests = self._unexecuted_tests(planner_input)

            if not unexecuted_tests:
                break

            decision = self.planner.plan(planner_input)

            # Record planner-side decision information for P4's
            # adaptive evaluation. Keep the raw execution result below.
            selected_tests.append(decision.selected_test)
            decisions.append(
                {
                    "selected_test": decision.selected_test,
                    "reason": decision.reason,
                    "priority": decision.priority,
                    "confidence": decision.confidence,
                }
            )

            # The planner's fallback_decision() uses a reason beginning
            # with "Fallback". Record whether fallback was used at least once.
            if (
                isinstance(decision.reason, str)
                and decision.reason.strip().lower().startswith("fallback")
            ):
                fallback_used = True

            # Execute through P4's adapter. Any execution-cost metadata
            # returned by P4 is preserved unchanged in this record.
            sandbox_result = execute_planned_test(
                decision,
                experiment_id,
            )

            execution_results.append(sandbox_result)

            # Record the attempted test even when execution fails.
            planner_input.previous_tests.append(
                decision.selected_test
            )

            # A failed sandbox execution does not create a Finding.
            if sandbox_result["status"] == "failed":
                continue

            finding = self._finding_from_sandbox_result(
                sandbox_result
            )

            planner_input.findings.append(finding)
            findings.append(finding)

            # Keep the existing budget accounting available to callers.
            planner_input.budget_used.tests += 1

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
                0,
                final_llm_calls - initial_llm_calls,
            ),
            "llm_calls": final_llm_calls,
            "fallback_used": fallback_used,
            "budget_used": planner_input.budget_used.model_dump(),
            "budget_used_delta": {
                "tests": max(0, final_tests - initial_tests),
                "llm_calls": max(
                    0,
                    final_llm_calls - initial_llm_calls,
                ),
            },
        }
