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


def test_planner_ranks_candidates_using_candidate_scorer():
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

    ranked = planner.scorer.rank_candidates(candidates)

    assert ranked

    ranked_names = [
        candidate.test_name
        for candidate, score in ranked
    ]

    assert "permission_test" not in ranked_names
    assert "tool_access_test" in ranked_names
    assert "memory_access_test" in ranked_names

    assert ranked[0][1] >= ranked[-1][1]

def test_planner_rank_candidates_returns_sorted_results():
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

    ranked = planner.rank_candidates(
        planner_input
    )

    assert len(ranked) == 2

    scores = [
        score
        for candidate, score in ranked
    ]

    assert scores == sorted(
        scores,
        reverse=True,
    )

    assert all(
        candidate.test_name != "permission_test"
        for candidate, score in ranked
    )

def test_ranked_candidates_contain_metadata():
    from planner import AdaptivePlanner
    from schemas import PlannerInput

    planner = AdaptivePlanner()

    planner_input = PlannerInput(
        findings=[],
        previous_tests=[],
        available_tests=[
            "permission_test",
            "tool_access_test",
        ],
    )

    ranked = planner.rank_candidates(
        planner_input
    )

    assert len(ranked) == 2

    for candidate, score in ranked:
        assert isinstance(
            candidate.test_name,
            str,
        )

        assert 0.0 <= candidate.relevance <= 1.0
        assert 0.0 <= candidate.severity <= 1.0
        assert 0.0 <= candidate.confidence <= 1.0
        assert (
            0.0
            <= candidate.expected_information_gain
            <= 1.0
        )
        assert 0.0 <= candidate.testing_cost <= 1.0

        assert 0.0 <= score <= 1.0


def test_rank_candidates_excludes_previous_tests():
    from planner import AdaptivePlanner
    from schemas import PlannerInput

    planner = AdaptivePlanner()

    planner_input = PlannerInput(
        findings=[],
        previous_tests=[
            "permission_test",
            "tool_access_test",
        ],
        available_tests=[
            "permission_test",
            "tool_access_test",
            "memory_access_test",
        ],
    )

    ranked = planner.rank_candidates(
        planner_input
    )

    assert len(ranked) == 1

    assert (
        ranked[0][0].test_name
        == "memory_access_test"
    )

def test_rank_candidates_returns_empty_when_all_tests_executed():
    from planner import AdaptivePlanner
    from schemas import PlannerInput

    planner = AdaptivePlanner()

    planner_input = PlannerInput(
        findings=[],
        previous_tests=[
            "permission_test",
        ],
        available_tests=[
            "permission_test",
        ],
    )

    ranked = planner.rank_candidates(
        planner_input
    )

    assert ranked == []

def test_build_candidate_context_contains_ranked_scores():
    from planner import AdaptivePlanner
    from schemas import PlannerInput

    planner = AdaptivePlanner()

    planner_input = PlannerInput(
        findings=[],
        previous_tests=[],
        available_tests=[
            "permission_test",
            "tool_access_test",
            "memory_access_test",
        ],
    )

    context = planner.build_candidate_context(
        planner_input
    )

    assert len(context) == 3

    for candidate in context:
        assert "test_name" in candidate
        assert "score" in candidate
        assert "relevance" in candidate
        assert "severity" in candidate
        assert "confidence" in candidate
        assert "expected_information_gain" in candidate
        assert "testing_cost" in candidate

        assert 0.0 <= candidate["score"] <= 1.0


def test_build_candidate_context_excludes_previous_tests():
    from planner import AdaptivePlanner
    from schemas import PlannerInput

    planner = AdaptivePlanner()

    planner_input = PlannerInput(
        findings=[],
        previous_tests=[
            "permission_test",
        ],
        available_tests=[
            "permission_test",
            "tool_access_test",
            "memory_access_test",
        ],
    )

    context = planner.build_candidate_context(
        planner_input
    )

    test_names = [
        candidate["test_name"]
        for candidate in context
    ]

    assert "permission_test" not in test_names
    assert "tool_access_test" in test_names
    assert "memory_access_test" in test_names


def test_create_prompt_includes_candidate_scores():
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
        previous_tests=[
            "permission_test",
        ],
        available_tests=[
            "permission_test",
            "tool_access_test",
            "memory_access_test",
        ],
        retrieved_knowledge=[
            "Permission controls should prevent unauthorized tool access."
        ],
    )

    prompt = planner.create_prompt(
        planner_input
    )

    assert "candidate_scores" in prompt
    assert "tool_access_test" in prompt
    assert "memory_access_test" in prompt

