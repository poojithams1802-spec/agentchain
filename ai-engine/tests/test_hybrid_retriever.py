from hybrid_retriever import HybridKnowledgeRetriever


def test_hybrid_retriever_returns_semantic_results():
    retriever = HybridKnowledgeRetriever()

    results = retriever.retrieve(
        "agent tool access without authorization",
        top_k=3,
    )

    assert len(results) == 3


def test_hybrid_retriever_finds_security_knowledge():
    retriever = HybridKnowledgeRetriever()

    results = retriever.retrieve(
        "agent uses sensitive tool without permission",
        top_k=3,
    )

    combined_results = " ".join(
        results
    ).lower()

    assert (
        "tool" in combined_results
        or "permission" in combined_results
        or "authorization" in combined_results
    )


def test_hybrid_retriever_handles_empty_query():
    retriever = HybridKnowledgeRetriever()

    results = retriever.retrieve(
        "",
        top_k=3,
    )

    assert results == []


def test_hybrid_retriever_handles_invalid_top_k():
    retriever = HybridKnowledgeRetriever()

    results = retriever.retrieve(
        "agent security",
        top_k=0,
    )

    assert results == []


def test_hybrid_retriever_combines_rankings():
    retriever = HybridKnowledgeRetriever.__new__(
        HybridKnowledgeRetriever
    )

    semantic_results = [
        "semantic_result",
        "shared_result",
    ]

    keyword_results = [
        "shared_result",
        "keyword_result",
    ]

    results = retriever.reciprocal_rank_fusion(
        [
            semantic_results,
            keyword_results,
        ],
        top_k=3,
    )

    assert len(results) == 3

    assert "semantic_result" in results
    assert "shared_result" in results
    assert "keyword_result" in results


def test_hybrid_retriever_falls_back_when_embedding_fails():
    retriever = HybridKnowledgeRetriever.__new__(
        HybridKnowledgeRetriever
    )

    class FakeKeywordRetriever:
        def retrieve(
            self,
            query,
            top_k=3,
        ):
            return [
                "keyword_result_1",
                "keyword_result_2",
            ]

    class FakeEmbeddingRetriever:
        def retrieve(
            self,
            query,
            top_k=3,
        ):
            raise RuntimeError(
                "Embedding model unavailable."
            )

    retriever.keyword_retriever = FakeKeywordRetriever()
    retriever.embedding_retriever = FakeEmbeddingRetriever()

    results = retriever.retrieve(
        "agent tool authorization",
        top_k=2,
    )

    assert results == [
        "keyword_result_1",
        "keyword_result_2",
    ]


def test_rrf_handles_duplicate_results():
    retriever = HybridKnowledgeRetriever.__new__(
        HybridKnowledgeRetriever
    )

    results = retriever.reciprocal_rank_fusion(
        [
            [
                "result_a",
                "result_a",
                "result_b",
            ],
            [
                "result_b",
                "result_c",
            ],
        ],
        top_k=3,
    )

    assert len(results) == 3
    assert set(results) == {
        "result_a",
        "result_b",
        "result_c",
    }


def test_rrf_respects_top_k():
    retriever = HybridKnowledgeRetriever.__new__(
        HybridKnowledgeRetriever
    )

    results = retriever.reciprocal_rank_fusion(
        [
            [
                "result_a",
                "result_b",
                "result_c",
            ],
            [
                "result_d",
                "result_e",
                "result_f",
            ],
        ],
        top_k=2,
    )

    assert len(results) == 2


def test_rrf_handles_empty_result_lists():
    retriever = HybridKnowledgeRetriever.__new__(
        HybridKnowledgeRetriever
    )

    results = retriever.reciprocal_rank_fusion(
        [
            [],
            [],
        ],
        top_k=3,
    )

    assert results == []


def test_rrf_handles_invalid_top_k():
    retriever = HybridKnowledgeRetriever.__new__(
        HybridKnowledgeRetriever
    )

    results = retriever.reciprocal_rank_fusion(
        [
            ["result_a"],
            ["result_b"],
        ],
        top_k=0,
    )

    assert results == []

def test_hybrid_retrieve_chunks_returns_metadata():
    retriever = HybridKnowledgeRetriever()

    results = retriever.retrieve_chunks(
        "unsafe tool access",
        top_k=3,
    )

    assert results

    first = results[0]

    assert "content" in first
    assert "chunk_id" in first
    assert "document_id" in first
    assert "topic" in first
    assert "title" in first
    assert "similarity" in first


def test_hybrid_retrieve_chunks_combines_sources(
    monkeypatch,
):
    retriever = HybridKnowledgeRetriever()

    semantic_chunks = [
        {
            "chunk_id": "KB001_CHUNK_1",
            "document_id": "KB001",
            "topic": "tool_security",
            "title": "Unsafe tool access",
            "content": "semantic result",
            "similarity": 0.91,
        },
        {
            "chunk_id": "KB002_CHUNK_1",
            "document_id": "KB002",
            "topic": "authorization",
            "title": "Permission validation",
            "content": "shared result",
            "similarity": 0.87,
        },
    ]

    keyword_results = [
        "shared result",
        "keyword result",
    ]

    monkeypatch.setattr(
        retriever.embedding_retriever,
        "retrieve_chunks",
        lambda query, top_k: semantic_chunks,
    )

    monkeypatch.setattr(
        retriever.keyword_retriever,
        "retrieve",
        lambda query, top_k: keyword_results,
    )

    results = retriever.retrieve_chunks(
        "security",
        top_k=3,
    )

    contents = [
        result["content"]
        for result in results
    ]

    assert "shared result" in contents
    assert "semantic result" in contents
    assert "keyword result" in contents


def test_hybrid_retrieve_chunks_empty_query():
    retriever = HybridKnowledgeRetriever()

    results = retriever.retrieve_chunks(
        "",
        top_k=3,
    )

    assert results == []

def test_hybrid_retrieve_chunks_invalid_top_k():
    retriever = HybridKnowledgeRetriever()

    results = retriever.retrieve_chunks(
        "security",
        top_k=0,
    )

    assert results == []

def test_hybrid_retrieve_chunks_keyword_only(
    monkeypatch,
):
    retriever = HybridKnowledgeRetriever()

    monkeypatch.setattr(
        retriever.embedding_retriever,
        "retrieve_chunks",
        lambda query, top_k: [],
    )

    monkeypatch.setattr(
        retriever.keyword_retriever,
        "retrieve",
        lambda query, top_k: [
            "keyword result"
        ],
    )

    results = retriever.retrieve_chunks(
        "security",
        top_k=3,
    )

    assert len(results) == 1
    assert results[0]["content"] == (
        "keyword result"
    )
    assert results[0]["chunk_id"] is None

def test_hybrid_retrieve_chunks_embedding_failure(
    monkeypatch,
):
    retriever = HybridKnowledgeRetriever()

    def failing_retrieval(
        query,
        top_k,
    ):
        raise RuntimeError(
            "Embedding model unavailable"
        )

    monkeypatch.setattr(
        retriever.embedding_retriever,
        "retrieve_chunks",
        failing_retrieval,
    )

    monkeypatch.setattr(
        retriever.keyword_retriever,
        "retrieve",
        lambda query, top_k: [
            "keyword fallback"
        ],
    )

    results = retriever.retrieve_chunks(
        "security",
        top_k=3,
    )

    assert results
    assert results[0]["content"] == (
        "keyword fallback"
    )
    assert results[0]["chunk_id"] is None
    assert results[0]["similarity"] is None