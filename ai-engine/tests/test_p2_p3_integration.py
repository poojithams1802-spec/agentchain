import sys
from pathlib import Path

AI_ENGINE_DIR = Path(__file__).resolve().parents[1]

if str(AI_ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(AI_ENGINE_DIR))

from mitigation_selector import MitigationSelector
from mitigation_schemas import MitigationSelectorInput


def test_p2_p3_selector_contract():
    selector = MitigationSelector()

    request = MitigationSelectorInput(
        findings=[
            {
                "finding": "weak_permission_control",
                "severity": "high",
                "evidence": (
                    "Permission was DENIED, but the protected "
                    "operation was still executed."
                ),
                "confidence": 1.0,
            }
        ],
        attack_chain=[
            "permission_test",
            "protected_operation",
        ],
        available_controls=[
            "authorization_gate",
            "tool_allowlist",
            "memory_validation",
        ],
    )

    decision = selector.select(request)

    assert decision.selected_control in {
        "authorization_gate",
        "tool_allowlist",
        "memory_validation",
    }

    assert isinstance(decision.reason, str)
    assert len(decision.reason) > 0

    assert isinstance(decision.confidence, float)
    assert 0.0 <= decision.confidence <= 1.0