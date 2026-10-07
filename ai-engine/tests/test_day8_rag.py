from retriever import KnowledgeRetriever


def test_day8_retrieves_indirect_prompt_injection():
    retriever = KnowledgeRetriever()

    results = retriever.retrieve(
        "indirect prompt injection retrieved document untrusted instructions",
        top_k=3,
    )

    assert any(
        "indirect prompt injection" in result.lower()
        for result in results
    )


def test_day8_retrieves_sensitive_data_exposure():
    retriever = KnowledgeRetriever()

    results = retriever.retrieve(
        "sensitive data exposure unauthorized disclosure agent communication",
        top_k=3,
    )

    assert any(
        "sensitive information" in result.lower()
        or "sensitive data" in result.lower()
        for result in results
    )


def test_day8_prompt_injection_validation_knowledge():
    retriever = KnowledgeRetriever()

    results = retriever.retrieve(
        "prompt injection validation trusted instructions authorization evidence",
        top_k=5,
    )

    assert any(
        "prompt-injection findings should be validated" in result.lower()
        for result in results
    )


def test_day8_knowledge_entries_exist():
    retriever = KnowledgeRetriever()

    ids = {document["id"] for document in retriever.documents}

    assert {"KB025", "KB026", "KB027"}.issubset(ids)
