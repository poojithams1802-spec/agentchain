from embedding_retriever import EmbeddingKnowledgeRetriever
from retriever import KnowledgeRetriever


class HybridKnowledgeRetriever:
    """
    Hybrid security knowledge retriever.

    Combines:
    - semantic retrieval using embeddings
    - keyword retrieval using lexical matching

    Results are merged using Reciprocal Rank Fusion (RRF).

    If semantic retrieval fails, keyword retrieval is used
    as a safe fallback.
    """

    RRF_K = 60

    def __init__(self) -> None:
        self.keyword_retriever = KnowledgeRetriever()
        self.embedding_retriever = EmbeddingKnowledgeRetriever()

    def reciprocal_rank_fusion(
        self,
        result_lists: list[list[str]],
        top_k: int,
    ) -> list[str]:
        """
        Combine ranked result lists using Reciprocal Rank Fusion.

        RRF score:

            1 / (k + rank)

        Rank starts at 1.
        """

        if top_k <= 0:
            return []

        scores: dict[str, float] = {}

        for results in result_lists:
            seen_in_list: set[str] = set()

            for rank, result in enumerate(
                results,
                start=1,
            ):
                if not result:
                    continue

                if result in seen_in_list:
                    continue

                seen_in_list.add(result)

                scores[result] = (
                    scores.get(result, 0.0)
                    + 1.0 / (self.RRF_K + rank)
                )

        ranked_results = sorted(
            scores.items(),
            key=lambda item: (
                -item[1],
                item[0],
            ),
        )

        return [
            result
            for result, _score in ranked_results[:top_k]
        ]

    def retrieve(
        self,
        query: str,
        top_k: int = 3,
    ) -> list[str]:
        """
        Retrieve security knowledge using semantic
        and keyword retrieval.

        Results are combined using Reciprocal Rank
        Fusion.

        This method preserves the original planner
        interface and returns only text content.
        """

        if top_k <= 0:
            return []

        if not query or not query.strip():
            return []

        try:
            semantic_results = (
                self.embedding_retriever.retrieve(
                    query,
                    top_k=top_k,
                )
            )

        except Exception as error:
            print(
                "[Hybrid Retriever Warning] "
                "Embedding retrieval failed: "
                f"{type(error).__name__}: {error}"
            )

            return self.keyword_retriever.retrieve(
                query,
                top_k=top_k,
            )

        keyword_results = (
            self.keyword_retriever.retrieve(
                query,
                top_k=top_k,
            )
        )

        if not semantic_results:
            return keyword_results

        if not keyword_results:
            return semantic_results

        return self.reciprocal_rank_fusion(
            [
                semantic_results,
                keyword_results,
            ],
            top_k=top_k,
        )

    def retrieve_chunks(
        self,
        query: str,
        top_k: int = 3,
    ) -> list[dict]:
        """
        Retrieve knowledge chunks using semantic and
        keyword retrieval.

        Semantic results provide chunk metadata.
        Keyword results provide lexical matches.

        RRF combines both sources.
        """

        if top_k <= 0:
            return []

        if not query or not query.strip():
            return []

        try:
            semantic_chunks = (
                self.embedding_retriever.retrieve_chunks(
                    query,
                    top_k=top_k,
                )
            )

        except Exception as error:
            print(
                "[Hybrid Retriever Warning] "
                "Chunk embedding retrieval failed: "
                f"{type(error).__name__}: {error}"
            )

            keyword_results = (
                self.keyword_retriever.retrieve(
                    query,
                    top_k=top_k,
                )
            )

            return [
                {
                    "chunk_id": None,
                    "document_id": None,
                    "topic": None,
                    "title": None,
                    "content": content,
                    "similarity": None,
                }
                for content in keyword_results
            ]

        keyword_results = (
            self.keyword_retriever.retrieve(
                query,
                top_k=top_k,
            )
        )

        if not semantic_chunks:
            return [
                {
                    "chunk_id": None,
                    "document_id": None,
                    "topic": None,
                    "title": None,
                    "content": content,
                    "similarity": None,
                }
                for content in keyword_results
            ]

        if not keyword_results:
            return semantic_chunks

        # Build content → metadata mapping for
        # semantic chunks.
        semantic_by_content = {
            chunk["content"]: chunk
            for chunk in semantic_chunks
        }

        semantic_results = [
            chunk["content"]
            for chunk in semantic_chunks
        ]

        fused_results = self.reciprocal_rank_fusion(
            [
                semantic_results,
                keyword_results,
            ],
            top_k=top_k,
        )

        results = []

        for content in fused_results:
            if content in semantic_by_content:
                results.append(
                    semantic_by_content[content]
                )

            else:
                results.append(
                    {
                        "chunk_id": None,
                        "document_id": None,
                        "topic": None,
                        "title": None,
                        "content": content,
                        "similarity": None,
                    }
                )

        return results