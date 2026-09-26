from scoring import CandidateMetadata, CandidateScorer


def test_candidate_scorer_ranks_candidates():
    scorer = CandidateScorer()

    candidates = [
        CandidateMetadata(
            test_name="memory_access_test",
            relevance=0.5,
            severity=0.5,
            confidence=0.5,
            expected_information_gain=0.5,
            testing_cost=0.5,
        ),
        CandidateMetadata(
            test_name="tool_access_test",
            relevance=0.9,
            severity=0.9,
            confidence=0.9,
            expected_information_gain=0.9,
            testing_cost=0.2,
        ),
    ]

    ranked = scorer.rank_candidates(candidates)

    assert ranked[0][0].test_name == "tool_access_test"
    assert ranked[0][1] > ranked[1][1]

def test_candidate_metadata_values_are_valid():
    candidates = [
        CandidateMetadata(
            test_name="permission_test",
            relevance=0.8,
            severity=0.9,
            confidence=0.9,
            expected_information_gain=0.8,
            testing_cost=0.2,
        ),
        CandidateMetadata(
            test_name="tool_access_test",
            relevance=0.9,
            severity=0.9,
            confidence=0.9,
            expected_information_gain=0.95,
            testing_cost=0.3,
        ),
    ]

    for candidate in candidates:
        assert 0.0 <= candidate.relevance <= 1.0
        assert 0.0 <= candidate.severity <= 1.0
        assert 0.0 <= candidate.confidence <= 1.0
        assert 0.0 <= candidate.expected_information_gain <= 1.0
        assert 0.0 <= candidate.testing_cost <= 1.0


def test_candidate_builder_creates_metadata_for_unexecuted_tests():
    from planner import AdaptivePlanner
    from schemas import Finding, PlannerInput

    planner = AdaptivePlanner()

    planner_input = PlannerInput(
        findings=[
            Finding(
                finding="weak_permission_control",
                severity="high",
                confidence=1.0,
                evidence="Permission denied but tool was allowed.",
            )
        ],
        previous_tests=["permission_test"],
        available_tests=[
            "permission_test",
            "tool_access_test",
            "memory_access_test",
        ],
    )

    candidates = planner.build_candidates(planner_input)

    candidate_names = [
        candidate.test_name
        for candidate in candidates
    ]

    assert "permission_test" not in candidate_names
    assert "tool_access_test" in candidate_names
    assert "memory_access_test" in candidate_names

    for candidate in candidates:
        assert 0.0 <= candidate.relevance <= 1.0
        assert 0.0 <= candidate.severity <= 1.0
        assert 0.0 <= candidate.confidence <= 1.0
        assert 0.0 <= candidate.expected_information_gain <= 1.0
        assert 0.0 <= candidate.testing_cost <= 1.0