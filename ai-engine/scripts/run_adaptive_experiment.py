import sys
from pathlib import Path

AI_ENGINE_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = Path(__file__).resolve().parents[2]

for path in (AI_ENGINE_ROOT, PROJECT_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))
from planner import AdaptivePlanner
from adaptive_loop import AdaptiveLoop
from schemas import PlannerInput


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


def run_experiment() -> None:
    experiment_id = "DAY12_DEMO"

    planner = AdaptivePlanner()

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

    loop = AdaptiveLoop(
        planner=planner
    )

    print_experiment_header(experiment_id)

    findings = loop.run(
        planner_input=planner_input,
        experiment_id=experiment_id,
        max_tests=3,
    )

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

    print()
    print("=" * 70)
    print("EXPERIMENT SUMMARY")
    print("=" * 70)

    print(f"Tests executed : {len(planner_input.previous_tests)}")
    print(f"Findings       : {len(findings)}")

    print()
    print("Test sequence:")

    for index, test_name in enumerate(
        planner_input.previous_tests,
        start=1,
    ):
        print(f"  {index}. {test_name}")

    print()
    print("Finding sequence:")

    for index, finding in enumerate(
        findings,
        start=1,
    ):
        print(
            f"  {index}. "
            f"{finding.finding} "
            f"({finding.severity}, "
            f"confidence={finding.confidence:.2f})"
        )

    print()
    print("=" * 70)


if __name__ == "__main__":
    run_experiment()