from planner import AdaptivePlanner
from schemas import PlannerInput


def test_chain_context_is_extracted():
    planner = AdaptivePlanner()

    planner_input = PlannerInput(
        available_tests=[
            "permission_test",
            "tool_access_test",
            "memory_access_test",
        ],
        chain_state={
            "chain_id": "CHAIN-001",
            "ordered_steps": [
                "authorization",
                "tool_access",
                "memory_access",
            ],
            "dependencies": {
                "tool_access": ["authorization"],
                "memory_access": ["tool_access"],
            },
            "validation_result": {
                "validation_rate": 1.0,
                "all_findings_reproduced": True,
            },
        },
    )

    context = planner.get_chain_context(
        planner_input
    )

    assert context["chain_id"] == "CHAIN-001"

    assert context["ordered_steps"] == [
        "authorization",
        "tool_access",
        "memory_access",
    ]

    assert context["dependencies"]["tool_access"] == [
        "authorization"
    ]

    assert context["validation_result"]["validation_rate"] == 1.0


def test_residual_chain_context_is_extracted():
    planner = AdaptivePlanner()

    planner_input = PlannerInput(
        available_tests=[
            "permission_test",
            "tool_access_test",
        ],
        previous_tests=[
            "permission_test",
        ],
        chain_state={
            "chain_id": "CHAIN-001",
            "ordered_steps": [
                "authorization",
                "tool_access",
            ],
            "dependencies": {
                "tool_access": ["authorization"],
            },
            "validation_result": {
                "validation_rate": 1.0,
            },
        },
    )

    candidates = planner.build_candidates(
        planner_input
    )

    assert len(candidates) == 1

    candidate = candidates[0]

    assert candidate.test_name == "tool_access_test"
    assert candidate.relevance >= 0.9
    