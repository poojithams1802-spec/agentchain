from hybrid_retriever import HybridKnowledgeRetriever


def test_rrf_rewards_results_found_by_both_retrievers():
    retriever = HybridKnowledgeRetriever.__new__(
        HybridKnowledgeRetriever
    )

    results = retriever.reciprocal_rank_fusion(
        [
            [
                "shared",
                "semantic_only",
            ],
            [
                "shared",
                "keyword_only",
            ],
        ],
        top_k=3,
    )

    assert results[0] == "shared"


def test_rrf_combines_multiple_sources():
    retriever = HybridKnowledgeRetriever.__new__(
        HybridKnowledgeRetriever
    )

    results = retriever.reciprocal_rank_fusion(
        [
            ["a", "b"],
            ["b", "c"],
        ],
        top_k=3,
    )

    assert set(results) == {
        "a",
        "b",
        "c",
    }


def test_rrf_deduplicates_results_within_source():
    retriever = HybridKnowledgeRetriever.__new__(
        HybridKnowledgeRetriever
    )

    results = retriever.reciprocal_rank_fusion(
        [
            ["a", "a", "b"],
        ],
        top_k=3,
    )

    assert results == [
        "a",
        "b",
    ]


def test_rrf_respects_top_k():
    retriever = HybridKnowledgeRetriever.__new__(
        HybridKnowledgeRetriever
    )

    results = retriever.reciprocal_rank_fusion(
        [
            ["a", "b", "c", "d"],
        ],
        top_k=2,
    )

    assert len(results) == 2


def test_rrf_invalid_top_k_returns_empty():
    retriever = HybridKnowledgeRetriever.__new__(
        HybridKnowledgeRetriever
    )

    results = retriever.reciprocal_rank_fusion(
        [
            ["a", "b"],
        ],
        top_k=0,
    )

    assert results == []