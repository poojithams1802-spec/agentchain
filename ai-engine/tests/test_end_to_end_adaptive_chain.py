from adaptive_loop import AdaptiveLoop
from planner import AdaptivePlanner
from schemas import PlannerInput


def test_end_to_end_adaptive_chain(monkeypatch):
    """
    Verify the Person 3 adaptive chain:

    permission_test
        ↓
    sandbox finding
        ↓
    RAG retrieval
        ↓
    adaptive planner
        ↓
    tool_access_test
        ↓
    sandbox finding
    """

    planner = AdaptivePlanner()

    planner_input = PlannerInput(
        available_tests=[
            "permission_test",
            "tool_access_test",
            "memory_access_test",
        ]
    )

    executed_tests = []

    def fake_llm_response(prompt):
        if "permission_test" not in executed_tests:
            return {
                "selected_test": "permission_test",
                "reason": "Start with permission boundary testing.",
                "priority": 0.9,
                "confidence": 0.9,
            }

        return {
            "selected_test": "tool_access_test",
            "reason": "Investigate tool access after permission finding.",
            "priority": 0.9,
            "confidence": 0.9,
        }

    def fake_execute(decision, experiment_id):
        executed_tests.append(decision.selected_test)

        if decision.selected_test == "permission_test":
            return {
                "status": "completed",
                "test": "permission_test",
                "finding": "weak_permission_control",
                "severity": "high",
                "evidence": (
                    "Permission boundary allowed unauthorized "
                    "access."
                ),
                "confidence": 1.0,
            }

        if decision.selected_test == "tool_access_test":
            return {
                "status": "completed",
                "test": "tool_access_test",
                "finding": "unsafe_tool_access",
                "severity": "high",
                "evidence": (
                    "Tool access was allowed without sufficient "
                    "authorization."
                ),
                "confidence": 1.0,
            }

        raise AssertionError(
            f"Unexpected test executed: "
            f"{decision.selected_test}"
        )

    monkeypatch.setattr(
        planner.llm_client,
        "generate_json",
        fake_llm_response,
    )

    monkeypatch.setattr(
        "adaptive_loop.execute_planned_test",
        fake_execute,
    )

    loop = AdaptiveLoop(planner=planner)

    findings = loop.run(
        planner_input=planner_input,
        experiment_id="integration-exp-001",
        max_tests=2,
    )

    assert executed_tests == [
        "permission_test",
        "tool_access_test",
    ]

    assert len(findings) == 2

    assert findings[0].finding == "weak_permission_control"
    assert findings[0].confidence == 1.0

    assert findings[1].finding == "unsafe_tool_access"
    assert findings[1].confidence == 1.0

    assert planner_input.previous_tests == [
        "permission_test",
        "tool_access_test",
    ]

    assert len(planner_input.findings) == 2

    assert planner_input.findings[0].finding == (
        "weak_permission_control"
    )

    assert planner_input.findings[1].finding == (
        "unsafe_tool_access"
    )

    assert planner_input.retrieved_knowledge