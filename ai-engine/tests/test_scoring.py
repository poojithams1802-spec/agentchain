import pytest

from scoring import CandidateScorer


def test_high_quality_candidate_gets_high_score():
    scorer = CandidateScorer()

    score = scorer.score(
        relevance=1.0,
        severity=1.0,
        confidence=1.0,
        information_gain=1.0,
        testing_cost=0.0
    )

    assert score == 1.0


def test_low_quality_candidate_gets_lower_score():
    scorer = CandidateScorer()

    score = scorer.score(
        relevance=0.0,
        severity=0.0,
        confidence=0.0,
        information_gain=0.0,
        testing_cost=1.0
    )

    assert score == 0.0


def test_expensive_test_has_lower_score():
    scorer = CandidateScorer()

    cheap_score = scorer.score(
        relevance=0.8,
        severity=0.8,
        confidence=0.8,
        information_gain=0.8,
        testing_cost=0.1
    )

    expensive_score = scorer.score(
        relevance=0.8,
        severity=0.8,
        confidence=0.8,
        information_gain=0.8,
        testing_cost=0.9
    )

    assert cheap_score > expensive_score


def test_invalid_scoring_value_is_rejected():
    scorer = CandidateScorer()

    with pytest.raises(ValueError):
        scorer.score(
            relevance=1.2,
            severity=0.5,
            confidence=0.5,
            information_gain=0.5,
            testing_cost=0.5
        )


def test_score_is_between_zero_and_one():
    scorer = CandidateScorer()

    score = scorer.score(
        relevance=0.7,
        severity=0.8,
        confidence=0.9,
        information_gain=0.6,
        testing_cost=0.2
    )

    assert 0.0 <= score <= 1.0