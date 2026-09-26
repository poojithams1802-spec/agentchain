import json
from pathlib import Path

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

        self.model = SentenceTransformer(
            model_name
        )

        self.document_texts = [
            self.build_document_text(
                document
            )
            for document in self.documents
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
                self.documents[index]["content"]
            )

        return results