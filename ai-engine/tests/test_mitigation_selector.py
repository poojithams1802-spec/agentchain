import sys
from pathlib import Path

AI_ENGINE_DIR = Path(__file__).resolve().parents[1]

if str(AI_ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(AI_ENGINE_DIR))

from mitigation_selector import MitigationSelector
from mitigation_schemas import MitigationSelectorInput


APPROVED_CONTROLS = [
    "authorization_gate",
    "tool_allowlist",
    "memory_validation",
]


class FakeRetriever:
    def retrieve(self, query, top_k=5):
        return [
            "Control: authorization_gate; Target findings: weak_permission_control"
        ]


class FakeLLM:
    def __init__(self, response):
        self.response = response

    def generate_json(self, prompt):
        return self.response


def make_request():
    return MitigationSelectorInput(
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
        available_controls=APPROVED_CONTROLS,
    )


def test_wrong_control_is_rejected():
    """
    The LLM incorrectly recommends tool_allowlist for
    weak_permission_control.

    P3 must reject the wrong control and safely fall back
    to authorization_gate.
    """

    selector = MitigationSelector(
        llm_client=FakeLLM(
            {
                "selected_control": "tool_allowlist",
                "reason": "Incorrect control recommendation",
                "priority": 0.9,
                "confidence": 0.95,
            }
        ),
        retriever=FakeRetriever(),
    )

    decision = selector.select(make_request())

    assert decision.selected_control == "authorization_gate"
    assert selector.last_metrics["fallback_used"] is True
    assert selector.last_metrics["llm_success"] is False


def test_unknown_control_is_rejected():
    """
    The LLM returns a control that is not part of the
    approved mitigation-control set.
    """

    selector = MitigationSelector(
        llm_client=FakeLLM(
            {
                "selected_control": "disable_security",
                "reason": "Unknown control",
                "priority": 0.9,
                "confidence": 0.95,
            }
        ),
        retriever=FakeRetriever(),
    )

    decision = selector.select(make_request())

    assert decision.selected_control == "authorization_gate"
    assert selector.last_metrics["fallback_used"] is True
    assert selector.last_metrics["llm_success"] is False


def test_correct_control_is_accepted():
    """
    A valid LLM recommendation should be accepted.
    """

    selector = MitigationSelector(
        llm_client=FakeLLM(
            {
                "selected_control": "authorization_gate",
                "reason": "Authorization must be enforced before execution.",
                "priority": 0.9,
                "confidence": 0.95,
            }
        ),
        retriever=FakeRetriever(),
    )

    decision = selector.select(make_request())

    assert decision.selected_control == "authorization_gate"
    assert selector.last_metrics["fallback_used"] is False
    assert selector.last_metrics["llm_success"] is True


def test_llm_failure_uses_safe_fallback():
    """
    If the LLM is unavailable, P3 should still return
    the correct approved control.
    """

    class FailingLLM:
        def generate_json(self, prompt):
            raise RuntimeError("LLM unavailable")

    selector = MitigationSelector(
        llm_client=FailingLLM(),
        retriever=FakeRetriever(),
    )

    decision = selector.select(make_request())

    assert decision.selected_control == "authorization_gate"
    assert selector.last_metrics["fallback_used"] is True
    assert selector.last_metrics["llm_success"] is False