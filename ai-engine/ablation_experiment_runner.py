from __future__ import annotations

import copy
import json
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable

from ablation import get_ablation_configuration
from schemas import Finding, AblationConfiguration, PlannerInput

if TYPE_CHECKING:
    from planner import AdaptivePlanner


ExecutionFunction = Callable[[Any, str], dict[str, Any]]
ResetFunction = Callable[[str], Any]


class AblationExperimentRunner:
    """
    Phase 3 Day 12 ablation experiment runner.

    Runs configurations A-D from the same initial PlannerInput and
    executes the selected sandbox tests through the existing P4 adapter.

    P3 owns:
        - configuration selection
        - planner execution
        - experiment-level measurement
        - comparison-ready result assembly

    P4 owns:
        - controlled sandbox execution
        - vulnerability behavior
        - mitigation state and replay behavior

    P2 owns:
        - production experiment IDs
        - persistence / database records

    This runner therefore accepts experiment IDs from the caller instead
    of generating production experiment IDs itself.
    """

    CONFIGURATION_ORDER = ("A", "B", "C", "D")

    def __init__(
        self,
        planner: "AdaptivePlanner" | None = None,
        executor: ExecutionFunction | None = None,
        reset_hook: ResetFunction | None = None,
    ) -> None:
        if planner is None:
            # Import lazily so tests that inject a deterministic planner do
            # not require GEMINI_API_KEY just to import this module.
            from planner import AdaptivePlanner

            planner = AdaptivePlanner()

        self.planner = planner

        if executor is None:
            # Import lazily so planner-only tests remain independent from
            # the sandbox package and its runtime environment.
            from sandbox_adapter import execute_planned_test

            self.executor = execute_planned_test
        else:
            self.executor = executor

        self.reset_hook = reset_hook

    # ------------------------------------------------------------------
    # Validation helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_experiment_id(experiment_id: str) -> str:
        if not isinstance(experiment_id, str) or not experiment_id.strip():
            raise ValueError(
                "experiment_id must be a non-empty string."
            )

        return experiment_id.strip()

    @staticmethod
    def _validate_max_tests(max_tests: int) -> int:
        if not isinstance(max_tests, int):
            raise TypeError("max_tests must be an integer.")

        if max_tests < 1:
            raise ValueError("max_tests must be at least 1.")

        return max_tests

    @staticmethod
    def _validate_execution_result(
        result: dict[str, Any],
    ) -> dict[str, Any]:
        if not isinstance(result, dict):
            raise ValueError(
                "Sandbox executor must return a dictionary."
            )

        required_fields = {
            "status",
            "test",
            "finding",
            "severity",
            "evidence",
            "confidence",
        }

        missing = required_fields - result.keys()

        if missing:
            raise ValueError(
                "Sandbox response is missing fields: "
                f"{sorted(missing)}"
            )

        if result["status"] not in {"completed", "failed"}:
            raise ValueError(
                f"Invalid sandbox status: {result['status']}"
            )

        confidence = result["confidence"]

        if not isinstance(confidence, (int, float)):
            raise ValueError(
                "Sandbox confidence must be numeric."
            )

        if not 0.0 <= float(confidence) <= 1.0:
            raise ValueError(
                "Sandbox confidence must be between 0.0 and 1.0."
            )

        return result

    @staticmethod
    def _finding_from_result(
        result: dict[str, Any],
    ) -> Finding:
        evidence = result["evidence"]

        if not isinstance(evidence, str):
            evidence = str(evidence)

        return Finding(
            finding=str(result["finding"]),
            severity=str(result["severity"]),
            confidence=float(result["confidence"]),
            evidence=evidence,
        )

    @staticmethod
    def _selection_accuracy(
        selected_tests: list[str],
        expected_test_sequence: list[str] | None,
    ) -> float | None:
        """
        Calculate selection accuracy only when a controlled expected
        sequence is supplied by the experiment designer.

        No ground truth is invented when the caller does not provide it.
        """

        if expected_test_sequence is None:
            return None

        if not expected_test_sequence:
            return 0.0

        comparisons = min(
            len(selected_tests),
            len(expected_test_sequence),
        )

        if comparisons == 0:
            return 0.0

        correct = sum(
            selected_tests[index]
            == expected_test_sequence[index]
            for index in range(comparisons)
        )

        return round(
            correct / len(expected_test_sequence),
            4,
        )

    @staticmethod
    def _extract_chain_metrics(
        planner_state: PlannerInput,
    ) -> dict[str, Any]:
        """
        Read chain metrics already supplied by the controlled chain
        executor/validator.

        This method does not invent or validate chain results.
        """

        chain_state = planner_state.chain_state or {}
        validation_result = chain_state.get(
            "validation_result",
            {},
        )

        if not isinstance(validation_result, dict):
            validation_result = {}

        candidate_chains = chain_state.get(
            "candidate_chains",
            [],
        )
        validated_chains = chain_state.get(
            "validated_chains",
            [],
        )
        residual_steps = validation_result.get(
            "residual_vulnerable_steps",
            validation_result.get("residual_steps", []),
        )

        if not isinstance(candidate_chains, list):
            candidate_chains = []

        if not isinstance(validated_chains, list):
            validated_chains = []

        if not isinstance(residual_steps, list):
            residual_steps = []

        return {
            "candidate_chains": copy.deepcopy(candidate_chains),
            "validated_chains": copy.deepcopy(validated_chains),
            "validation_rate": validation_result.get(
                "validation_rate"
            ),
            "chain_disrupted": validation_result.get(
                "disrupted"
            ),
            "residual_vulnerable_steps": copy.deepcopy(
                residual_steps
            ),
        }

    # ------------------------------------------------------------------
    # One configuration
    # ------------------------------------------------------------------

    def run_configuration(
        self,
        planner_input: PlannerInput,
        configuration: str | AblationConfiguration,
        experiment_id: str,
        max_tests: int | None = None,
        expected_test_sequence: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Execute one ablation configuration.

        The caller's PlannerInput is never mutated. Each configuration
        receives its own deep copy so A-D start from identical state.
        """

        experiment_id = self._validate_experiment_id(
            experiment_id
        )

        config = get_ablation_configuration(
            configuration
        )

        state = copy.deepcopy(planner_input)

        if max_tests is None:
            max_tests = state.testing_budget.max_tests

        max_tests = self._validate_max_tests(max_tests)

        if self.reset_hook is not None:
            self.reset_hook(experiment_id)

        selected_tests: list[str] = []
        findings: list[Finding] = []
        decisions: list[dict[str, Any]] = []
        execution_records: list[dict[str, Any]] = []
        errors: list[str] = []

        planner_time_seconds = 0.0
        execution_time_seconds = 0.0
        total_time_start = time.perf_counter()

        status = "completed"

        for step_index in range(max_tests):
            if self.planner.budget_exhausted(state):
                status = "budget_exhausted"
                break

            unexecuted_tests = [
                test
                for test in state.available_tests
                if test not in state.previous_tests
            ]

            if not unexecuted_tests:
                break

            # ------------------------------------------------------
            # P3 adaptive planning
            # ------------------------------------------------------

            planner_start = time.perf_counter()

            try:
                decision = self.planner.plan(
                    state,
                    configuration=config,
                )
            except Exception as error:
                planner_elapsed = (
                    time.perf_counter() - planner_start
                )
                planner_time_seconds += planner_elapsed
                errors.append(
                    f"Planner step {step_index + 1}: "
                    f"{type(error).__name__}: {error}"
                )
                status = "failed"
                break

            planner_elapsed = (
                time.perf_counter() - planner_start
            )
            planner_time_seconds += planner_elapsed

            selected_tests.append(
                decision.selected_test
            )

            decisions.append(
                {
                    "step": step_index + 1,
                    "selected_test": decision.selected_test,
                    "reason": decision.reason,
                    "priority": decision.priority,
                    "confidence": decision.confidence,
                    "planner_time_seconds": round(
                        planner_elapsed,
                        6,
                    ),
                }
            )

            # Record the selected test before execution, matching the
            # existing AdaptiveLoop/P4 contract.
            state.previous_tests.append(
                decision.selected_test
            )
            state.budget_used.tests += 1

            # ------------------------------------------------------
            # P4 controlled sandbox execution
            # ------------------------------------------------------

            execution_start = time.perf_counter()

            try:
                raw_result = self.executor(
                    decision,
                    experiment_id,
                )
                sandbox_result = self._validate_execution_result(
                    raw_result
                )
            except Exception as error:
                execution_elapsed = (
                    time.perf_counter() - execution_start
                )
                execution_time_seconds += execution_elapsed

                execution_records.append(
                    {
                        "step": step_index + 1,
                        "test": decision.selected_test,
                        "status": "failed",
                        "error": (
                            f"{type(error).__name__}: {error}"
                        ),
                        "execution_time_seconds": round(
                            execution_elapsed,
                            6,
                        ),
                    }
                )

                errors.append(
                    f"Execution step {step_index + 1}: "
                    f"{type(error).__name__}: {error}"
                )

                # Charge the measured iteration time to the shared
                # adaptive budget even when the sandbox execution fails.
                state.budget_used.time_seconds += (
                    planner_elapsed + execution_elapsed
                )

                if self.planner.budget_exhausted(state):
                    status = "budget_exhausted"
                    break

                # Continue the experiment with the next controlled test.
                continue

            execution_elapsed = (
                time.perf_counter() - execution_start
            )
            execution_time_seconds += execution_elapsed

            execution_records.append(
                {
                    "step": step_index + 1,
                    "test": decision.selected_test,
                    "status": sandbox_result["status"],
                    "finding": sandbox_result["finding"],
                    "severity": sandbox_result["severity"],
                    "confidence": sandbox_result["confidence"],
                    "execution_time_seconds": round(
                        execution_elapsed,
                        6,
                    ),
                    "mitigation_applied": sandbox_result.get(
                        "mitigation_applied"
                    ),
                    "mitigation_control": sandbox_result.get(
                        "mitigation_control"
                    ),
                }
            )

            if sandbox_result["status"] == "failed":
                continue

            finding = self._finding_from_result(
                sandbox_result
            )

            state.findings.append(finding)
            findings.append(finding)

            # ------------------------------------------------------
            # Adaptive time budget
            # ------------------------------------------------------

            iteration_elapsed = (
                planner_elapsed + execution_elapsed
            )
            state.budget_used.time_seconds += iteration_elapsed

            if self.planner.budget_exhausted(state):
                status = "budget_exhausted"
                break

        total_time_seconds = (
            time.perf_counter() - total_time_start
        )

        # Include failed execution time in the budget even when the
        # execution raised before producing a normal sandbox response.
        measured_time = (
            planner_time_seconds
            + execution_time_seconds
        )

        if state.budget_used.time_seconds < measured_time:
            state.budget_used.time_seconds = measured_time

        if (
            status == "completed"
            and self.planner.budget_exhausted(state)
            and len(selected_tests) < max_tests
        ):
            status = "budget_exhausted"

        chain_metrics = self._extract_chain_metrics(
            state
        )

        execution_successes = sum(
            1
            for record in execution_records
            if record.get("status") == "completed"
        )

        execution_attempts = len(execution_records)

        execution_success_rate = (
            execution_successes / execution_attempts
            if execution_attempts
            else 0.0
        )

        fallback_used = any(
            "fallback" in str(
                decision.get("reason", "")
            ).lower()
            for decision in decisions
        )

        return {
            "experiment_id": experiment_id,
            "study": "phase3_ablation",
            "configuration": config.model_dump(),
            "runner_scope": "planner_plus_sandbox",
            "status": status,
            "tests_requested": max_tests,
            "tests_required": len(selected_tests),
            "tests_selected": len(selected_tests),
            "selected_tests": selected_tests,
            "decisions": decisions,
            "findings": [
                finding.model_dump()
                for finding in findings
            ],
            "execution_records": execution_records,
            "errors": errors,
            "selection_accuracy": self._selection_accuracy(
                selected_tests,
                expected_test_sequence,
            ),
            "execution_success_rate": round(
                execution_success_rate,
                4,
            ),
            "llm_calls": state.budget_used.llm_calls,
            "fallback_used": fallback_used,
            "planner_time_seconds": round(
                planner_time_seconds,
                6,
            ),
            "execution_time_seconds": round(
                execution_time_seconds,
                6,
            ),
            "total_time_seconds": round(
                total_time_seconds,
                6,
            ),
            "budget_used": state.budget_used.model_dump(),
            "remaining_budget": self.planner.remaining_budget(
                state
            ),
            "chain_metrics": chain_metrics,
            "mitigation_metrics": {
                "mitigation_controls_observed": sorted(
                    {
                        record["mitigation_control"]
                        for record in execution_records
                        if record.get("mitigation_control")
                    }
                ),
                "mitigation_applied_count": sum(
                    1
                    for record in execution_records
                    if record.get("mitigation_applied") is True
                ),
            },
        }

    # ------------------------------------------------------------------
    # Full A-D suite
    # ------------------------------------------------------------------

    def run_suite(
        self,
        planner_input: PlannerInput,
        experiment_ids: dict[str, str],
        max_tests: int | None = None,
        expected_test_sequence: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Execute A, B, C and D from the same initial PlannerInput.

        `experiment_ids` must be supplied by the caller. In production,
        these should be P2-issued IDs. The runner never creates them.
        """

        if not isinstance(experiment_ids, dict):
            raise TypeError(
                "experiment_ids must be a dictionary keyed by A, B, C, D."
            )

        missing = [
            config_id
            for config_id in self.CONFIGURATION_ORDER
            if config_id not in experiment_ids
        ]

        if missing:
            raise ValueError(
                "Missing experiment IDs for configurations: "
                f"{missing}"
            )

        results: list[dict[str, Any]] = []

        for config_id in self.CONFIGURATION_ORDER:
            results.append(
                self.run_configuration(
                    planner_input=planner_input,
                    configuration=config_id,
                    experiment_id=experiment_ids[config_id],
                    max_tests=max_tests,
                    expected_test_sequence=expected_test_sequence,
                )
            )

        return {
            "study": "phase3_ablation",
            "runner_scope": "planner_plus_sandbox",
            "same_initial_state": True,
            "configuration_order": list(
                self.CONFIGURATION_ORDER
            ),
            "experiment_ids": {
                key: str(experiment_ids[key])
                for key in self.CONFIGURATION_ORDER
            },
            "results": results,
        }


def save_ablation_result(
    result: dict[str, Any],
    output_path: str | Path,
) -> Path:
    """
    Save a local JSON research artifact.

    This is not P2 database persistence. It is a reproducible local
    experiment artifact that can later be ingested by the P2 layer.
    """

    path = Path(output_path)
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        json.dumps(
            result,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    return path
