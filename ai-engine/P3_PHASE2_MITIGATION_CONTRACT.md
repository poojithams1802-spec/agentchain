# AgentChain Phase 2 — Person 3

# AI/RAG Mitigation Reasoning & Control Selection Contract

## 1. Purpose

Person 3 is responsible for the AI/RAG mitigation reasoning layer.

The purpose of this component is to select an approved defensive control based on:

- detected security finding
- finding severity
- evidence
- attack-chain context
- current chain state
- retrieved mitigation knowledge

The selector does not modify source code or generate arbitrary security patches.

---

## 2. Approved Defensive Controls

The mitigation system supports exactly three predefined controls:

1. `authorization_gate`
2. `tool_allowlist`
3. `memory_validation`

The LLM is restricted to selecting from these approved controls.

---

## 3. Finding-to-Control Mapping

The expected defensive control mapping is:

| Finding                      | Defensive Control    |
| ---------------------------- | -------------------- |
| `weak_permission_control`    | `authorization_gate` |
| `unsafe_tool_access`         | `tool_allowlist`     |
| `memory_validation_weakness` | `memory_validation`  |

This mapping is used for validation and deterministic fallback behavior.

---

## 4. P2 → P3 Input Contract

P2 provides mitigation information through:

`MitigationSelectorInput`

The input contains:

- findings
- severity
- evidence
- attack-chain context
- available controls
- current chain state
- retrieved mitigation knowledge

Example:

```python
MitigationSelectorInput(
    findings=[
        {
            "finding": "weak_permission_control",
            "severity": "high",
            "evidence": "Permission was DENIED, but the protected operation was still executed.",
            "confidence": 1.0,
        }
    ],
    attack_chain=[
        "permission_test",
        "protected_operation"
    ],
    available_controls=[
        "authorization_gate",
        "tool_allowlist",
        "memory_validation"
    ],
)
```
