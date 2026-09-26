from embedding_retriever import EmbeddingKnowledgeRetriever
from retriever import KnowledgeRetriever


class HybridKnowledgeRetriever:
    """
    Hybrid security knowledge retriever.

    Uses semantic retrieval first and falls back to
    keyword retrieval if semantic retrieval fails.
    """

    def __init__(self) -> None:
        self.keyword_retriever = KnowledgeRetriever()
        self.embedding_retriever = (
            EmbeddingKnowledgeRetriever()
        )

    def retrieve(
        self,
        query: str,
        top_k: int = 3,
    ) -> list[str]:

        if top_k <= 0:
            return []

        if not query or not query.strip():
            return []

        try:
            results = (
                self.embedding_retriever.retrieve(
                    query,
                    top_k=top_k,
                )
            )

            if results:
                return results

        except Exception as error:
            print(
                "[Hybrid Retriever Warning] "
                f"Embedding retrieval failed: "
                f"{type(error).__name__}: {error}"
            )

        return self.keyword_retriever.retrieve(
            query,
            top_k=top_k,
        )