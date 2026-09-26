from planner import AdaptivePlanner
from schemas import Finding, PlannerInput


def test_finding_drives_rag_context_for_next_planning_step(monkeypatch):
    planner = AdaptivePlanner()

    # Do not call the real Gemini API.
    captured_prompt = {}

    def fake_generate_json(prompt):
        captured_prompt["prompt"] = prompt

        return {
            "selected_test": "tool_access_test",
            "reason": "The permission finding indicates that tool authorization should be examined next.",
            "priority": 0.9,
            "confidence": 0.9,
        }

    monkeypatch.setattr(
        planner.llm_client,
        "generate_json",
        fake_generate_json,
    )

    planner_input = PlannerInput(
        findings=[
            Finding(
                finding="weak_permission_control",
                severity="high",
                confidence=1.0,
                evidence="permission DENIED but TOOL_ALLOWED",
            )
        ],
        previous_tests=["permission_test"],
        available_tests=[
            "permission_test",
            "tool_access_test",
            "memory_access_test",
        ],
    )

    decision = planner.plan(planner_input)

    assert decision.selected_test == "tool_access_test"

    # RAG must have populated planner state.
    assert planner_input.retrieved_knowledge

    # The retrieved knowledge should contain permission-related
    # security guidance from the knowledge base.
    retrieved_text = " ".join(
        planner_input.retrieved_knowledge
    ).lower()

    assert (
        "permission" in retrieved_text
        or "authorization" in retrieved_text
    )

    # The generated LLM prompt must contain the retrieved
    # security knowledge.
    assert "retrieved_knowledge" in captured_prompt["prompt"]

    assert (
        "permission" in captured_prompt["prompt"].lower()
        or "authorization" in captured_prompt["prompt"].lower()
    )