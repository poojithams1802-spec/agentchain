import sys
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1]),
)

from planner import AdaptivePlanner
from schemas import PlannerInput

def test_planner_populates_retrieved_knowledge(monkeypatch):
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
            "experiment_id": "rag-test-001",
            "step": 1,
        },
    )

    expected_knowledge = [
        "Authorization controls should enforce least privilege.",
        "Sensitive tools require permission checks.",
    ]

    def fake_retrieve_knowledge(_):
        return expected_knowledge

    def fake_generate_json(prompt):
        return {
            "selected_test": "permission_test",
            "reason": "Permission testing is relevant to the retrieved knowledge.",
            "priority": 0.9,
            "confidence": 0.9,
        }

    monkeypatch.setattr(
        planner,
        "retrieve_knowledge",
        fake_retrieve_knowledge,
    )

    monkeypatch.setattr(
        planner.llm_client,
        "generate_json",
        fake_generate_json,
    )

    planner.plan(planner_input)

    assert planner_input.retrieved_knowledge == expected_knowledge
    assert len(planner_input.retrieved_knowledge) == 2