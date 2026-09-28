import sys
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).parent.parent)
)

from knowledge_ingestion import KnowledgeIngestor

def main():
    knowledge_file = (
        Path(__file__).parent.parent
        / "knowledge"
        / "security_knowledge.json"
    )

    ingestor = KnowledgeIngestor(
        knowledge_file
    )

    chunks = ingestor.ingest(
        chunk_size=50,
        overlap=10,
    )

    print("=" * 60)
    print("KNOWLEDGE INGESTION DEMO")
    print("=" * 60)

    print(f"Total chunks: {len(chunks)}")

    for chunk in chunks[:5]:
        print()
        print(f"ID: {chunk.chunk_id}")
        print(f"Document: {chunk.document_id}")
        print(f"Topic: {chunk.topic}")
        print(f"Title: {chunk.title}")
        print(f"Content: {chunk.content}")


if __name__ == "__main__":
    main()