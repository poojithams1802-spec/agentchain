from retriever import KnowledgeRetriever


def test_retriever_returns_relevant_knowledge():
    retriever = KnowledgeRetriever()

    results = retriever.retrieve(
        "unsafe tool access",
        top_k=3
    )

    assert len(results) > 0
    assert any(
        "authorization" in result.lower()
        or "permissions" in result.lower()
        for result in results
    )


def test_retriever_respects_top_k():
    retriever = KnowledgeRetriever()

    results = retriever.retrieve(
        "tool access",
        top_k=1
    )

    assert len(results) <= 1


def test_retriever_returns_empty_for_unknown_query():
    retriever = KnowledgeRetriever()

    results = retriever.retrieve(
        "xyznonexistenttopic123",
        top_k=3
    )

    assert results == []