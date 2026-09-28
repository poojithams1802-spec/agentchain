import json
from pathlib import Path
from knowledge_ingestion import KnowledgeIngestor
from sentence_transformers import SentenceTransformer


KNOWLEDGE_FILE = (
    Path(__file__).parent
    / "knowledge"
    / "security_knowledge.json"
)

MODEL_NAME = "all-MiniLM-L6-v2"


class EmbeddingKnowledgeRetriever:
    """
    Semantic security knowledge retriever.

    Uses a local Sentence Transformer model to convert
    the query and knowledge documents into embeddings,
    then ranks documents using cosine similarity.
    """

    def __init__(
        self,
        model_name: str = MODEL_NAME,
    ) -> None:

        with open(
            KNOWLEDGE_FILE,
            "r",
            encoding="utf-8",
        ) as file:
            self.documents = json.load(file)

        self.ingestor = KnowledgeIngestor(
            KNOWLEDGE_FILE
        )

        self.chunks = self.ingestor.ingest(
            chunk_size=500,
            overlap=100,
        )

        self.model = SentenceTransformer(
            model_name
        )

        self.document_texts = [
            chunk.content
            for chunk in self.chunks
        ]

        self.document_embeddings = (
            self.model.encode(
                self.document_texts,
                normalize_embeddings=True,
            )
        )

    def build_document_text(
        self,
        document: dict,
    ) -> str:
        """
        Combine the structured knowledge fields into
        one semantic document representation.
        """

        return " ".join(
            [
                document.get("topic", ""),
                document.get("title", ""),
                document.get("content", ""),
            ]
        ).strip()

    def retrieve(
        self,
        query: str,
        top_k: int = 3,
    ) -> list[str]:

        if top_k <= 0:
            return []

        if not query or not query.strip():
            return []

        query_embedding = self.model.encode(
            [query],
            normalize_embeddings=True,
        )[0]

        similarities = (
            self.document_embeddings
            @ query_embedding
        )

        ranked_indices = sorted(
            range(
                len(similarities)
            ),
            key=lambda index: (
                -float(similarities[index]),
                index,
            ),
        )

        results = []

        for index in ranked_indices[:top_k]:
            results.append(
                self.chunks[index].content
            )

        return results


    def retrieve_chunks(
        self,
        query: str,
        top_k: int = 3,
    ) -> list[dict]:

        if top_k <= 0:
            return []

        if not query or not query.strip():
            return []

        query_embedding = self.model.encode(
            [query],
            normalize_embeddings=True,
        )[0]

        similarities = (
            self.document_embeddings
            @ query_embedding
        )

        ranked_indices = sorted(
            range(len(similarities)),
            key=lambda index: (
                -float(similarities[index]),
                index,
            ),
        )

        results = []

        for index in ranked_indices[:top_k]:
            chunk = self.chunks[index]

            results.append(
                {
                    "chunk_id": chunk.chunk_id,
                    "document_id": chunk.document_id,
                    "topic": chunk.topic,
                    "title": chunk.title,
                    "content": chunk.content,
                    "similarity": float(
                        similarities[index]
                    ),
                }
            )

        return results