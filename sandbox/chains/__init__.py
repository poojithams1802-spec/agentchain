"""
Phase 3 attack-chain package.

This package defines, registers, and executes controlled
multi-step attack-chain scenarios.

Imports are intentionally kept lightweight here.  The executor imports
the validator, while the validator imports the registry, so eagerly
importing the executor from this package would create an import cycle
when the validator is imported first.
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
    "execute_chain",
]


def __getattr__(name):
    """
    Lazily expose the chain executor without creating an import cycle.

    This preserves the public package API:
        from sandbox.chains import execute_chain
    """
    if name == "execute_chain":
        from .chain_executor import execute_chain
        return execute_chain

    raise AttributeError(
        f"module {__name__!r} has no attribute {name!r}"
    )