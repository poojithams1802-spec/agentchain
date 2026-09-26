from planner import AdaptivePlanner
from schemas import Finding, PlannerInput
from sandbox_adapter import execute_planned_test
from sandbox.validator.chain_validator import ChainValidator


def test_day7_end_to_end_adaptive_security_flow(monkeypatch):
    experiment_id = "day7-end-to-end"

    # --------------------------------------------------
    # Step 1: First test selected deterministically
    # --------------------------------------------------
    planner = AdaptivePlanner()

    first_decision = planner.plan(
        PlannerInput(
            findings=[],
            previous_tests=[],
            available_tests=[
                "permission_test",
                "tool_access_test",
                "memory_access_test",
            ],
        )
    )

    assert first_decision.selected_test == "permission_test"

    # --------------------------------------------------
    # Step 2: Execute first test in REAL P4 sandbox
    # --------------------------------------------------
    first_result = execute_planned_test(
        first_decision,
        experiment_id,
    )

    assert first_result["status"] == "completed"
    assert first_result["test"] == "permission_test"
    assert first_result["finding"] == "weak_permission_control"
    assert first_result["confidence"] == 1.0

    # --------------------------------------------------
    # Step 3: Feed finding into planner
    # --------------------------------------------------
    planner_input = PlannerInput(
        findings=[
            Finding(
                finding=first_result["finding"],
                severity=first_result["severity"],
                confidence=first_result["confidence"],
                evidence=str(first_result["evidence"]),
            )
        ],
        previous_tests=["permission_test"],
        available_tests=[
            "permission_test",
            "tool_access_test",
            "memory_access_test",
        ],
    )

    # --------------------------------------------------
    # Step 4: Mock only the LLM response
    #         RAG remains REAL
    # --------------------------------------------------
    captured_prompt = {}

    def fake_generate_json(prompt):
        captured_prompt["prompt"] = prompt

        return {
            "selected_test": "tool_access_test",
            "reason": (
                "The permission finding indicates that "
                "tool authorization should be examined next."
            ),
            "priority": 0.9,
            "confidence": 0.9,
        }

    monkeypatch.setattr(
        planner.llm_client,
        "generate_json",
        fake_generate_json,
    )

    # --------------------------------------------------
    # Step 5: RAG + Adaptive Planner
    # --------------------------------------------------
    second_decision = planner.plan(planner_input)

    assert second_decision.selected_test == "tool_access_test"

    # Verify RAG actually retrieved knowledge
    assert planner_input.retrieved_knowledge

    retrieved_text = " ".join(
        planner_input.retrieved_knowledge
    ).lower()

    assert (
        "permission" in retrieved_text
        or "authorization" in retrieved_text
    )

    # Verify retrieved knowledge reached the planner prompt
    assert "retrieved_knowledge" in captured_prompt["prompt"]

    # --------------------------------------------------
    # Step 6: Execute second test in REAL P4 sandbox
    # --------------------------------------------------
    second_result = execute_planned_test(
        second_decision,
        experiment_id,
    )

    assert second_result["status"] == "completed"
    assert second_result["test"] == "tool_access_test"
    assert second_result["finding"] == "unsafe_tool_access"
    assert second_result["confidence"] == 1.0

    # --------------------------------------------------
    # Step 7: Build candidate chain
    # --------------------------------------------------
    candidate_chain = [
        first_result["test"],
        second_result["test"],
    ]

    assert candidate_chain == [
        "permission_test",
        "tool_access_test",
    ]

    # --------------------------------------------------
    # Step 8: Validate candidate chain using P4
    # --------------------------------------------------
    validator = ChainValidator(experiment_id)

    validation_result = validator.validate_chain(
        "DAY7_CHAIN_001",
        candidate_chain,
    )

    assert validation_result["status"] == "validated"
    assert validation_result["validated_steps"] == 2
    assert validation_result["total_steps"] == 2