from planner import AdaptivePlanner
from schemas import Finding, PlannerInput


def test_fallback_decision_uses_highest_ranked_candidate():
    planner = AdaptivePlanner()

    planner_input = PlannerInput(
        findings=[
            Finding(
                finding="weak_permission_control",
                severity="high",
                confidence=1.0,
                evidence="Unauthorized permission access.",
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
    )

    decision = planner.fallback_decision(
        planner_input,
        reason="LLM unavailable.",
    )

    assert decision.selected_test == "tool_access_test"
    assert decision.priority > 0.0
    assert decision.confidence == 0.1
    assert "highest-ranked" in decision.reason