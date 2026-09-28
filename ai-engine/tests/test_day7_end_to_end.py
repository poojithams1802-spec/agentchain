from planner import AdaptivePlanner
from schemas import Finding, PlannerDecision, PlannerInput
from sandbox_adapter import execute_planned_test
from sandbox.validator.chain_validator import ChainValidator


def test_day7_end_to_end_adaptive_security_flow(monkeypatch):
    experiment_id = "day7-end-to-end"

    available_tests = [
        "permission_test",
        "tool_access_test",
        "memory_access_test",
    ]

    # --------------------------------------------------
    # Step 1: First adaptive planning iteration
    # --------------------------------------------------
    planner = AdaptivePlanner()

    first_prompt = {}

    def fake_first_generate_json(prompt):
        first_prompt["prompt"] = prompt

        return {
            "selected_test": "permission_test",
            "reason": (
                "Start by checking permission and authorization "
                "controls before evaluating dependent tool access."
            ),
            "priority": 0.9,
            "confidence": 0.9,
        }

    monkeypatch.setattr(
        planner.llm_client,
        "generate_json",
        fake_first_generate_json,
    )

    first_planner_input = PlannerInput(
        findings=[],
        previous_tests=[],
        available_tests=available_tests,
    )

    first_decision = planner.plan(first_planner_input)

    assert isinstance(first_decision, PlannerDecision)

    # Selected test must be one of the allowed tests.
    assert first_decision.selected_test in available_tests

    # No previous tests exist, so the first selection must be new.
    assert first_decision.selected_test not in []

    # Verify RAG was actually used.
    assert first_planner_input.retrieved_knowledge

    assert "retrieved_knowledge" in first_prompt["prompt"]

    # --------------------------------------------------
    # Step 2: Execute first test in REAL P4 sandbox
    # --------------------------------------------------
    first_result = execute_planned_test(
        first_decision,
        experiment_id,
    )

    assert first_result["status"] == "completed"

    assert (
        first_result["test"]
        == first_decision.selected_test
    )

    assert first_result["finding"]
    assert first_result["confidence"] == 1.0

    # --------------------------------------------------
    # Step 3: Feed first finding into next planning
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
        previous_tests=[
            first_decision.selected_test
        ],
        available_tests=available_tests,
    )

    # Verify the finding from the sandbox reached the
    # next planner iteration.
    assert len(planner_input.findings) == 1

    assert (
        planner_input.findings[0].finding
        == first_result["finding"]
    )

    assert (
        planner_input.findings[0].confidence
        == first_result["confidence"]
    )

    # --------------------------------------------------
    # Step 4: Mock second LLM response
    #         RAG remains REAL
    # --------------------------------------------------
    captured_second_prompt = {}

    def fake_second_generate_json(prompt):
        captured_second_prompt["prompt"] = prompt

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
        fake_second_generate_json,
    )

    # --------------------------------------------------
    # Step 5: Second RAG + Adaptive Planner iteration
    # --------------------------------------------------
    second_decision = planner.plan(planner_input)

    assert isinstance(
        second_decision,
        PlannerDecision,
    )

    # Selected test must be allowed.
    assert (
        second_decision.selected_test
        in planner_input.available_tests
    )

    # Selected test must not already have been executed.
    assert (
        second_decision.selected_test
        not in planner_input.previous_tests
    )

    # Adaptive planning must select a different test.
    assert (
        second_decision.selected_test
        != first_decision.selected_test
    )

    # RAG should still be active in the second iteration.
    assert planner_input.retrieved_knowledge

    retrieved_text = " ".join(
        planner_input.retrieved_knowledge
    ).lower()

    assert (
        "permission" in retrieved_text
        or "authorization" in retrieved_text
    )

    # Retrieved knowledge must reach the planner prompt.
    assert (
        "retrieved_knowledge"
        in captured_second_prompt["prompt"]
    )

    # The previous finding must also reach the planner prompt.
    assert (
        first_result["finding"]
        in captured_second_prompt["prompt"]
    )

    # --------------------------------------------------
    # Step 6: Execute second test in REAL P4 sandbox
    # --------------------------------------------------
    second_result = execute_planned_test(
        second_decision,
        experiment_id,
    )

    assert second_result["status"] == "completed"

    assert (
        second_result["test"]
        == second_decision.selected_test
    )

    assert second_result["finding"]
    assert second_result["confidence"] == 1.0

    # --------------------------------------------------
    # Step 7: Build candidate chain from actual
    #         planner decisions
    # --------------------------------------------------
    candidate_chain = [
        first_decision.selected_test,
        second_decision.selected_test,
    ]

    assert candidate_chain == [
        "permission_test",
        "tool_access_test",
    ]

    assert len(candidate_chain) == 2
    assert len(set(candidate_chain)) == 2

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