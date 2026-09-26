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
        Run adaptive testing until the test budget is exhausted
        or there are no unexecuted tests remaining.

        Person 2 supplies experiment_id.
        Person 3 owns the adaptive planning logic.
        Person 4 owns sandbox execution.
        """

        if not experiment_id or not experiment_id.strip():
            raise ValueError(
                "experiment_id must not be empty."
            )

        if max_tests < 1:
            raise ValueError(
                "max_tests must be at least 1."
            )

        findings: list[Finding] = []

        for _ in range(max_tests):
            # Stop when every available test has already been used.
            unexecuted_tests = [
                test
                for test in planner_input.available_tests
                if test not in planner_input.previous_tests
            ]

            if not unexecuted_tests:
                break

            # Ask the adaptive planner for the next test.
            decision = self.planner.plan(planner_input)

            # Execute the selected test through Person 4's adapter.
            sandbox_result = execute_planned_test(
                decision,
                experiment_id,
            )

            # Record the executed test.
            planner_input.previous_tests.append(
                decision.selected_test
            )

            # A failed sandbox execution does not produce a finding.
            if sandbox_result["status"] == "failed":
                continue

            # Convert sandbox evidence to a string because Finding.evidence
            # currently expects a string.
            evidence = sandbox_result["evidence"]

            if not isinstance(evidence, str):
                evidence = str(evidence)

            finding = Finding(
                finding=sandbox_result["finding"],
                severity=sandbox_result["severity"],
                confidence=sandbox_result["confidence"],
                evidence=evidence,
            )

            # Add the new finding to the planner state.
            planner_input.findings.append(finding)

            # Keep the result in a local list for the caller.
            findings.append(finding)

        return findings