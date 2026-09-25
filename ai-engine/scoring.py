from dataclasses import dataclass


@dataclass
class CandidateMetadata:
    """
    Metadata describing an allowed sandbox test.
    """

    test_name: str
    relevance: float
    expected_information_gain: float
    testing_cost: float


class CandidateScorer:
    """
    Deterministic scoring for allowed sandbox tests.

    All feature values must be between 0.0 and 1.0.
    """

    def score(
        self,
        relevance: float,
        severity: float,
        confidence: float,
        information_gain: float,
        testing_cost: float
    ) -> float:
        values = [
            relevance,
            severity,
            confidence,
            information_gain,
            testing_cost
        ]

        if any(
            value < 0.0 or value > 1.0
            for value in values
        ):
            raise ValueError(
                "All scoring values must be "
                "between 0.0 and 1.0."
            )

        score = (
            0.25 * relevance
            + 0.25 * severity
            + 0.20 * confidence
            + 0.20 * information_gain
            + 0.10 * (1.0 - testing_cost)
        )

        return round(score, 4)