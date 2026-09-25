import pytest

from scoring import CandidateMetadata, CandidateScorer

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


def test_rank_candidates_orders_by_score():
    scorer = CandidateScorer()

    candidates = [
        CandidateMetadata(
            test_name="low_value_test",
            relevance=0.2,
            severity=0.2,
            confidence=0.2,
            expected_information_gain=0.2,
            testing_cost=0.8,
        ),
        CandidateMetadata(
            test_name="high_value_test",
            relevance=1.0,
            severity=1.0,
            confidence=1.0,
            expected_information_gain=1.0,
            testing_cost=0.0,
        ),
    ]

    ranked = scorer.rank_candidates(candidates)

    assert ranked[0][0].test_name == "high_value_test"
    assert ranked[1][0].test_name == "low_value_test"
    assert ranked[0][1] > ranked[1][1]


def test_rank_candidates_returns_scores():
    scorer = CandidateScorer()

    candidate = CandidateMetadata(
        test_name="sample_test",
        relevance=1.0,
        severity=1.0,
        confidence=1.0,
        expected_information_gain=1.0,
        testing_cost=0.0,
    )

    ranked = scorer.rank_candidates([candidate])

    assert len(ranked) == 1
    assert ranked[0][1] == 1.0


def test_rank_candidates_uses_test_name_for_ties():
    scorer = CandidateScorer()

    candidates = [
        CandidateMetadata(
            test_name="z_test",
            relevance=0.5,
            severity=0.5,
            confidence=0.5,
            expected_information_gain=0.5,
            testing_cost=0.5,
        ),
        CandidateMetadata(
            test_name="a_test",
            relevance=0.5,
            severity=0.5,
            confidence=0.5,
            expected_information_gain=0.5,
            testing_cost=0.5,
        ),
    ]

    ranked = scorer.rank_candidates(candidates)

    assert ranked[0][0].test_name == "a_test"
    assert ranked[1][0].test_name == "z_test"

def test_rank_candidates_handles_empty_list():
    scorer = CandidateScorer()

    ranked = scorer.rank_candidates([])

    assert ranked == []