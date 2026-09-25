import json
from pathlib import Path


KNOWLEDGE_FILE = (
    Path(__file__).parent
    / "knowledge"
    / "security_knowledge.json"
)


class KnowledgeRetriever:
    def __init__(self) -> None:
        with open(
            KNOWLEDGE_FILE,
            "r",
            encoding="utf-8"
        ) as file:
            self.documents = json.load(file)

    def retrieve(
        self,
        query: str,
        top_k: int = 3
    ) -> list[str]:
        query_words = set(
            query.lower().split()
        )

        scored_documents = []

        for document in self.documents:
            text = (
                document["topic"]
                + " "
                + document["title"]
                + " "
                + document["content"]
            ).lower()

            document_words = set(
                text.split()
            )

            score = len(
                query_words.intersection(
                    document_words
                )
            )

            scored_documents.append(
                (score, document)
            )

        scored_documents.sort(
            key=lambda item: item[0],
            reverse=True
        )

        results = []

        for score, document in scored_documents:
            if score <= 0:
                continue

            results.append(
                document["content"]
            )

            if len(results) >= top_k:
                break

        return results