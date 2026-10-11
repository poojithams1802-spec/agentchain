
import json
import sys
from pathlib import Path
from time import perf_counter

AI_ENGINE_ROOT = Path(__file__).resolve().parent.parent
PROJECT_ROOT = AI_ENGINE_ROOT.parent

for path in (AI_ENGINE_ROOT, PROJECT_ROOT):
    path_string = str(path)
    if path_string not in sys.path:
        sys.path.insert(0, path_string)

from planner import AdaptivePlanner
from adaptive_loop import AdaptiveLoop
from schemas import PlannerInput


def build_experiment_result(
    experiment_id,
    planner,
    planner_input,
    findings,
    execution_results=None,
    timing=None,
    loop_result=None,
):
    """Build a JSON-serializable experiment result."""

    execution_results = execution_results or []
    timing = timing or {}
    loop_result = loop_result or {}

    return {
        "experiment_id": experiment_id,
        "test_sequence": [
            result.get("test", result.get("test_name"))
            for result in execution_results
        ],
        "finding_sequence": [
            finding.model_dump()
            if hasattr(finding, "model_dump")
            else finding
            for finding in findings
        ],
        "planner_trace": loop_result.get("decisions", []),
        "execution_results": execution_results,
        "tests_executed": len(execution_results),
        "findings_count": len(findings),
        "timing": timing,
        "budget_used": loop_result.get(
            "budget_used",
            planner_input.budget_used.model_dump(),
        ),
        "fallback_used": loop_result.get("fallback_used", False),
        "llm_calls_used": loop_result.get("llm_calls_used", 0),
    }


def main():
    experiment_id = "DAY14_FINAL"

    print("=" * 70)
    print("AGENTCHAIN ADAPTIVE SECURITY EXPERIMENT")
    print("=" * 70)
    print(f"Experiment ID : {experiment_id}")

    planner = AdaptivePlanner()

    planner_input = PlannerInput(
        available_tests=[
            "permission_test",
            "tool_access_test",
            "memory_access_test",
        ],
        previous_tests=[],
        findings=[],
    )

    loop = AdaptiveLoop(planner=planner)

    experiment_start = perf_counter()

    loop_result = loop.run_detailed(
        planner_input=planner_input,
        experiment_id=experiment_id,
        max_tests=3,
    )

    experiment_runtime = perf_counter() - experiment_start

    findings = loop_result.get("findings", [])
    execution_results = loop_result.get("execution_results", [])
    timing = loop_result.get("timing", {}).copy()

    timing["experiment_loop_runtime_seconds"] = experiment_runtime

    timing["timing_scope"] = {
        "total_runtime_seconds": (
            "Time measured inside AdaptiveLoop.run_detailed."
        ),
        "total_planning_time_seconds": (
            "Sum of complete planner.plan calls, including retrieval "
            "and LLM request time."
        ),
        "total_sandbox_adapter_time_seconds": (
            "Sum of execute_planned_test adapter call durations."
        ),
        "experiment_loop_runtime_seconds": (
            "Wall-clock time around the complete run_detailed call."
        ),
    }

    result = build_experiment_result(
        experiment_id=experiment_id,
        planner=planner,
        planner_input=planner_input,
        findings=findings,
        execution_results=execution_results,
        timing=timing,
        loop_result=loop_result,
    )

    results_dir = AI_ENGINE_ROOT / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    output_path = results_dir / f"{experiment_id}_backup.json"

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(result, file, indent=2, default=str)

    print()
    print("=" * 70)
    print("FINAL ADAPTIVE EXPERIMENT SUMMARY")
    print("=" * 70)
    print(f"Tests executed : {len(execution_results)}")
    print(f"Findings       : {len(findings)}")
    print(f"Fallback used  : {result['fallback_used']}")
    print(f"LLM calls used : {result['llm_calls_used']}")

    print("\nTest sequence:")
    for index, test_name in enumerate(result["test_sequence"], start=1):
        print(f"  {index}. {test_name}")

    print("\nTiming:")
    print(
        "Adaptive loop runtime       : "
        f"{timing.get('total_runtime_seconds', 0):.6f} seconds"
    )
    print(
        "Planning time total         : "
        f"{timing.get('total_planning_time_seconds', 0):.6f} seconds"
    )
    print(
        "Sandbox adapter time total  : "
        f"{timing.get('total_sandbox_adapter_time_seconds', 0):.6f} seconds"
    )
    print(
        "Experiment loop wall time   : "
        f"{timing.get('experiment_loop_runtime_seconds', 0):.6f} seconds"
    )

    planning_latencies = timing.get("planning_latency_seconds", [])
    if planning_latencies:
        print("\nPer-decision planning latency:")
        for index, latency in enumerate(planning_latencies, start=1):
            print(f"  Step {index}: {latency:.6f} seconds")

    measured_test_count = 0
    measured_execution_time = 0.0

    for execution in execution_results:
        cost = execution.get("execution_cost", {})
        if isinstance(cost, dict):
            measured_test_count += cost.get("test_count", 0)
            measured_execution_time += cost.get(
                "execution_time_seconds", 0.0
            )

    print("\nP4 execution-cost measurements:")
    print(f"Measured test count      : {measured_test_count}")
    print(
        "Measured execution time  : "
        f"{measured_execution_time:.6f} seconds"
    )

    print(f"\n[Result] Saved experiment result to: {output_path}")
    print("=" * 70)


if __name__ == "__main__":
    main()