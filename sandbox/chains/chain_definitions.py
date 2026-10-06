"""
Controlled Phase 3 chain definitions.

These definitions describe how existing sandbox tests can be
composed into multi-step chains.

Important:
- These are controlled local sandbox chains.
- No real-world actions are defined here.
- Actual test execution remains in sandbox.execution.
- Actual validation remains in sandbox.validator.
"""

CHAIN_DEFINITIONS = {
    "CHAIN-AUTH-TOOL": {
        "chain_id": "CHAIN-AUTH-TOOL",
        "name": "Authorization to Tool Access",
        "description": (
            "A two-step controlled chain where a weak authorization "
            "condition precedes unsafe tool access."
        ),
        "steps": [
            "permission_test",
            "tool_access_test",
        ],
        "dependencies": {
            "permission_test": [],
            "tool_access_test": [
                "permission_test",
            ],
        },
    },

    "CHAIN-AUTH-TOOL-MEM": {
        "chain_id": "CHAIN-AUTH-TOOL-MEM",
        "name": "Authorization to Tool Access to Memory",
        "description": (
            "A three-step controlled chain where authorization weakness "
            "precedes tool access and memory-validation weakness."
        ),
        "steps": [
            "permission_test",
            "tool_access_test",
            "memory_access_test",
        ],
        "dependencies": {
            "permission_test": [],
            "tool_access_test": [
                "permission_test",
            ],
            "memory_access_test": [
                "tool_access_test",
            ],
        },
    },
}