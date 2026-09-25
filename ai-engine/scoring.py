from dataclasses import dataclass


@dataclass
class CandidateMetadata:
    test_name: str
    relevance: float
    severity: float
    confidence: float
    expected_information_gain: float
    testing_cost: float


class CandidateScorer:
    def score(
        self,
        relevance: float,
        severity: float,
        confidence: float,
        information_gain: float,
        testing_cost: float,
    ) -> float:
        values = [
            relevance,
            severity,
            confidence,
            information_gain,
            testing_cost,
        ]

        if any(value < 0.0 or value > 1.0 for value in values):
            raise ValueError(
                "All scoring values must be between 0.0 and 1.0."
            )

        score = (
            0.25 * relevance
            + 0.25 * severity
            + 0.20 * confidence
            + 0.20 * information_gain
            + 0.10 * (1.0 - testing_cost)
        )

        return round(score, 4)

    def score_candidate(
        self,
        candidate: CandidateMetadata,
    ) -> float:
        return self.score(
            relevance=candidate.relevance,
            severity=candidate.severity,
            confidence=candidate.confidence,
            information_gain=candidate.expected_information_gain,
            testing_cost=candidate.testing_cost,
        )

    def rank_candidates(
        self,
        candidates: list[CandidateMetadata],
    ) -> list[tuple[CandidateMetadata, float]]:
        scored_candidates = [
            (candidate, self.score_candidate(candidate))
            for candidate in candidates
        ]

        scored_candidates.sort(
            key=lambda item: (-item[1], item[0].test_name)
        )

        return scored_candidates