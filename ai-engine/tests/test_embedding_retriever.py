import pytest

from embedding_retriever import (
    EmbeddingKnowledgeRetriever,
)


@pytest.fixture
def retriever():
    return EmbeddingKnowledgeRetriever()


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

def test_retriever_creates_chunks(retriever):
    assert retriever.chunks
    assert len(retriever.chunks) == len(
        retriever.document_texts
    )


def test_embeddings_match_chunk_count(retriever):
    assert len(
        retriever.document_embeddings
    ) == len(retriever.chunks)


def test_retrieve_returns_chunk_content(retriever):
    results = retriever.retrieve(
        "unsafe tool access",
        top_k=3,
    )

    assert results

    assert all(
        isinstance(result, str)
        for result in results
    )


def test_retrieve_chunks_returns_metadata(
    retriever,
):
    results = retriever.retrieve_chunks(
        "unsafe tool access",
        top_k=3,
    )

    assert results

    first = results[0]

    assert "chunk_id" in first
    assert "document_id" in first
    assert "topic" in first
    assert "title" in first
    assert "content" in first
    assert "similarity" in first


def test_retrieve_chunks_similarity(
    retriever,
):
    results = retriever.retrieve_chunks(
        "permission validation",
        top_k=3,
    )

    assert results

    for result in results:
        assert 0.0 <= result["similarity"] <= 1.0