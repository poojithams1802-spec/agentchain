from pathlib import Path

import pytest

from knowledge_ingestion import KnowledgeIngestor


KNOWLEDGE_FILE = (
    Path(__file__).parent.parent
    / "knowledge"
    / "security_knowledge.json"
)


def test_load_documents():
    ingestor = KnowledgeIngestor(KNOWLEDGE_FILE)

    documents = ingestor.load_documents()

    assert isinstance(documents, list)
    assert len(documents) > 0


def test_build_document_text():
    ingestor = KnowledgeIngestor(KNOWLEDGE_FILE)

    documents = ingestor.load_documents()

    text = ingestor.build_document_text(
        documents[0]
    )

    assert isinstance(text, str)
    assert text.strip()


def test_chunk_text():
    ingestor = KnowledgeIngestor(KNOWLEDGE_FILE)

    text = " ".join(
        f"word{i}"
        for i in range(120)
    )

    chunks = ingestor.chunk_text(
        text,
        chunk_size=50,
        overlap=10,
    )

    assert len(chunks) > 1
    assert all(chunk.strip() for chunk in chunks)


def test_chunk_overlap():
    ingestor = KnowledgeIngestor(KNOWLEDGE_FILE)

    text = " ".join(
        f"word{i}"
        for i in range(100)
    )

    chunks = ingestor.chunk_text(
        text,
        chunk_size=40,
        overlap=10,
    )

    first_words = chunks[0].split()
    second_words = chunks[1].split()

    assert first_words[-10:] == second_words[:10]


def test_empty_text_returns_no_chunks():
    ingestor = KnowledgeIngestor(KNOWLEDGE_FILE)

    assert ingestor.chunk_text("") == []


def test_invalid_chunk_size():
    ingestor = KnowledgeIngestor(KNOWLEDGE_FILE)

    with pytest.raises(ValueError):
        ingestor.chunk_text(
            "some text",
            chunk_size=0,
        )


def test_invalid_overlap():
    ingestor = KnowledgeIngestor(KNOWLEDGE_FILE)

    with pytest.raises(ValueError):
        ingestor.chunk_text(
            "some text",
            chunk_size=10,
            overlap=10,
        )


def test_ingest_creates_chunks():
    ingestor = KnowledgeIngestor(KNOWLEDGE_FILE)

    chunks = ingestor.ingest(
        chunk_size=50,
        overlap=10,
    )

    assert chunks
    assert all(
        chunk.chunk_id
        for chunk in chunks
    )
    assert all(
        chunk.document_id
        for chunk in chunks
    )
    assert all(
        chunk.content
        for chunk in chunks
    )