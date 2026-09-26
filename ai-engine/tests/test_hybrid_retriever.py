from hybrid_retriever import HybridKnowledgeRetriever


def test_hybrid_retriever_returns_semantic_results():
    retriever = HybridKnowledgeRetriever()

    results = retriever.retrieve(
        "agent uses sensitive tool without permission",
        top_k=3,
    )

    assert len(results) == 3

    combined = " ".join(
        results
    ).lower()

    assert "tool" in combined


def test_hybrid_retriever_falls_back_to_keyword(
    monkeypatch,
):
    retriever = HybridKnowledgeRetriever()

    def failing_retrieve(
        query,
        top_k=3,
    ):
        raise RuntimeError(
            "Simulated embedding failure"
        )

    monkeypatch.setattr(
        retriever.embedding_retriever,
        "retrieve",
        failing_retrieve,
    )

    results = retriever.retrieve(
        "unsafe tool access permission",
        top_k=3,
    )

    assert len(results) > 0

    combined = " ".join(
        results
    ).lower()

    assert "tool" in combined

def test_hybrid_retriever_returns_empty_for_empty_query():
    retriever = HybridKnowledgeRetriever()

    assert (
        retriever.retrieve(
            "",
            top_k=3,
        )
        == []
    )


def test_hybrid_retriever_returns_empty_for_invalid_top_k():
    retriever = HybridKnowledgeRetriever()

    assert (
        retriever.retrieve(
            "agent security",
            top_k=0,
        )
        == []
    )


    