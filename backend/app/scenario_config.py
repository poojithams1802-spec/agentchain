"""
Phase 3 scenario configuration helpers.

Scenario configuration is derived from the controlled chain registry.
P2 does not duplicate chain definitions or vulnerability definitions.
"""

from sandbox.chains.chain_registry import get_all_chains, get_chain


def chain_to_scenario(chain: dict) -> dict:
    """Convert one controlled chain definition into an API scenario."""
    return {
        "scenario_id": chain["chain_id"],
        "scenario_name": chain["name"],
        "description": chain["description"],
        "chain_ids": [chain["chain_id"]],
        "steps": chain["steps"],
    }


def get_all_scenarios() -> list[dict]:
    """Return all currently registered controlled scenarios."""
    chains = get_all_chains()
    return [
        chain_to_scenario(chain)
        for chain in chains.values()
    ]


def get_scenario(scenario_id: str) -> dict | None:
    """Return one scenario derived from a registered chain."""
    chain = get_chain(scenario_id)

    if chain is None:
        return None

    return chain_to_scenario(chain)