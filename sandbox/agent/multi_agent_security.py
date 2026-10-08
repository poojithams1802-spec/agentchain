"""
Phase 3 Day 14 - Controlled Multi-Agent Security Scenario.

P4 responsibility:
- compose existing V11 + V10 weaknesses
- execute the scenario through the local AgentRegistry
- produce deterministic evidence
- validate the resulting multi-agent attack chain

This is a synthetic, local-only research scenario.
"""

from __future__ import annotations

from typing import Any

from .multi_agent import AgentRegistry
from sandbox.vulnerabilities.v10_unsafe_delegation import (
    run_v10_scenario,
)
from sandbox.vulnerabilities.v11_cross_agent_trust import (
    run_v11_scenario,
)


CHAIN_ID = "MULTI-AGENT-CHAIN-V11-V10"


def build_multi_agent_security_scenario() -> AgentRegistry:
    """
    Build the intentionally vulnerable two-agent scenario.

    The untrusted agent is incorrectly permitted to communicate with
    the controlled higher-trust agent. This models the controlled
    precondition needed for V11 -> V10 composition.
    """
    registry = AgentRegistry()

    registry.register_agent(
        "AGENT_UNTRUSTED",
        "Research",
        permissions={"read"},
        tools={"search"},
        trust_level=0.2,
        allowed_interactions={"AGENT_CONTROLLED"},
    )

    registry.register_agent(
        "AGENT_CONTROLLED",
        "Planning",
        permissions={"plan", "delegate"},
        tools={"planner"},
        trust_level=0.9,
        allowed_interactions=set(),
    )

    return registry


def execute_multi_agent_security_scenario() -> dict[str, Any]:
    """
    Execute the controlled V11 -> V10 scenario.

    No external systems, networking, or real-world actions are used.
    """
    registry = build_multi_agent_security_scenario()

    trust_message = registry.send_message(
        "AGENT_UNTRUSTED",
        "AGENT_CONTROLLED",
        "Controlled delegation request.",
    )

    v11 = run_v11_scenario()
    v10 = run_v10_scenario()

    chain_steps = [
        {
            "step": 1,
            "vulnerability_id": "V11",
            "test": v11["test"],
            "finding": v11["name"],
            "status": (
                "triggered"
                if v11["vulnerable"]
                else "not_triggered"
            ),
        },
        {
            "step": 2,
            "vulnerability_id": "V10",
            "test": v10["test"],
            "finding": v10["name"],
            "status": (
                "triggered"
                if v10["vulnerable"]
                else "not_triggered"
            ),
        },
    ]

    chain_triggered = (
        v11["vulnerable"]
        and v10["vulnerable"]
        and trust_message["status"] == "delivered"
    )

    return {
        "status": "completed",
        "chain_id": CHAIN_ID,
        "agents": registry.list_agents(),
        "communication": trust_message,
        "vulnerabilities": {
            "V11": v11,
            "V10": v10,
        },
        "chain_steps": chain_steps,
        "chain_triggered": chain_triggered,
        "expected_chain": [
            "V11",
            "V10",
        ],
        "validation_rule": (
            "The chain is vulnerable when an untrusted agent is "
            "accepted across the trust boundary and can subsequently "
            "reach the controlled delegation path."
        ),
    }


def validate_multi_agent_security_scenario(
    result: dict[str, Any],
) -> dict[str, Any]:
    """
    Validate that the controlled V11 -> V10 chain was actually
    represented and triggered.
    """
    errors: list[str] = []

    if result.get("chain_id") != CHAIN_ID:
        errors.append("Unexpected chain_id.")

    if result.get("chain_triggered") is not True:
        errors.append(
            "Expected the controlled multi-agent chain to trigger."
        )

    communication = result.get("communication", {})
    if communication.get("status") != "delivered":
        errors.append(
            "Expected the controlled communication to be delivered."
        )

    vulnerabilities = result.get("vulnerabilities", {})

    v11 = vulnerabilities.get("V11", {})
    v10 = vulnerabilities.get("V10", {})

    if v11.get("vulnerable") is not True:
        errors.append("V11 must be vulnerable in the scenario.")

    if v10.get("vulnerable") is not True:
        errors.append("V10 must be vulnerable in the scenario.")

    chain_steps = result.get("chain_steps", [])

    actual_ids = [
        step.get("vulnerability_id")
        for step in chain_steps
    ]

    if actual_ids != ["V11", "V10"]:
        errors.append(
            "Expected chain steps V11 -> V10."
        )

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "chain_id": result.get("chain_id"),
        "chain_length": len(chain_steps),
        "validated_chain": (
            len(errors) == 0
            and actual_ids == ["V11", "V10"]
        ),
    }


def run_and_validate_multi_agent_security_scenario() -> dict[str, Any]:
    """
    Convenience entry point for Day 14 validation.
    """
    result = execute_multi_agent_security_scenario()
    validation = validate_multi_agent_security_scenario(result)

    return {
        **result,
        "validation": validation,
    }