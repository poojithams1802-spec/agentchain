from adaptive_loop import AdaptiveLoop
from schemas import PlannerDecision, PlannerInput


class DeterministicPlanner:
    """
    Deterministic planner for the real P3 -> P4 integration test.

    The sandbox is real.
    Only the planner decision is deterministic so that
    the integration test is reproducible.
    """

    def __init__(self):
        self.calls = []

    def plan(self, planner_input):
        self.calls.append(
            {
                "previous_tests": list(planner_input.previous_tests),
                "findings": list(planner_input.findings),
            }
        )

        if "permission_test" not in planner_input.previous_tests:
            return PlannerDecision(
                selected_test="permission_test",
                reason="Start with permission boundary testing.",
                priority=0.9,
                confidence=0.9,
            )

        return PlannerDecision(
            selected_test="tool_access_test",
            reason="Follow up with tool access testing after the permission finding.",
            priority=0.9,
            confidence=0.9,
        )


def test_real_p3_p4_adaptive_loop():
    planner = DeterministicPlanner()

    planner_input = PlannerInput(
        available_tests=[
            "permission_test",
            "tool_access_test",
        ]
    )

    loop = AdaptiveLoop(planner=planner)

    findings = loop.run(
        planner_input=planner_input,
        experiment_id="day7-real-adaptive-test",
        max_tests=2,
    )

    assert len(findings) == 2

    # First real P4 result.
    assert findings[0].finding == "weak_permission_control"
    assert findings[0].severity == "high"
    assert findings[0].confidence == 1.0

    # Second real P4 result.
    assert findings[1].finding == "unsafe_tool_access"
    assert findings[1].severity == "high"
    assert findings[1].confidence == 1.0

    # Adaptive sequence.
    assert planner_input.previous_tests == [
        "permission_test",
        "tool_access_test",
    ]

    # The second planner call received the first finding.
    assert len(planner.calls) == 2

    assert planner.calls[1]["previous_tests"] == [
        "permission_test"
    ]

    assert len(planner.calls[1]["findings"]) == 1

    assert (
        planner.calls[1]["findings"][0].finding
        == "weak_permission_control"
    )