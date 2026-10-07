from planner import AdaptivePlanner
from schemas import PlannerInput, MultiAgentContext


def _planner_input(**kwargs):
    return PlannerInput(
        available_tests=["permission_test", "tool_access_test", "memory_access_test"],
        **kwargs,
    )


def test_day14_disabled_defaults_are_safe():
    planner = AdaptivePlanner()
    result = planner.build_trust_delegation_reasoning(_planner_input())

    assert result["enabled"] is False
    assert result["interaction_assessments"] == []
    assert result["trust_risks"] == []
    assert result["delegation_risks"] == []
    assert result["security_signals"] == []


def test_day14_detects_unauthorized_delegation():
    planner = AdaptivePlanner()
    context = MultiAgentContext(
        enabled=True,
        agents={
            "research": {
                "trust_level": "trusted",
                "allowed_interactions": [],
            },
            "execution": {
                "trust_level": "trusted",
            },
        },
        allowed_interactions=[
            {
                "from_agent": "research",
                "to_agent": "execution",
                "action": "unsafe_delegation",
                "allowed": False,
            }
        ],
    )

    result = planner.build_trust_delegation_reasoning(
        _planner_input(multi_agent_context=context)
    )

    assessment = result["interaction_assessments"][0]
    assert assessment["is_delegation"] is True
    assert assessment["allowed"] is False
    assert "unauthorized_delegation" in assessment["risks"]
    assert "unauthorized_delegation" in result["delegation_risks"]


def test_day14_detects_privilege_propagation_to_low_trust_agent():
    planner = AdaptivePlanner()
    context = MultiAgentContext(
        enabled=True,
        agents={
            "planning": {
                "trust_level": "trusted",
            },
            "execution": {
                "trust_level": "low",
            },
        },
        allowed_interactions=[
            {
                "from_agent": "planning",
                "to_agent": "execution",
                "action": "delegation",
                "allowed": True,
                "privileged": True,
            }
        ],
        trust_context={
            "cross_agent_trust": True,
        },
    )

    result = planner.build_trust_delegation_reasoning(
        _planner_input(multi_agent_context=context)
    )

    assessment = result["interaction_assessments"][0]
    assert "delegation_to_low_trust_agent" in assessment["risks"]
    assert "privilege_propagation" in assessment["risks"]
    assert "privilege_propagation" in result["security_signals"]


def test_day14_shared_memory_adds_cross_agent_security_signal():
    planner = AdaptivePlanner()
    context = MultiAgentContext(
        enabled=True,
        agents={
            "research": {"trust_level": "trusted"},
            "planning": {"trust_level": "trusted"},
        },
        shared_memory_context={
            "shared_memory_enabled": True,
            "cross_agent_memory": True,
        },
    )

    result = planner.build_trust_delegation_reasoning(
        _planner_input(multi_agent_context=context)
    )

    assert "cross_agent_context_leakage" in result["security_signals"]
    assert "cross_agent_memory_sharing" in result["security_signals"]
    assert "memory_access_test" in result["recommended_checks"]


def test_day14_reasoning_is_exposed_in_planner_context():
    planner = AdaptivePlanner()
    context = MultiAgentContext(
        enabled=True,
        agents={
            "planning": {"trust_level": "trusted"},
            "execution": {"trust_level": "low"},
        },
        allowed_interactions=[
            {
                "from_agent": "planning",
                "to_agent": "execution",
                "action": "delegation",
                "allowed": True,
            }
        ],
    )

    reasoning = planner.build_reasoning_context(
        _planner_input(multi_agent_context=context)
    )

    assert "trust_delegation_reasoning" in reasoning["multi_agent_context"]
    assert "delegation_to_low_trust_agent" in reasoning["multi_agent_context"]["trust_delegation_reasoning"]["delegation_risks"]
