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


def test_retriever_handles_punctuation():
    retriever = KnowledgeRetriever()

    results = retriever.retrieve(
        "authorization, permissions!",
        top_k=3
    )

    assert len(results) > 0


def test_retriever_ignores_stopwords():
    retriever = KnowledgeRetriever()

    results = retriever.retrieve(
        "the and is a",
        top_k=3
    )

    assert results == []


def test_retriever_returns_empty_for_invalid_top_k():
    retriever = KnowledgeRetriever()

    assert retriever.retrieve(
        "tool access",
        top_k=0
    ) == []

    assert retriever.retrieve(
        "tool access",
        top_k=-1
    ) == []


def test_retriever_matches_topic_terms():
    retriever = KnowledgeRetriever()

    results = retriever.retrieve(
        "prompt_injection",
        top_k=1
    )

    assert len(results) == 1

    assert (
        "higher-priority system instructions"
        in results[0]
    )