"""
Phase 3 attack-chain package.

This package defines, registers, and executes controlled
multi-step attack-chain scenarios.
"""

from .chain_registry import (
    get_all_chains,
    get_chain,
    register_chain,
    validate_chain_definition,
)

from .chain_executor import execute_chain


__all__ = [
    "get_all_chains",
    "get_chain",
    "register_chain",
    "validate_chain_definition",
    "execute_chain",
]