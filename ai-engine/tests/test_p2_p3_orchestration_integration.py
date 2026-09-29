import sys
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1]),
)

from planner import AdaptivePlanner
from schemas import Finding, PlannerDecision, PlannerInput


def test_p2_to_p3_orchestration_integration(monkeypatch):
    """
    Simulates the interface used by P2 orchestration.

    P2 creates PlannerInput
        ↓
    P3 AdaptivePlanner.plan()
        ↓
    P3 returns PlannerDecision
    """

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
            "experiment_id": "integration_test_001",
            "step": 1,
        },
    )

    # Avoid depending on a live Gemini response.
    def fake_generate_json(prompt):
        return {
            "selected_test": "permission_test",
            "reason": "Permission validation is the first available security test.",
            "priority": 0.9,
            "confidence": 0.95,
        }
    monkeypatch.setattr(
        planner.llm_client,
        "generate_json",
        fake_generate_json,
    )

    decision = planner.plan(planner_input)

    # Verify P3 returned the agreed PlannerDecision structure.
    assert isinstance(decision, PlannerDecision)

    assert set(decision.model_fields.keys()) == {
        "selected_test",
        "reason",
        "priority",
        "confidence",
    }

    # Verify P2 can safely consume the selected test.
    assert decision.selected_test in planner_input.available_tests
    assert decision.selected_test not in planner_input.previous_tests

    assert decision.reason
    assert 0.0 <= decision.priority <= 1.0
    assert 0.0 <= decision.confidence <= 1.0


def test_p2_updates_state_and_calls_p3_again(monkeypatch):
    """
    Simulates two iterations of P2 orchestration.

    P2
      ↓
    P3 selects permission_test
      ↓
    P2 records permission_test + finding
      ↓
    P3 receives updated state
      ↓
    P3 selects tool_access_test
    """

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
            "experiment_id": "integration_test_002",
            "step": 1,
        },
    )

    responses = [
        {
            "selected_test": "permission_test",
            "reason": "Start with permission validation.",
            "priority": 0.9,
            "confidence": 0.95,
        },
        {
            "selected_test": "tool_access_test",
            "reason": "Permission testing is complete, so evaluate tool access.",
            "priority": 0.9,
            "confidence": 0.95,
        },
    ]

    call_index = {"value": 0}

    def fake_generate_json(prompt):
        response = responses[call_index["value"]]
        call_index["value"] += 1
        return response


    monkeypatch.setattr(
        planner.llm_client,
        "generate_json",
        fake_generate_json,
    )

    # -------------------------
    # P2 → P3: First iteration
    # -------------------------

    first_decision = planner.plan(planner_input)

    assert first_decision.selected_test == "permission_test"

    # P2 records the executed test.
    planner_input.previous_tests.append(
        first_decision.selected_test
    )

    # P2 receives a finding from P4.
    planner_input.findings.append(
        Finding(
            finding="weak_permission_control",
            severity="high",
            confidence=1.0,
            evidence=(
                "{'permission': 'DENIED', "
                "'observed_behavior': 'TOOL_ALLOWED'}"
            ),
        )
    )

    # P2 updates chain state.
    planner_input.chain_state["step"] = 2

    # -------------------------
    # P2 → P3: Second iteration
    # -------------------------

    second_decision = planner.plan(planner_input)

    assert second_decision.selected_test == "tool_access_test"

    # Verify P2 can continue consuming the decision.
    assert second_decision.selected_test in (
        planner_input.available_tests
    )

    assert second_decision.selected_test not in (
        planner_input.previous_tests
    )