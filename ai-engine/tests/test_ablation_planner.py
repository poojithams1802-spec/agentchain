from ablation import (
    get_ablation_configuration,
    list_ablation_configurations,
)
from planner import AdaptivePlanner
from schemas import Finding, PlannerInput


AVAILABLE_TESTS = [
    "permission_test",
    "tool_access_test",
    "memory_access_test",
]


def make_planner_input():
    return PlannerInput(
        findings=[
            Finding(
                finding="weak authorization boundary",
                severity="high",
                confidence=0.9,
                evidence="controlled permission evidence",
            )
        ],
        previous_tests=[],
        available_tests=list(AVAILABLE_TESTS),
        chain_state={
            "chain_id": "CHAIN_B",
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
                "validation_rate": 0.5,
                "residual_steps": [
                    "tool_access",
                    "memory_access",
                ],
            },
        },
    )


def test_four_ablation_configurations_are_defined():
    configs = list_ablation_configurations()

    assert [config.config_id for config in configs] == [
        "A",
        "B",
        "C",
        "D",
    ]

    assert configs[0].use_rag is False
    assert configs[0].use_chain_context is False

    assert configs[1].use_rag is True
    assert configs[1].use_chain_context is False

    assert configs[2].use_rag is False
    assert configs[2].use_chain_context is True

    assert configs[3].use_rag is True
    assert configs[3].use_chain_context is True


def test_invalid_ablation_configuration_is_rejected():
    try:
        get_ablation_configuration("X")
    except ValueError as error:
        assert "A, B, C, or D" in str(error)
    else:
        raise AssertionError("Invalid configuration was accepted.")


def test_prompt_contains_only_selected_context(monkeypatch):
    planner = AdaptivePlanner()
    planner.retrieve_knowledge = lambda planner_input, configuration: (
        ["retrieved authorization knowledge"]
        if configuration.use_rag
        else []
    )

    prompts = {}

    for config_id in ["A", "B", "C", "D"]:
        planner_input = make_planner_input()

        # Populate retrieved knowledge only through the planner's
        # configuration-aware retrieval path.
        planner.retrieve_knowledge(
            planner_input,
            get_ablation_configuration(config_id),
        )

        if config_id in {"B", "D"}:
            planner_input.retrieved_knowledge = [
                "retrieved authorization knowledge"
            ]

        prompts[config_id] = planner.create_prompt(
            planner_input,
            configuration=config_id,
        )

    assert "SECURITY KNOWLEDGE / RAG" not in prompts["A"]
    assert "ATTACK-CHAIN REASONING" not in prompts["A"]

    assert "SECURITY KNOWLEDGE / RAG" in prompts["B"]
    assert "ATTACK-CHAIN REASONING" not in prompts["B"]

    assert "SECURITY KNOWLEDGE / RAG" not in prompts["C"]
    assert "ATTACK-CHAIN REASONING" in prompts["C"]

    assert "SECURITY KNOWLEDGE / RAG" in prompts["D"]
    assert "ATTACK-CHAIN REASONING" in prompts["D"]
    assert "Candidate scores" in prompts["D"]


def test_plan_respects_rag_ablation(monkeypatch):
    planner = AdaptivePlanner()

    retrieval_calls = []

    def fake_retrieve(planner_input, configuration="D"):
        retrieval_calls.append(configuration.config_id)
        return (
            ["RAG evidence"]
            if configuration.use_rag
            else []
        )

    monkeypatch.setattr(
        planner,
        "retrieve_knowledge",
        fake_retrieve,
    )

    def fake_generate_json(prompt):
        return {
            "selected_test": "permission_test",
            "reason": "Use the first permitted test.",
            "priority": 0.8,
            "confidence": 0.9,
        }

    monkeypatch.setattr(
        planner.llm_client,
        "generate_json",
        fake_generate_json,
    )

    input_a = make_planner_input()
    decision_a = planner.plan(
        input_a,
        configuration="A",
    )

    input_b = make_planner_input()
    decision_b = planner.plan(
        input_b,
        configuration="B",
    )

    assert decision_a.selected_test == "permission_test"
    assert decision_b.selected_test == "permission_test"

    assert retrieval_calls == ["A", "B"]
    assert input_a.retrieved_knowledge == []
    assert input_b.retrieved_knowledge == ["RAG evidence"]


def test_plan_respects_chain_ablation(monkeypatch):
    planner = AdaptivePlanner()

    captured_prompts = {}

    monkeypatch.setattr(
        planner,
        "retrieve_knowledge",
        lambda planner_input, configuration="D": [],
    )

    def fake_generate_json(prompt):
        captured_prompts["prompt"] = prompt
        return {
            "selected_test": "permission_test",
            "reason": "Controlled baseline decision.",
            "priority": 0.7,
            "confidence": 0.8,
        }

    monkeypatch.setattr(
        planner.llm_client,
        "generate_json",
        fake_generate_json,
    )

    input_a = make_planner_input()
    planner.plan(
        input_a,
        configuration="A",
    )
    prompt_a = captured_prompts["prompt"]

    input_c = make_planner_input()
    planner.plan(
        input_c,
        configuration="C",
    )
    prompt_c = captured_prompts["prompt"]

    assert "CHAIN_B" not in prompt_a
    assert "CHAIN_B" in prompt_c
    assert "ATTACK-CHAIN REASONING" not in prompt_a
    assert "ATTACK-CHAIN REASONING" in prompt_c


def test_ablation_suite_runs_all_four_modes(monkeypatch):
    planner = AdaptivePlanner()

    monkeypatch.setattr(
        planner,
        "retrieve_knowledge",
        lambda planner_input, configuration="D": (
            ["controlled RAG evidence"]
            if configuration.use_rag
            else []
        ),
    )

    def fake_generate_json(prompt):
        return {
            "selected_test": "permission_test",
            "reason": "Deterministic test response.",
            "priority": 0.8,
            "confidence": 0.9,
        }

    monkeypatch.setattr(
        planner.llm_client,
        "generate_json",
        fake_generate_json,
    )

    planner_input = make_planner_input()

    result = planner.run_ablation_suite(
        planner_input,
        max_steps=1,
    )

    assert result["study"] == "phase3_ablation"
    assert result["runner_scope"] == "planner_only"
    assert result["same_initial_state"] is True

    configurations = result["configurations"]

    assert len(configurations) == 4
    assert [
        item["configuration"]["config_id"]
        for item in configurations
    ] == ["A", "B", "C", "D"]

    assert all(
        item["tests_selected"] == 1
        for item in configurations
    )

    # Each configuration receives an independent copy.
    assert planner_input.previous_tests == []
    assert planner_input.budget_used.tests == 0
    assert planner_input.budget_used.llm_calls == 0
