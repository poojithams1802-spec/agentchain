
import pytest

from mitigation_selector import MitigationSelector
from mitigation_schemas import (
    MitigationFinding,
    MitigationSelectorInput,
)


class FakeRetriever:
    def __init__(self, result=None, error=None):
        self.result = result
        self.error = error

    def retrieve(self, query, top_k=5):
        if self.error:
            raise self.error
        return self.result


class FailingLLM:
    def generate_json(self, prompt):
        raise RuntimeError("Simulated Gemini failure")


class InvalidLLM:
    def generate_json(self, prompt):
        return {
            "selected_control": "invented_control",
            "reason": "Invalid control",
            "priority": 0.5,
            "confidence": 0.9,
        }


def make_request():
    return MitigationSelectorInput(
        findings=[
            MitigationFinding(
                finding="weak_permission_control",
                severity="high",
                evidence="Permission boundary is insufficiently enforced.",
                confidence=1.0,
            )
        ],
        attack_chain=["permission_test"],
        available_controls=[
            "authorization_gate",
            "tool_allowlist",
            "memory_validation",
        ],
        chain_state={"status": "active"},
    )


def test_empty_retrieval_is_reported():
    selector = MitigationSelector(
        llm_client=FailingLLM(),
        retriever=FakeRetriever(result=[]),
    )

    decision = selector.select(make_request())

    assert selector.last_metrics["rag_retrieval_status"] == "empty"
    assert selector.last_metrics["retrieved_documents"] == 0
    assert selector.last_metrics["rag_context_in_prompt"] is False
    assert selector.last_metrics["fallback_used"] is True
    assert decision.selected_control == "authorization_gate"


def test_retriever_exception_is_reported():
    selector = MitigationSelector(
        llm_client=FailingLLM(),
        retriever=FakeRetriever(
            error=RuntimeError("Simulated retrieval failure")
        ),
    )

    decision = selector.select(make_request())

    assert selector.last_metrics["rag_retrieval_status"] == "failed"
    assert "Simulated retrieval failure" in (
        selector.last_metrics["rag_retrieval_error"]
    )
    assert selector.last_metrics["fallback_used"] is True
    assert decision.selected_control == "authorization_gate"


def test_invalid_retriever_result_is_reported():
    selector = MitigationSelector(
        llm_client=FailingLLM(),
        retriever=FakeRetriever(result=None),
    )

    selector.select(make_request())

    assert (
        selector.last_metrics["rag_retrieval_status"]
        == "invalid_result"
    )
    assert selector.last_metrics["rag_retrieval_error"] is not None


def test_llm_failure_uses_fallback_and_records_error():
    selector = MitigationSelector(
        llm_client=FailingLLM(),
        retriever=FakeRetriever(
            result=["Relevant authorization mitigation knowledge"]
        ),
    )

    decision = selector.select(make_request())

    assert decision.selected_control == "authorization_gate"
    assert selector.last_metrics["llm_success"] is False
    assert selector.last_metrics["fallback_used"] is True
    assert "Simulated Gemini failure" in (
        selector.last_metrics["llm_error"]
    )
    assert selector.last_metrics["rag_retrieval_status"] == "success"
    assert selector.last_metrics["retrieved_documents"] == 1
    assert selector.last_metrics["rag_context_in_prompt"] is True


def test_invalid_llm_control_uses_fallback():
    selector = MitigationSelector(
        llm_client=InvalidLLM(),
        retriever=FakeRetriever(
            result=["Relevant authorization mitigation knowledge"]
        ),
    )

    decision = selector.select(make_request())

    assert decision.selected_control == "authorization_gate"
    assert selector.last_metrics["llm_success"] is False
    assert selector.last_metrics["fallback_used"] is True
    assert "ValidationError" in selector.last_metrics["llm_error"]

def test_metrics_are_reset_between_retrievals():
    selector = MitigationSelector(
        llm_client=FailingLLM(),
        retriever=FakeRetriever(
            error=RuntimeError("First failure")
        ),
    )

    request = make_request()
    selector.retrieve_knowledge(request)

    assert selector._last_rag_status == "failed"

    selector.retriever = FakeRetriever(
        result=["Relevant mitigation knowledge"]
    )
    results = selector.retrieve_knowledge(request)

    assert selector._last_rag_status == "success"
    assert selector._last_rag_error is None
    assert len(results) == 1
