from embedding_retriever import EmbeddingKnowledgeRetriever


def test_embedding_retriever_returns_results():
    retriever = EmbeddingKnowledgeRetriever()

    results = retriever.retrieve(
        "agent tool access without permission",
        top_k=3,
    )

    assert len(results) == 3


def test_embedding_retriever_finds_tool_security():
    retriever = EmbeddingKnowledgeRetriever()

    results = retriever.retrieve(
        "an agent uses a sensitive tool without authorization",
        top_k=3,
    )

    combined_results = " ".join(
        results
    ).lower()

    assert "tool" in combined_results
    assert (
        "permission" in combined_results
        or "authorization" in combined_results
    )


def test_embedding_retriever_finds_memory_security():
    retriever = EmbeddingKnowledgeRetriever()

    results = retriever.retrieve(
        "untrusted information is stored in agent memory",
        top_k=3,
    )

    combined_results = " ".join(
        results
    ).lower()

    assert "memory" in combined_results


def test_embedding_retriever_respects_top_k():
    retriever = EmbeddingKnowledgeRetriever()

    results = retriever.retrieve(
        "agent security",
        top_k=2,
    )

    assert len(results) == 2


def test_embedding_retriever_handles_empty_query():
    retriever = EmbeddingKnowledgeRetriever()

    results = retriever.retrieve(
        "",
        top_k=3,
    )

    assert results == []


def test_embedding_retriever_handles_invalid_top_k():
    retriever = EmbeddingKnowledgeRetriever()

    results = retriever.retrieve(
        "agent security",
        top_k=0,
    )

    assert results == []