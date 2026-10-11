
import sys
import json
from pathlib import Path


# ============================================================
# PATH SETUP
# ============================================================

AI_ENGINE_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = Path(__file__).resolve().parents[2]

for path in (AI_ENGINE_ROOT, PROJECT_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))


# ============================================================
# IMPORTS
# ============================================================

from planner import AdaptivePlanner
from adaptive_loop import AdaptiveLoop
from schemas import PlannerInput


# ============================================================
# DISPLAY HELPERS
# ============================================================

def print_experiment_header(experiment_id: str) -> None:
    print("=" * 70)
    print("AGENTCHAIN ADAPTIVE SECURITY EXPERIMENT")
    print("=" * 70)
    print(f"Experiment ID : {experiment_id}")
    print("=" * 70)


def print_finding(step: int, test_name: str, finding) -> None:
    print()
    print(f"STEP {step}")
    print("-" * 50)
    print(f"Test       : {test_name}")
    print(f"Finding    : {finding.finding}")
    print(f"Severity   : {finding.severity}")
    print(f"Confidence : {finding.confidence:.2f}")
    print(f"Evidence   : {finding.evidence}")


# ============================================================
# PLANNER TRACE WRAPPER
# ============================================================

class TracingPlanner:
    def __init__(self, planner):
        self.planner = planner
        self.traces = []

    def plan(self, planner_input):
        decision = self.planner.plan(planner_input)

        ranked_candidates = self.planner.rank_candidates(
            planner_input
        )

        trace = {
            "step": len(self.traces) + 1,
            "selected_test": decision.selected_test,
            "reason": decision.reason,
            "priority": decision.priority,
            "confidence": decision.confidence,
            "retrieved_knowledge": list(
                planner_input.retrieved_knowledge
            ),
            "candidate_scores": [
                {
                    "test": candidate.test_name,
                    "score": score,
                }
                for candidate, score in ranked_candidates
            ],
        }

        self.traces.append(trace)
        return decision


# ============================================================
# BUILD STRUCTURED EXPERIMENT RESULT
# ============================================================

def build_experiment_result(
    experiment_id: str,
    planner,
    planner_input,
    findings,
    execution_results=None,
) -> dict:
    return {
        "experiment_id": experiment_id,
        "test_sequence": list(planner_input.previous_tests),
        "finding_sequence": [
            {
                "finding": finding.finding,
                "severity": finding.severity,
                "confidence": finding.confidence,
                "evidence": finding.evidence,
            }
            for finding in findings
        ],
        "planner_trace": list(planner.traces),
        "execution_results": execution_results or [],
        "tests_executed": len(planner_input.previous_tests),
        "findings_count": len(findings),
    }


# ============================================================
# SAVE RESULT AS JSON
# ============================================================

def save_experiment_result(
    result: dict,
    output_path: str,
) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as file:
        json.dump(result, file, indent=2)

    print()
    print(f"[Result] Saved experiment result to: {path}")


# ============================================================
# PRINT PLANNER TRACE
# ============================================================

def print_planner_trace(planner) -> None:
    print()
    print("=" * 70)
    print("PLANNER REASONING TRACE")
    print("=" * 70)

    for trace in planner.traces:
        print()
        print(f"STEP {trace['step']}")
        print("-" * 50)
        print(f"Selected test : {trace['selected_test']}")
        print(f"Reason        : {trace['reason']}")
        print(f"Priority      : {trace['priority']:.4f}")
        print(f"Confidence    : {trace['confidence']:.4f}")

        print()
        print("Retrieved knowledge:")

        if trace["retrieved_knowledge"]:
            for knowledge in trace["retrieved_knowledge"]:
                print(f"  - {knowledge}")
        else:
            print("  - None")

        print()
        print("Candidate scores:")

        if trace["candidate_scores"]:
            for candidate in trace["candidate_scores"]:
                print(
                    f"  {candidate['test']:<25} "
                    f"{candidate['score']:.4f}"
                )
        else:
            print("  - None")


# ============================================================
# PRINT FINAL SUMMARY
# ============================================================

def print_final_summary(result: dict) -> None:
    print()
    print("=" * 70)
    print("FINAL ADAPTIVE EXPERIMENT SUMMARY")
    print("=" * 70)

    print(f"Experiment ID  : {result['experiment_id']}")
    print(f"Tests executed : {result['tests_executed']}")
    print(f"Findings       : {result['findings_count']}")

    print()
    print("Test sequence:")

    for index, test in enumerate(result["test_sequence"], start=1):
        print(f"  {index}. {test}")

    print()
    print("Finding sequence:")

    for index, finding in enumerate(
        result["finding_sequence"], start=1
    ):
        print(
            f"  {index}. {finding['finding']} "
            f"({finding['severity']}, "
            f"confidence={finding['confidence']:.2f})"
        )

    execution_results = result.get("execution_results", [])
    print()
    print(f"Execution result records: {len(execution_results)}")

    if execution_results:
        measured_tests = 0
        measured_seconds = 0.0

        for item in execution_results:
            cost = item.get("execution_cost", {})
            if isinstance(cost, dict):
                measured_tests += cost.get("test_count", 0)
                measured_seconds += cost.get(
                    "execution_time_seconds", 0.0
                )

        print(f"Measured test count      : {measured_tests}")
        print(f"Measured execution time  : {measured_seconds:.6f} seconds")
    else:
        print(
            "WARNING: No execution result records were returned "
            "by the adaptive loop."
        )

    print("=" * 70)


# ============================================================
# MAIN EXPERIMENT
# ============================================================

def run_experiment(
    experiment_id: str = "DAY14_FINAL",
) -> dict:
    # Create base planner
    base_planner = AdaptivePlanner()

    # Wrap planner with tracing
    planner = TracingPlanner(base_planner)

    # Initial planner state
    planner_input = PlannerInput(
        findings=[],
        previous_tests=[],
        available_tests=[
            "permission_test",
            "tool_access_test",
            "memory_access_test",
        ],
        retrieved_knowledge=[],
        chain_state={
            "experiment_id": experiment_id,
            "step": 1,
        },
    )

    # Create adaptive loop
    loop = AdaptiveLoop(planner=planner)

    print_experiment_header(experiment_id)

    # Run adaptive experiment
    detailed_result = loop.run_detailed(
        planner_input=planner_input,
        experiment_id=experiment_id,
        max_tests=3,
    )

    findings = detailed_result["findings"]
    execution_results = detailed_result["execution_results"]

    # Print individual findings
    print()
    print("=" * 70)
    print("EXPERIMENT FINDINGS")
    print("=" * 70)

    for index, finding in enumerate(findings, start=1):
        if index <= len(planner_input.previous_tests):
            test_name = planner_input.previous_tests[index - 1]
        else:
            test_name = "unknown"

        print_finding(
            step=index,
            test_name=test_name,
            finding=finding,
        )

    # Print planner reasoning
    print_planner_trace(planner)

    # Build structured result, including execution costs
    result = build_experiment_result(
        experiment_id=experiment_id,
        planner=planner,
        planner_input=planner_input,
        findings=findings,
        execution_results=execution_results,
    )

    # Save JSON result
    save_experiment_result(
        result,
        f"results/{experiment_id}_backup.json",
    )

    # Print final summary
    print_final_summary(result)

    return result


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    run_experiment("DAY14_FINAL")
