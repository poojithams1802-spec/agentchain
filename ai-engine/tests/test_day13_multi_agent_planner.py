from planner import AdaptivePlanner
from schemas import (
    MultiAgentContext,
    PlannerInput,
)


def build_multi_agent_input():
    return PlannerInput(
        available_tests=[
            "permission_test",
            "tool_access_test",
            "memory_access_test",
        ],
        multi_agent_context=MultiAgentContext(
            enabled=True,
            agents={
                "agent_a": {
                    "role": "research",
                    "tools": ["knowledge_search"],
                    "permissions": ["read"],
                },
                "agent_b": {
                    "role": "planning",
                    "tools": ["planner"],
                    "permissions": ["read"],
                },
                "agent_c": {
                    "role": "execution",
                    "tools": ["sandbox"],
                    "permissions": ["execute"],
                },
            },
            allowed_interactions=[
                {
                    "source": "agent_a",
                    "target": "agent_b",
                    "interaction": "research_handoff",
                },
                {
                    "source": "agent_b",
                    "target": "agent_c",
                    "interaction": "execution_request",
                },
            ],
            trust_context={
                "untrusted_agents": [],
                "cross_agent_trust": False,
            },
            shared_memory_context={
                "shared_memory_enabled": True,
                "cross_agent_memory": True,
            },
        ),
    )


def test_multi_agent_context_is_extracted():
    planner = AdaptivePlanner()

    planner_input = build_multi_agent_input()

    context = planner.get_multi_agent_context(
        planner_input
    )

    assert context["enabled"] is True
    assert set(context["agents"]) == {
        "agent_a",
        "agent_b",
        "agent_c",
    }

    assert len(
        context["allowed_interactions"]
    ) == 2


def test_multi_agent_reasoning_context_tracks_roles_and_interactions():
    planner = AdaptivePlanner()

    planner_input = build_multi_agent_input()

    context = planner.build_multi_agent_reasoning_context(
        planner_input
    )

    assert context["enabled"] is True

    assert context["active_agents"] == [
        "agent_a",
        "agent_b",
        "agent_c",
    ]

    assert context["interaction_count"] == 2

    assert context["agents"]["agent_a"]["role"] == (
        "research"
    )

    assert context["agents"]["agent_b"]["role"] == (
        "planning"
    )

    assert context["agents"]["agent_c"]["role"] == (
        "execution"
    )


def test_multi_agent_reasoning_detects_memory_risk():
    planner = AdaptivePlanner()

    planner_input = build_multi_agent_input()

    context = planner.build_multi_agent_reasoning_context(
        planner_input
    )

    assert "shared_memory_access" in (
        context["memory_risks"]
    )

    assert "cross_agent_memory_sharing" in (
        context["memory_risks"]
    )


def test_disabled_multi_agent_context_is_safe():
    planner = AdaptivePlanner()

    planner_input = PlannerInput(
        available_tests=["permission_test"]
    )

    context = planner.build_multi_agent_reasoning_context(
        planner_input
    )

    assert context["enabled"] is False
    assert context["active_agents"] == []
    assert context["interaction_count"] == 0
    assert context["trust_risks"] == []
    assert context["memory_risks"] == []