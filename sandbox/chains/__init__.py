"""
Phase 3 attack-chain package.

This package defines and registers controlled multi-step
attack-chain scenarios. Actual sandbox execution and
validation remain owned by the existing execution and
validator modules.
"""

from .chain_registry import (
    get_all_chains,
    get_chain,
    register_chain,
    validate_chain_definition,
)

__all__ = [
    "get_all_chains",
    "get_chain",
    "register_chain",
    "validate_chain_definition",
]