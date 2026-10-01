import sys
from pathlib import Path

AI_ENGINE_DIR = Path(__file__).resolve().parents[1]

if str(AI_ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(AI_ENGINE_DIR))

from mitigation_reasoning import MitigationReasoning


def test_build_mitigation_reasoning_record():
    reasoning = MitigationReasoning()

    record = reasoning.build_record(
        finding="weak_permission_control",
        severity="high",
        evidence=(
            "Permission was DENIED, but the protected "
            "operation was still executed."
        ),
        attack_chain=[
            "permission_test",
            "protected_operation",
        ],
        selected_control="authorization_gate",
        reason=(
            "Authorization must be enforced before "
            "protected operations are executed."
        ),
        priority=0.9,
        confidence=1.0,
        retrieved_knowledge=[
            "Authorization gate for weak permission control."
        ],
        llm_used=True,
        fallback_used=False,
    )

    assert record["finding"] == "weak_permission_control"
    assert record["severity"] == "high"
    assert record["selected_control"] == "authorization_gate"
    assert record["priority"] == 0.9
    assert record["confidence"] == 1.0
    assert record["llm_used"] is True
    assert record["fallback_used"] is False

    assert isinstance(record["attack_chain"], list)
    assert isinstance(record["retrieved_knowledge"], list)
    assert isinstance(record["reason"], str)