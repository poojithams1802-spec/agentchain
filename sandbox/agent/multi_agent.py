"""
Phase 3 Day 13 - Multi-Agent Sandbox.

Person 4 responsibility:
- controlled agent registry
- agent identity and roles
- controlled inter-agent communication
- trust and interaction checks

All communication remains local and synthetic.
No network communication is performed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .agent import Agent
from .state import AgentState


@dataclass
class ControlledAgent:
    """
    Metadata wrapper around the existing Agent + AgentState classes.
    """

    agent_id: str
    role: str
    agent: Agent
    state: AgentState
    permissions: set[str] = field(default_factory=set)
    tools: set[str] = field(default_factory=set)
    trust_level: float = 1.0
    allowed_interactions: set[str] = field(default_factory=set)

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "role": self.role,
            "permissions": sorted(self.permissions),
            "tools": sorted(self.tools),
            "trust_level": self.trust_level,
            "allowed_interactions": sorted(
                self.allowed_interactions
            ),
        }


class AgentRegistry:
    """
    Local registry for controlled sandbox agents.
    """

    def __init__(self) -> None:
        self._agents: dict[str, ControlledAgent] = {}

    def register_agent(
        self,
        agent_id: str,
        role: str,
        *,
        permissions: set[str] | None = None,
        tools: set[str] | None = None,
        trust_level: float = 1.0,
        allowed_interactions: set[str] | None = None,
    ) -> ControlledAgent:
        if not agent_id or not agent_id.strip():
            raise ValueError("agent_id must not be empty.")

        if not role or not role.strip():
            raise ValueError("role must not be empty.")

        if agent_id in self._agents:
            raise ValueError(
                f"Agent already registered: {agent_id}"
            )

        if not 0.0 <= trust_level <= 1.0:
            raise ValueError(
                "trust_level must be between 0.0 and 1.0."
            )

        controlled_agent = ControlledAgent(
            agent_id=agent_id,
            role=role,
            agent=Agent(),
            state=AgentState(),
            permissions=set(permissions or set()),
            tools=set(tools or set()),
            trust_level=trust_level,
            allowed_interactions=set(
                allowed_interactions or set()
            ),
        )

        self._agents[agent_id] = controlled_agent

        return controlled_agent

    def get_agent(
        self,
        agent_id: str,
    ) -> ControlledAgent:
        if agent_id not in self._agents:
            raise KeyError(
                f"Unknown agent: {agent_id}"
            )

        return self._agents[agent_id]

    def list_agents(self) -> list[dict[str, Any]]:
        return [
            agent.to_dict()
            for agent in self._agents.values()
        ]

    def can_communicate(
        self,
        sender_id: str,
        receiver_id: str,
    ) -> bool:
        sender = self.get_agent(sender_id)
        self.get_agent(receiver_id)

        return receiver_id in sender.allowed_interactions

    def send_message(
        self,
        sender_id: str,
        receiver_id: str,
        message: str,
    ) -> dict[str, Any]:
        """
        Send a synthetic local message between two registered agents.

        Communication is allowed only when the sender explicitly lists
        the receiver in allowed_interactions.
        """
        if not isinstance(message, str):
            raise TypeError("message must be a string.")

        if not message.strip():
            raise ValueError("message must not be empty.")

        sender = self.get_agent(sender_id)
        receiver = self.get_agent(receiver_id)

        if sender_id == receiver_id:
            return {
                "status": "denied",
                "reason": "Self-communication is not allowed.",
                "sender": sender_id,
                "receiver": receiver_id,
            }

        if receiver_id not in sender.allowed_interactions:
            sender.state.add_history(
                {
                    "action": "communication_denied",
                    "receiver": receiver_id,
                    "reason": "interaction_not_allowed",
                }
            )

            return {
                "status": "denied",
                "reason": "Sender is not allowed to communicate with receiver.",
                "sender": sender_id,
                "receiver": receiver_id,
            }

        communication_record = {
            "action": "message_sent",
            "sender": sender_id,
            "receiver": receiver_id,
            "message": message,
        }

        sender.state.add_history(
            communication_record
        )

        receiver.state.add_history(
            communication_record
        )

        return {
            "status": "delivered",
            "sender": sender_id,
            "receiver": receiver_id,
            "message": message,
        }