def test_create_prompt_includes_candidate_scoring_instructions():
    from planner import AdaptivePlanner
    from schemas import PlannerInput

    planner = AdaptivePlanner()

    planner_input = PlannerInput(
        findings=[],
        previous_tests=[],
        available_tests=[
            "permission_test",
            "tool_access_test",
            "memory_access_test",
        ],
    )

    prompt = planner.create_prompt(
        planner_input
    )

    assert "Candidate scores" in prompt
    assert "Relevance" in prompt
    assert "Severity" in prompt
    assert "Confidence" in prompt
    assert "Expected information gain" in prompt
    assert "Testing cost" in prompt


def test_select_from_candidates_preserves_valid_llm_decision():
    from planner import AdaptivePlanner
    from schemas import PlannerDecision, PlannerInput

    planner = AdaptivePlanner()

    planner_input = PlannerInput(
        findings=[],
        previous_tests=[],
        available_tests=[
            "permission_test",
            "tool_access_test",
            "memory_access_test",
        ],
    )

    decision = PlannerDecision(
        selected_test="tool_access_test",
        reason="Tool access is relevant.",
        priority=0.8,
        confidence=0.9,
    )

    selected = planner.select_from_candidates(
        planner_input,
        decision,
    )

    assert selected.selected_test == "tool_access_test"
    assert selected.reason == "Tool access is relevant."
    assert selected.priority == 0.8
    assert selected.confidence == 0.9


def test_select_from_candidates_replaces_invalid_llm_decision():
    from planner import AdaptivePlanner
    from schemas import PlannerDecision, PlannerInput

    planner = AdaptivePlanner()

    planner_input = PlannerInput(
        findings=[],
        previous_tests=[
            "permission_test",
        ],
        available_tests=[
            "permission_test",
            "tool_access_test",
            "memory_access_test",
        ],
    )

    decision = PlannerDecision(
        selected_test="permission_test",
        reason="Invalid previous test selection.",
        priority=0.5,
        confidence=0.5,
    )

    selected = planner.select_from_candidates(
        planner_input,
        decision,
    )

    assert selected.selected_test != "permission_test"

    assert selected.selected_test in [
        "tool_access_test",
        "memory_access_test",
    ]

    assert (
        selected.reason
        == "Selected highest-ranked unexecuted candidate "
        "because the LLM decision was not valid."
    )


def test_select_from_candidates_uses_highest_ranked_candidate():
    from planner import AdaptivePlanner
    from schemas import PlannerDecision, PlannerInput

    planner = AdaptivePlanner()

    planner_input = PlannerInput(
        findings=[],
        previous_tests=[
            "permission_test",
            "tool_access_test",
        ],
        available_tests=[
            "permission_test",
            "tool_access_test",
            "memory_access_test",
        ],
    )

    decision = PlannerDecision(
        selected_test="permission_test",
        reason="Invalid selection.",
        priority=0.2,
        confidence=0.2,
    )

    selected = planner.select_from_candidates(
        planner_input,
        decision,
    )

    assert (
        selected.selected_test
        == "memory_access_test"
    )

def test_select_from_candidates_handles_no_candidates():
    from planner import AdaptivePlanner
    from schemas import PlannerDecision, PlannerInput

    planner = AdaptivePlanner()

    planner_input = PlannerInput(
        findings=[],
        previous_tests=[
            "permission_test",
        ],
        available_tests=[
            "permission_test",
        ],
    )

    decision = PlannerDecision(
        selected_test="permission_test",
        reason="Existing decision.",
        priority=0.5,
        confidence=0.5,
    )

    selected = planner.select_from_candidates(
        planner_input,
        decision,
    )

    assert selected.selected_test == "permission_test"
    assert selected.reason == "Existing decision."


def test_plan_uses_candidate_selection_layer(monkeypatch):
    from planner import AdaptivePlanner
    from schemas import PlannerDecision, PlannerInput

    planner = AdaptivePlanner()

    planner_input = PlannerInput(
        findings=[],
        previous_tests=[],
        available_tests=[
            "permission_test",
            "tool_access_test",
            "memory_access_test",
        ],
    )

    llm_decision = PlannerDecision(
        selected_test="tool_access_test",
        reason="Tool access should be checked.",
        priority=0.8,
        confidence=0.9,
    )

    called = {
        "value": False,
    }

    def fake_select_from_candidates(
        planner_input,
        decision,
    ):
        called["value"] = True
        return decision

    monkeypatch.setattr(
        planner,
        "select_from_candidates",
        fake_select_from_candidates,
    )

    monkeypatch.setattr(
        planner.llm_client,
        "generate_json",
        lambda prompt: {
            "selected_test": "tool_access_test",
            "reason": "Tool access should be checked.",
            "priority": 0.8,
            "confidence": 0.9,
        },
    )

    result = planner.plan(
        planner_input
    )

    assert called["value"] is True
    assert result.selected_test == "tool_access_test"