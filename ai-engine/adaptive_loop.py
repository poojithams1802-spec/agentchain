
from typing import Any

from planner import AdaptivePlanner
from sandbox_adapter import execute_planned_test
from schemas import Finding, PlannerInput


class AdaptiveLoop:
    """
    Adaptive testing loop.

    Flow:
        PlannerInput
            -> AdaptivePlanner
            -> PlannerDecision
            -> Sandbox execution
            -> Finding
            -> Updated planner state

    Person 2 supplies experiment_id.
    Person 3 owns adaptive planning logic.
    Person 4 owns sandbox execution.
    """

    def __init__(
        self,
        planner: AdaptivePlanner | None = None,
    ) -> None:
        self.planner = planner or AdaptivePlanner()

    def run(
        self,
        planner_input: PlannerInput,
        experiment_id: str,
        max_tests: int,
    ) -> list[Finding]:
        """
        Run adaptive testing until the budget is exhausted
        or no unexecuted tests remain.

        Preserves the existing interface: returns list[Finding].
        """
        self._validate_run_inputs(experiment_id, max_tests)

        findings: list[Finding] = []

        for _ in range(max_tests):
            unexecuted_tests = [
                test
                for test in planner_input.available_tests
                if test not in planner_input.previous_tests
            ]

            if not unexecuted_tests:
                break

            decision = self.planner.plan(planner_input)

            sandbox_result = execute_planned_test(
                decision,
                experiment_id,
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

            planner_input.findings.append(finding)
            findings.append(finding)

        return findings

    def run_detailed(
        self,
        planner_input: PlannerInput,
        experiment_id: str,
        max_tests: int,
    ) -> dict[str, Any]:
        """
        Run adaptive testing and return detailed evaluation data,
        including decision records and planner source metadata.
        """
        self._validate_run_inputs(experiment_id, max_tests)

        findings: list[Finding] = []
        selected_tests: list[str] = []
        decisions: list[dict[str, Any]] = []
        execution_results: list[dict[str, Any]] = []
        decision_metadata_history: list[dict[str, Any]] = []

        fallback_used = False

        for _ in range(max_tests):
            unexecuted_tests = [
                test
                for test in planner_input.available_tests
                if test not in planner_input.previous_tests
            ]

            if not unexecuted_tests:
                break

            # Get the next adaptive testing decision.
            decision = self.planner.plan(planner_input)

            # Preserve the existing detailed-evaluation decision contract.
            decision_reason = getattr(decision, "reason", "")
            if not isinstance(decision_reason, str):
                decision_reason = ""

            decisions.append(
                {
                    "selected_test": decision.selected_test,
                    "reason": decision_reason,
                }
            )

            # Capture metadata before the next planner call can overwrite it.
            raw_metadata = getattr(
                self.planner,
                "last_decision_metadata",
                None,
            )

            if isinstance(raw_metadata, dict):
                decision_metadata = dict(raw_metadata)
            else:
                decision_metadata = {
                    "decision_source": "unknown",
                    "fallback_reason": None,
                    "rag_retrieval_status": "unknown",
                    "rag_context_retrieved": None,
                    "rag_context_used": None,
                    "decision_recovery": None,
                }

            decision_metadata_history.append(decision_metadata)

            decision_source = decision_metadata.get(
                "decision_source",
                "unknown",
            )

            if (
                decision_source == "deterministic_fallback"
                or decision_reason.strip().lower().startswith("fallback")
            ):
                fallback_used = True

            selected_tests.append(decision.selected_test)

            # Execute the selected test in the sandbox.
            sandbox_result = execute_planned_test(
                decision,
                experiment_id,
            )

            execution_results.append(sandbox_result)

            # Mark the test as attempted, including failed executions.
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

            planner_input.findings.append(finding)
            findings.append(finding)

            planner_input.budget_used.tests += 1

        return {
            "status": "completed",
            "experiment_id": experiment_id,
            "selected_tests": selected_tests,
            "tests_used": len(selected_tests),
            "decisions": decisions,
            "execution_results": execution_results,
            "findings": findings,
            "llm_calls": planner_input.budget_used.llm_calls,
            "fallback_used": fallback_used,
            "decision_metadata": decision_metadata_history,
            "budget_used": planner_input.budget_used.model_dump(),
        }

    @staticmethod
    def _validate_run_inputs(
        experiment_id: str,
        max_tests: int,
    ) -> None:
        """Validate inputs shared by run() and run_detailed()."""
        if not experiment_id or not experiment_id.strip():
            raise ValueError("experiment_id must not be empty.")

        if max_tests < 1:
            raise ValueError("max_tests must be at least 1.")