import sys
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1]),
)

from planner import AdaptivePlanner
from schemas import PlannerDecision, PlannerInput


def test_p2_p3_planner_input_contract():
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
            "experiment_id": "contract-test-001",
            "step": 1,
        },
    )

    assert hasattr(planner_input, "findings")
    assert hasattr(planner_input, "previous_tests")
    assert hasattr(planner_input, "available_tests")
    assert hasattr(planner_input, "retrieved_knowledge")
    assert hasattr(planner_input, "chain_state")

    assert "experiment_id" not in PlannerInput.model_fields

def test_p2_p3_planner_decision_contract(monkeypatch):
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
            "experiment_id": "contract-test-002",
            "step": 1,
        },
    )

    def fake_retrieve_knowledge(_):
        return [
            "Permission and authorization controls "
            "should enforce least privilege."
        ]

    def fake_generate_json(prompt):
        return {
            "selected_test": "permission_test",
            "reason": "Permission testing is the first eligible sandbox test.",
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

    decision = planner.plan(planner_input)

    assert isinstance(decision, PlannerDecision)

    assert decision.selected_test == "permission_test"
    assert decision.reason
    assert 0.0 <= decision.priority <= 1.0
    assert 0.0 <= decision.confidence <= 1.0

    assert set(PlannerDecision.model_fields.keys()) == {
        "selected_test",
        "reason",
        "priority",
        "confidence",
    }