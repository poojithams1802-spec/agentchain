from planner import AdaptivePlanner
from schemas import Finding, PlannerInput


def print_section(title: str) -> None:
    print()
    print("=" * 60)
    print(title)
    print("=" * 60)


def main() -> None:
    planner = AdaptivePlanner()

    planner_input = PlannerInput(
        findings=[
            Finding(
                finding="weak_permission_control",
                severity="high",
                confidence=1.0,
                evidence=(
                    "The controlled sandbox reproduced "
                    "unauthorized permission access."
                ),
            )
        ],
        previous_tests=[
            "permission_test"
        ],
        available_tests=[
            "permission_test",
            "tool_access_test",
            "memory_access_test",
        ],
        chain_state={
            "experiment_id": "EXP001",
            "step": 2,
            "testing_budget_remaining": 8,
        },
    )

    print_section("AGENTCHAIN ADAPTIVE PLANNER DEMO")

    print("Previous tests:")
    for test in planner_input.previous_tests:
        print(f"  - {test}")

    print()
    print("Current findings:")
    for finding in planner_input.findings:
        print(f"  Finding: {finding.finding}")
        print(f"  Severity: {finding.severity}")
        print(f"  Confidence: {finding.confidence}")
        print(f"  Evidence: {finding.evidence}")

    print()
    print("Available tests:")
    for test in planner_input.available_tests:
        print(f"  - {test}")

    print_section("PLANNING")

    decision = planner.plan(planner_input)

    print("Selected next test:")
    print(f"  {decision.selected_test}")

    print()
    print("Reason:")
    print(f"  {decision.reason}")

    print()
    print(f"Priority:   {decision.priority}")
    print(f"Confidence: {decision.confidence}")

    print()
    print("Retrieved knowledge:")
    for knowledge in planner_input.retrieved_knowledge:
        print(f"  - {knowledge}")

    print_section("ADAPTIVE RESULT")

    print(
        f"Based on the existing finding "
        f"'{planner_input.findings[0].finding}', "
        f"the planner selected:"
    )

    print()
    print(f"  {decision.selected_test}")


if __name__ == "__main__":
    main()
    