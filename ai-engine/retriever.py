import json
import re
from pathlib import Path


KNOWLEDGE_FILE = (
    Path(__file__).parent
    / "knowledge"
    / "security_knowledge.json"
)


STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "should",
    "that",
    "the",
    "their",
    "this",
    "to",
    "with",
}


class KnowledgeRetriever:
    def __init__(self) -> None:
        with open(
            KNOWLEDGE_FILE,
            "r",
            encoding="utf-8"
        ) as file:
            self.documents = json.load(file)

    def tokenize(
        self,
        text: str
    ) -> set[str]:
        words = re.findall(
            r"[a-zA-Z0-9_]+",
            text.lower()
        )

        return {
            word
            for word in words
            if word not in STOPWORDS
        }

    def calculate_score(
        self,
        query_words: set[str],
        document: dict
    ) -> int:
        topic_words = self.tokenize(
            document["topic"]
        )

        title_words = self.tokenize(
            document["title"]
        )

        content_words = self.tokenize(
            document["content"]
        )

        topic_score = len(
            query_words.intersection(
                topic_words
            )
        )

        title_score = len(
            query_words.intersection(
                title_words
            )
        )

        content_score = len(
            query_words.intersection(
                content_words
            )
        )

        return (
            topic_score * 3
            + title_score * 2
            + content_score
        )

    def retrieve(
        self,
        query: str,
        top_k: int = 3
    ) -> list[str]:
        if top_k <= 0:
            return []

        query_words = self.tokenize(query)

        if not query_words:
            return []

        scored_documents = []

        for index, document in enumerate(
            self.documents
        ):
            score = self.calculate_score(
                query_words,
                document
            )

            if score > 0:
                scored_documents.append(
                    (
                        score,
                        index,
                        document
                    )
                )

        scored_documents.sort(
            key=lambda item: (
                -item[0],
                item[1]
            )
        )

        results = []

        for score, index, document in (
            scored_documents[:top_k]
        ):
            results.append(
                document["content"]
            )

        return results