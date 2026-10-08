from sandbox.agent.multi_agent import AgentRegistry


def build_registry():
    registry = AgentRegistry()

    registry.register_agent(
        "agent_research",
        "Research",
        permissions={"read"},
        tools={"search"},
        trust_level=0.9,
        allowed_interactions={"agent_planning"},
    )

    registry.register_agent(
        "agent_planning",
        "Planning",
        permissions={"plan"},
        tools={"planner"},
        trust_level=0.8,
        allowed_interactions=set(),
    )

    return registry


def test_registers_two_controlled_agents():
    registry = build_registry()

    agents = registry.list_agents()

    assert len(agents) == 2
    assert agents[0]["agent_id"] == "agent_research"
    assert agents[1]["agent_id"] == "agent_planning"


def test_agent_metadata_is_preserved():
    registry = build_registry()

    agent = registry.get_agent("agent_research")

    assert agent.role == "Research"
    assert agent.trust_level == 0.9
    assert "read" in agent.permissions
    assert "search" in agent.tools


def test_allowed_interaction_is_detected():
    registry = build_registry()

    assert registry.can_communicate(
        "agent_research",
        "agent_planning",
    ) is True


def test_disallowed_interaction_is_detected():
    registry = build_registry()

    assert registry.can_communicate(
        "agent_planning",
        "agent_research",
    ) is False


def test_allowed_message_is_delivered():
    registry = build_registry()

    result = registry.send_message(
        "agent_research",
        "agent_planning",
        "Research task completed.",
    )

    assert result["status"] == "delivered"
    assert result["sender"] == "agent_research"
    assert result["receiver"] == "agent_planning"


def test_message_updates_both_agent_histories():
    registry = build_registry()

    registry.send_message(
        "agent_research",
        "agent_planning",
        "Research task completed.",
    )

    sender = registry.get_agent("agent_research")
    receiver = registry.get_agent("agent_planning")

    assert len(sender.state.history) == 1
    assert len(receiver.state.history) == 1

    assert sender.state.history[0]["action"] == "message_sent"
    assert receiver.state.history[0]["message"] == (
        "Research task completed."
    )


def test_disallowed_message_is_blocked():
    registry = build_registry()

    result = registry.send_message(
        "agent_planning",
        "agent_research",
        "Unauthorized request.",
    )

    assert result["status"] == "denied"
    assert result["reason"] == (
        "Sender is not allowed to communicate with receiver."
    )


def test_self_communication_is_blocked():
    registry = build_registry()

    result = registry.send_message(
        "agent_research",
        "agent_research",
        "Self message.",
    )

    assert result["status"] == "denied"


def test_unknown_agent_is_rejected():
    registry = build_registry()

    try:
        registry.get_agent("unknown")
        assert False, "Expected KeyError"
    except KeyError:
        pass