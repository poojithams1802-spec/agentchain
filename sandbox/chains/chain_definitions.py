"""
Controlled Phase 3 chain definitions.

These definitions describe how existing sandbox tests can be
composed into deterministic multi-step controlled chains.

Backward compatibility:
- Existing fields `chain_id`, `name`, `description`,
  `steps`, and `dependencies` remain.
- P3-facing metadata is also exposed:
    chain_name
    ordered_steps
    vulnerability_ids
    entry_condition
    expected_goal
"""

CHAIN_DEFINITIONS = {
    # =========================================================
    # EXISTING CHAIN
    # =========================================================

    "CHAIN-AUTH-TOOL": {
        "chain_id": "CHAIN-AUTH-TOOL",
        "name": "Authorization to Tool Access",
        "chain_name": "Authorization to Tool Access",
        "description": (
            "A two-step controlled chain where a weak authorization "
            "condition precedes unsafe tool access."
        ),
        "steps": [
            "permission_test",
            "tool_access_test",
        ],
        "ordered_steps": [
            "permission_test",
            "tool_access_test",
        ],
        "vulnerability_ids": [
            "V01",
            "V02",
        ],
        "entry_condition": (
            "A controlled authorization boundary is weak."
        ),
        "expected_goal": (
            "Controlled tool access is reached after the "
            "authorization weakness."
        ),
        "dependencies": {
            "permission_test": [],
            "tool_access_test": [
                "permission_test",
            ],
        },
    },

    # =========================================================
    # EXISTING CHAIN
    # =========================================================

    "CHAIN-AUTH-TOOL-MEM": {
        "chain_id": "CHAIN-AUTH-TOOL-MEM",
        "name": "Authorization to Tool Access to Memory",
        "chain_name": "Authorization to Tool Access to Memory",
        "description": (
            "A three-step controlled chain where authorization "
            "weakness precedes tool access and memory-validation "
            "weakness."
        ),
        "steps": [
            "permission_test",
            "tool_access_test",
            "memory_access_test",
        ],
        "ordered_steps": [
            "permission_test",
            "tool_access_test",
            "memory_access_test",
        ],
        "vulnerability_ids": [
            "V01",
            "V02",
            "V03",
        ],
        "entry_condition": (
            "A controlled authorization boundary is weak."
        ),
        "expected_goal": (
            "Controlled memory access is reached after the "
            "authorization and tool-access weaknesses."
        ),
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

    # =========================================================
    # P3 CHAIN A
    # V01 -> V02
    # =========================================================

    "CHAIN_A": {
        "chain_id": "CHAIN_A",
        "name": "Authorization to Tool Access",
        "chain_name": "Authorization to Tool Access",
        "description": (
            "A controlled authorization weakness followed by "
            "controlled unsafe tool access."
        ),
        "steps": [
            "permission_test",
            "tool_access_test",
        ],
        "ordered_steps": [
            "permission_test",
            "tool_access_test",
        ],
        "vulnerability_ids": [
            "V01",
            "V02",
        ],
        "entry_condition": (
            "The controlled permission boundary is weak."
        ),
        "expected_goal": (
            "The controlled tool-access weakness is reached."
        ),
        "dependencies": {
            "permission_test": [],
            "tool_access_test": [
                "permission_test",
            ],
        },
    },

    # =========================================================
    # P3 CHAIN B
    # V01 -> V02 -> V03
    # =========================================================

    "CHAIN_B": {
        "chain_id": "CHAIN_B",
        "name": "Authorization to Tool Access to Memory",
        "chain_name": "Authorization to Tool Access to Memory",
        "description": (
            "A controlled authorization, tool-access, and "
            "memory-validation chain."
        ),
        "steps": [
            "permission_test",
            "tool_access_test",
            "memory_access_test",
        ],
        "ordered_steps": [
            "permission_test",
            "tool_access_test",
            "memory_access_test",
        ],
        "vulnerability_ids": [
            "V01",
            "V02",
            "V03",
        ],
        "entry_condition": (
            "The controlled permission boundary is weak."
        ),
        "expected_goal": (
            "The controlled memory-validation weakness is reached."
        ),
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

    # =========================================================
    # P3 CHAIN C
    # V02 -> V04 -> V06
    # =========================================================

    "CHAIN_C": {
        "chain_id": "CHAIN_C",
        "name": (
            "Tool Access to Prompt Injection to Data Exposure"
        ),
        "chain_name": (
            "Tool Access to Prompt Injection to Data Exposure"
        ),
        "description": (
            "A controlled unsafe tool-access weakness followed "
            "by prompt injection and sensitive data exposure."
        ),
        "steps": [
            "tool_access_test",
            "prompt_injection_test",
            "sensitive_data_test",
        ],
        "ordered_steps": [
            "tool_access_test",
            "prompt_injection_test",
            "sensitive_data_test",
        ],
        "vulnerability_ids": [
            "V02",
            "V04",
            "V06",
        ],
        "entry_condition": (
            "Controlled unsafe tool access is available."
        ),
        "expected_goal": (
            "Controlled sensitive data exposure is reached."
        ),
        "dependencies": {
            "tool_access_test": [],
            "prompt_injection_test": [
                "tool_access_test",
            ],
            "sensitive_data_test": [
                "prompt_injection_test",
            ],
        },
    },

    # =========================================================
    # P3 CHAIN D
    # V01 -> V02 -> V03 -> V10
    # =========================================================

    "CHAIN_D": {
        "chain_id": "CHAIN_D",
        "name": (
            "Authorization to Tool Access to Memory to Delegation"
        ),
        "chain_name": (
            "Authorization to Tool Access to Memory to Delegation"
        ),
        "description": (
            "A controlled authorization, tool-access, "
            "memory-validation, and unsafe-delegation chain."
        ),
        "steps": [
            "permission_test",
            "tool_access_test",
            "memory_access_test",
            "unsafe_delegation_test",
        ],
        "ordered_steps": [
            "permission_test",
            "tool_access_test",
            "memory_access_test",
            "unsafe_delegation_test",
        ],
        "vulnerability_ids": [
            "V01",
            "V02",
            "V03",
            "V10",
        ],
        "entry_condition": (
            "The controlled authorization boundary is weak."
        ),
        "expected_goal": (
            "Controlled unsafe delegation is reached after "
            "the preceding chain steps."
        ),
        "dependencies": {
            "permission_test": [],
            "tool_access_test": [
                "permission_test",
            ],
            "memory_access_test": [
                "tool_access_test",
            ],
            "unsafe_delegation_test": [
                "memory_access_test",
            ],
        },
    },

    # =========================================================
    # P3 CHAIN E
    # V04 -> V06 -> V10
    # =========================================================

    "CHAIN_E": {
        "chain_id": "CHAIN_E",
        "name": (
            "Prompt Injection to Data Exposure to Unsafe Delegation"
        ),
        "chain_name": (
            "Prompt Injection to Data Exposure to Unsafe Delegation"
        ),
        "description": (
            "A controlled prompt-injection weakness followed "
            "by sensitive data exposure and unsafe delegation."
        ),
        "steps": [
            "prompt_injection_test",
            "sensitive_data_test",
            "unsafe_delegation_test",
        ],
        "ordered_steps": [
            "prompt_injection_test",
            "sensitive_data_test",
            "unsafe_delegation_test",
        ],
        "vulnerability_ids": [
            "V04",
            "V06",
            "V10",
        ],
        "entry_condition": (
            "A controlled prompt-injection weakness is present."
        ),
        "expected_goal": (
            "Controlled unsafe delegation is reached after "
            "sensitive data exposure."
        ),
        "dependencies": {
            "prompt_injection_test": [],
            "sensitive_data_test": [
                "prompt_injection_test",
            ],
            "unsafe_delegation_test": [
                "sensitive_data_test",
            ],
        },
    },
}