from planner import AdaptivePlanner
from schemas import (
    Finding,
    PlannerInput
)


def main() -> None:
    planner = AdaptivePlanner()

    planner_input = PlannerInput(
        findings=[
            Finding(
                finding="unsafe_tool_access",
                severity="high",
                confidence=0.9,
                evidence=(
                    "A restricted tool was accessible "
                    "during the controlled test."
                )
            )
        ],
        previous_tests=[
            "initial_observation_test"
        ],
        available_tests=[
            "tool_access_test",
            "permission_test",
            "memory_validation_test"
        ],
        chain_state={
            "experiment_id": "EXP001",
            "step": 2,
            "testing_budget_remaining": 8
        }
    )

    decision = planner.plan(
        planner_input
    )

    print("Planner decision:")
    print(
        decision.model_dump_json(
            indent=2
        )
    )


if __name__ == "__main__":
    main()