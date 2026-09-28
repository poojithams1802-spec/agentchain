import json
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class KnowledgeChunk:
    chunk_id: str
    document_id: str
    topic: str
    title: str
    content: str


class KnowledgeIngestor:
    def __init__(self, knowledge_file: str | Path) -> None:
        self.knowledge_file = Path(knowledge_file)

    def load_documents(self) -> list[dict]:
        with open(
            self.knowledge_file,
            "r",
            encoding="utf-8",
        ) as file:
            documents = json.load(file)

        if not isinstance(documents, list):
            raise ValueError(
                "Knowledge file must contain a list of documents."
            )

        return documents

    def normalize_text(self, text: str) -> str:
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def build_document_text(self, document: dict) -> str:
        parts = [
            document.get("topic", ""),
            document.get("title", ""),
            document.get("content", ""),
        ]

        return " ".join(
            self.normalize_text(str(part))
            for part in parts
            if part
        ).strip()

    def chunk_text(
        self,
        text: str,
        chunk_size: int = 500,
        overlap: int = 100,
    ) -> list[str]:
        if chunk_size <= 0:
            raise ValueError(
                "chunk_size must be greater than 0."
            )

        if overlap < 0:
            raise ValueError(
                "overlap must not be negative."
            )

        if overlap >= chunk_size:
            raise ValueError(
                "overlap must be smaller than chunk_size."
            )

        words = text.split()

        if not words:
            return []

        chunks = []
        start = 0

        while start < len(words):
            end = min(
                start + chunk_size,
                len(words),
            )

            chunk = " ".join(words[start:end])

            if chunk:
                chunks.append(chunk)

            if end == len(words):
                break

            start = end - overlap

        return chunks

    def ingest(
        self,
        chunk_size: int = 500,
        overlap: int = 100,
    ) -> list[KnowledgeChunk]:

        documents = self.load_documents()

        chunks: list[KnowledgeChunk] = []

        for document_index, document in enumerate(documents):
            document_id = str(
                document.get(
                    "id",
                    f"DOC_{document_index + 1}",
                )
            )

            topic = self.normalize_text(
                str(document.get("topic", ""))
            )

            title = self.normalize_text(
                str(document.get("title", ""))
            )

            text = self.build_document_text(document)

            document_chunks = self.chunk_text(
                text,
                chunk_size=chunk_size,
                overlap=overlap,
            )

            for chunk_index, content in enumerate(
                document_chunks
            ):
                chunks.append(
                    KnowledgeChunk(
                        chunk_id=(
                            f"{document_id}_"
                            f"CHUNK_{chunk_index + 1}"
                        ),
                        document_id=document_id,
                        topic=topic,
                        title=title,
                        content=content,
                    )
                )

        return chunks