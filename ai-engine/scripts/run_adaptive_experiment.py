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

def run_experiment(experiment_id: str = "DAY12_DEMO") -> None:

    base_planner = AdaptivePlanner()

    planner = TracingPlanner(
        base_planner
    )

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


    experiment_result = build_experiment_result(
        experiment_id=experiment_id,
        planner=planner,
        planner_input=planner_input,
        findings=findings,
    )
    print()
    print("=" * 70)
    print("STRUCTURED EXPERIMENT RESULT")
    print("=" * 70)

    print(experiment_result)
    print()
    print("=" * 70)
    print("EXPERIMENT FINDINGS")
    print("=" * 70)

    for index, finding in enumerate(
        findings,
        start=1,
    ):
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
    print("PLANNER REASONING TRACE")
    print("=" * 70)

    for trace in planner.traces:
        print()
        print(f"STEP {trace['step']}")
        print("-" * 50)

        print(
            f"Selected test : "
            f"{trace['selected_test']}"
        )

        print(
            f"Reason        : "
            f"{trace['reason']}"
        )

        print(
            f"Priority      : "
            f"{trace['priority']:.4f}"
        )

        print(
            f"Confidence    : "
            f"{trace['confidence']:.4f}"
        )

        print()
        print("Retrieved knowledge:")

        if trace["retrieved_knowledge"]:
            for knowledge in trace["retrieved_knowledge"]:
                print(f"  - {knowledge}")
        else:
            print("  - None")

        print()
        print("Candidate scores:")

        for candidate in trace["candidate_scores"]:
            print(
                f"  {candidate['test']:<25} "
                f"{candidate['score']:.4f}"
            )

    print()
    print("=" * 70)
    print("EXPERIMENT SUMMARY")
    print("=" * 70)

    print(
        f"Tests executed : "
        f"{len(planner_input.previous_tests)}"
    )

    print(
        f"Findings       : "
        f"{len(findings)}"
    )

    print()
    print("Test sequence:")

    for index, test_name in enumerate(
        planner_input.previous_tests,
        start=1,
    ):
        print(
            f"  {index}. {test_name}"
        )

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

def build_experiment_result(
    experiment_id: str,
    planner,
    planner_input,
    findings,
) -> dict:
    return {
        "experiment_id": experiment_id,
        "test_sequence": list(
            planner_input.previous_tests
        ),
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
        "tests_executed": len(
            planner_input.previous_tests
        ),
        "findings_count": len(findings),
    }

if __name__ == "__main__":
    run_experiment()