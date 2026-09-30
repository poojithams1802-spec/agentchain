import json
import re
from pathlib import Path
from typing import Any


KNOWLEDGE_FILE = (
    Path(__file__).parent
    / "knowledge"
    / "mitigation_knowledge.json"
)


class MitigationKnowledgeRetriever:
    """
    Phase 2 mitigation RAG.

    Retrieves predefined mitigation knowledge based on:
    - finding
    - control
    - topic
    - title
    - mitigation content
    - validation procedure
    """

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
        "must",
    }

    def __init__(
        self,
        knowledge_file: str | Path = KNOWLEDGE_FILE,
    ) -> None:

        self.knowledge_file = Path(
            knowledge_file
        )

        with open(
            self.knowledge_file,
            "r",
            encoding="utf-8",
        ) as file:

            self.documents: list[
                dict[str, Any]
            ] = json.load(file)

        if not isinstance(
            self.documents,
            list,
        ):
            raise ValueError(
                "Mitigation knowledge file must contain a list."
            )

    def tokenize(
        self,
        text: str,
    ) -> set[str]:

        words = re.findall(
            r"[a-zA-Z0-9_]+",
            text.lower(),
        )

        return {
            word
            for word in words
            if word not in self.STOPWORDS
        }

    def score(
        self,
        query_words: set[str],
        document: dict[str, Any],
    ) -> int:

        fields = [
            (
                document.get(
                    "control",
                    "",
                ),
                4,
            ),
            (
                " ".join(
                    document.get(
                        "target_findings",
                        [],
                    )
                ),
                5,
            ),
            (
                document.get(
                    "topic",
                    "",
                ),
                2,
            ),
            (
                document.get(
                    "title",
                    "",
                ),
                3,
            ),
            (
                document.get(
                    "content",
                    "",
                ),
                1,
            ),
            (
                document.get(
                    "validation",
                    "",
                ),
                1,
            ),
        ]

        total = 0

        for value, weight in fields:

            matches = len(
                query_words.intersection(
                    self.tokenize(
                        str(value)
                    )
                )
            )

            total += matches * weight

        return total

    def retrieve_documents(
        self,
        query: str,
        top_k: int = 5,
    ) -> list[dict[str, Any]]:

        if (
            top_k <= 0
            or not query
            or not query.strip()
        ):
            return []

        query_words = self.tokenize(
            query
        )

        if not query_words:
            return []

        ranked = []

        for index, document in enumerate(
            self.documents
        ):

            score = self.score(
                query_words,
                document,
            )

            if score > 0:

                ranked.append(
                    (
                        score,
                        index,
                        document,
                    )
                )

        ranked.sort(
            key=lambda item: (
                -item[0],
                item[1],
            )
        )

        return [
            document
            for _score, _index, document
            in ranked[:top_k]
        ]

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
    ) -> list[str]:

        documents = self.retrieve_documents(
            query,
            top_k=top_k,
        )

        results = []

        for document in documents:

            results.append(
                (
                    f"Control: "
                    f"{document['control']}; "

                    f"Target findings: "
                    f"{', '.join(document.get('target_findings', []))}; "

                    f"{document['title']}. "

                    f"{document['content']} "

                    f"Validation: "
                    f"{document['validation']}"
                )
            )

        return results