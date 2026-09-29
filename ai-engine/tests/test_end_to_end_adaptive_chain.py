import sys
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1]),
)

from adaptive_loop import AdaptiveLoop
from planner import AdaptivePlanner
from schemas import Finding, PlannerInput, PlannerDecision

def test_end_to_end_adaptive_chain(monkeypatch):
    """
    Verify the Person 3 adaptive chain:

    permission_test
        ↓
    sandbox finding
        ↓
    RAG retrieval
        ↓
    adaptive planner
        ↓
    tool_access_test
        ↓
    sandbox finding
    """

    planner = AdaptivePlanner()

    planner_input = PlannerInput(
        available_tests=[
            "permission_test",
            "tool_access_test",
            "memory_access_test",
        ]
    )

    executed_tests = []

    def fake_llm_response(prompt):
        if "permission_test" not in executed_tests:
            return {
                "selected_test": "permission_test",
                "reason": "Start with permission boundary testing.",
                "priority": 0.9,
                "confidence": 0.9,
            }

        return {
            "selected_test": "tool_access_test",
            "reason": "Investigate tool access after permission finding.",
            "priority": 0.9,
            "confidence": 0.9,
        }

    def fake_execute(decision, experiment_id):
        executed_tests.append(decision.selected_test)

        if decision.selected_test == "permission_test":
            return {
                "status": "completed",
                "test": "permission_test",
                "finding": "weak_permission_control",
                "severity": "high",
                "evidence": (
                    "Permission boundary allowed unauthorized "
                    "access."
                ),
                "confidence": 1.0,
            }

        if decision.selected_test == "tool_access_test":
            return {
                "status": "completed",
                "test": "tool_access_test",
                "finding": "unsafe_tool_access",
                "severity": "high",
                "evidence": (
                    "Tool access was allowed without sufficient "
                    "authorization."
                ),
                "confidence": 1.0,
            }

        raise AssertionError(
            f"Unexpected test executed: "
            f"{decision.selected_test}"
        )

    monkeypatch.setattr(
        planner.llm_client,
        "generate_json",
        fake_llm_response,
    )

    monkeypatch.setattr(
        "adaptive_loop.execute_planned_test",
        fake_execute,
    )

    loop = AdaptiveLoop(planner=planner)

    findings = loop.run(
        planner_input=planner_input,
        experiment_id="integration-exp-001",
        max_tests=2,
    )

    assert executed_tests == [
        "permission_test",
        "tool_access_test",
    ]

    assert len(findings) == 2

    assert findings[0].finding == "weak_permission_control"
    assert findings[0].confidence == 1.0

    assert findings[1].finding == "unsafe_tool_access"
    assert findings[1].confidence == 1.0

    assert planner_input.previous_tests == [
        "permission_test",
        "tool_access_test",
    ]

    assert len(planner_input.findings) == 2

    assert planner_input.findings[0].finding == (
        "weak_permission_control"
    )

    assert planner_input.findings[1].finding == (
        "unsafe_tool_access"
    )

    assert planner_input.retrieved_knowledge


def test_day11_adaptive_chain_records_test_sequence():
    planner = AdaptivePlanner()

    planner_input = PlannerInput(
        findings=[],
        previous_tests=[],
        available_tests=[
            "permission_test",
            "tool_access_test",
            "memory_access_test",
        ],
        retrieved_knowledge=[],
        chain_state={
            "experiment_id": "DAY11_SEQUENCE",
            "step": 1,
        },
    )

    decisions = [
        PlannerDecision(
            selected_test="permission_test",
            reason="Initial permission assessment.",
            priority=0.9,
            confidence=0.9,
        ),
        PlannerDecision(
            selected_test="tool_access_test",
            reason="Follow up on the permission finding.",
            priority=0.9,
            confidence=0.9,
        ),
        PlannerDecision(
            selected_test="memory_access_test",
            reason="Follow up on the tool-access finding.",
            priority=0.9,
            confidence=0.9,
        ),
    ]

    class RecordingPlanner:
        def __init__(self):
            self.index = 0
            self.selected_tests = []

        def plan(self, planner_input):
            decision = decisions[self.index]
            self.index += 1
            self.selected_tests.append(
                decision.selected_test
            )
            return decision

    recording_planner = RecordingPlanner()

    loop = AdaptiveLoop(
        planner=recording_planner
    )

    findings = loop.run(
        planner_input=planner_input,
        experiment_id="DAY11_SEQUENCE",
        max_tests=3,
    )

    assert len(findings) == 3

    assert recording_planner.selected_tests == [
        "permission_test",
        "tool_access_test",
        "memory_access_test",
    ]

    assert planner_input.previous_tests == [
        "permission_test",
        "tool_access_test",
        "memory_access_test",
    ]


def test_day11_adaptive_chain_records_findings_in_order():
    planner_input = PlannerInput(
        findings=[],
        previous_tests=[],
        available_tests=[
            "permission_test",
            "tool_access_test",
            "memory_access_test",
        ],
        retrieved_knowledge=[],
        chain_state={
            "experiment_id": "DAY11_FINDINGS",
        },
    )

    decisions = [
        PlannerDecision(
            selected_test="permission_test",
            reason="Initial permission assessment.",
            priority=0.9,
            confidence=0.9,
        ),
        PlannerDecision(
            selected_test="tool_access_test",
            reason="Follow up on permission weakness.",
            priority=0.9,
            confidence=0.9,
        ),
        PlannerDecision(
            selected_test="memory_access_test",
            reason="Follow up on unsafe tool access.",
            priority=0.9,
            confidence=0.9,
        ),
    ]

    class RecordingPlanner:
        def __init__(self):
            self.index = 0

        def plan(self, planner_input):
            decision = decisions[self.index]
            self.index += 1
            return decision

    loop = AdaptiveLoop(
        planner=RecordingPlanner()
    )

    findings = loop.run(
        planner_input=planner_input,
        experiment_id="DAY11_FINDINGS",
        max_tests=3,
    )

    assert len(findings) == 3

    assert [
        finding.finding
        for finding in findings
    ] == [
        "weak_permission_control",
        "unsafe_tool_access",
        "memory_validation_weakness",
    ]

    assert [
        finding.severity
        for finding in findings
    ] == [
        "high",
        "high",
        "medium",
    ]

    assert all(
        finding.confidence == 1.0
        for finding in findings
    )

def test_day11_rag_context_changes_with_findings():
    planner = AdaptivePlanner()

    permission_input = PlannerInput(
        findings=[
            Finding(
                finding="weak_permission_control",
                severity="high",
                confidence=1.0,
                evidence="Unauthorized permission access reproduced.",
            )
        ],
        previous_tests=["permission_test"],
        available_tests=[
            "permission_test",
            "tool_access_test",
            "memory_access_test",
        ],
        retrieved_knowledge=[],
        chain_state={"step": 2},
    )

    memory_input = PlannerInput(
        findings=[
            Finding(
                finding="memory_validation_weakness",
                severity="medium",
                confidence=1.0,
                evidence="Untrusted information entered agent memory.",
            )
        ],
        previous_tests=[
            "permission_test",
            "tool_access_test",
        ],
        available_tests=[
            "permission_test",
            "tool_access_test",
            "memory_access_test",
        ],
        retrieved_knowledge=[],
        chain_state={"step": 3},
    )

    permission_query = planner.build_query(
        permission_input
    )

    memory_query = planner.build_query(
        memory_input
    )

    assert "weak_permission_control" in permission_query
    assert "memory_validation_weakness" in memory_query

    assert permission_query != memory_query

    permission_knowledge = planner.retrieve_knowledge(
        permission_input
    )

    memory_knowledge = planner.retrieve_knowledge(
        memory_input
    )

    assert isinstance(permission_knowledge, list)
    assert isinstance(memory_knowledge, list)

def test_day11_retrieved_knowledge_affects_next_test():
    planner = AdaptivePlanner()

    without_rag = PlannerInput(
        findings=[],
        previous_tests=[
            "permission_test",
        ],
        available_tests=[
            "permission_test",
            "tool_access_test",
            "memory_access_test",
        ],
        retrieved_knowledge=[],
        chain_state={"step": 1},
    )

    with_rag = PlannerInput(
        findings=[],
        previous_tests=[
            "permission_test",
        ],
        available_tests=[
            "permission_test",
            "tool_access_test",
            "memory_access_test",
        ],
        retrieved_knowledge=[
            "Sensitive tools require authorization "
            "and proper permission checks before execution."
        ],
        chain_state={"step": 1},
    )

    without_rag_ranked = planner.rank_candidates(
        without_rag
    )

    with_rag_ranked = planner.rank_candidates(
        with_rag
    )

    assert without_rag_ranked
    assert with_rag_ranked

    without_rag_scores = {
        candidate.test_name: score
        for candidate, score in without_rag_ranked
    }

    with_rag_scores = {
        candidate.test_name: score
        for candidate, score in with_rag_ranked
    }

    assert (
        with_rag_scores["tool_access_test"]
        > without_rag_scores["tool_access_test"]
    )

def test_day11_rag_boosts_permission_candidate():
    planner = AdaptivePlanner()

    planner_input = PlannerInput(
        findings=[],
        previous_tests=[],
        available_tests=[
            "permission_test",
            "tool_access_test",
            "memory_access_test",
        ],
        retrieved_knowledge=[
            "Authorization and permission checks "
            "should enforce least privilege."
        ],
        chain_state={"step": 1},
    )

    ranked = planner.rank_candidates(planner_input)

    scores = {
        candidate.test_name: score
        for candidate, score in ranked
    }

    assert scores["permission_test"] > 0.0


def test_day11_rag_boosts_tool_candidate():
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
        retrieved_knowledge=[
            "Sensitive tools must require authorization "
            "before execution."
        ],
        chain_state={"step": 1},
    )

    ranked = planner.rank_candidates(planner_input)

    scores = {
        candidate.test_name: score
        for candidate, score in ranked
    }

    assert scores["tool_access_test"] > 0.0


def test_day11_finding_and_rag_strengthen_same_candidate():
    planner = AdaptivePlanner()

    planner_input = PlannerInput(
        findings=[
            Finding(
                finding="unsafe_tool_access",
                severity="high",
                confidence=1.0,
                evidence="Sensitive tool access bypassed authorization.",
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
            "Sensitive tools require authorization "
            "before execution."
        ],
        chain_state={"step": 1},
    )

    ranked = planner.rank_candidates(planner_input)

    assert ranked

    top_candidate = ranked[0][0]

    assert top_candidate.test_name == "tool_access_test"


def test_day11_planner_preserves_security_test_order():
    planner = AdaptivePlanner()

    planner_input = PlannerInput(
        findings=[
            Finding(
                finding="weak_permission_control",
                severity="high",
                confidence=1.0,
                evidence="Unauthorized permission access reproduced.",
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
            "Sensitive tools require permission "
            "and authorization checks."
        ],
        chain_state={
            "step": 2,
            "experiment_id": "DAY11_ORDER",
        },
    )

    ranked = planner.rank_candidates(planner_input)

    assert ranked

    candidate_names = [
        candidate.test_name
        for candidate, score in ranked
    ]

    assert "permission_test" not in candidate_names
    assert candidate_names[0] == "tool_access_test"

def test_day11_complete_adaptive_experiment_trace():
    planner_input = PlannerInput(
        findings=[],
        previous_tests=[],
        available_tests=[
            "permission_test",
            "tool_access_test",
            "memory_access_test",
        ],
        retrieved_knowledge=[],
        chain_state={
            "experiment_id": "DAY11_COMPLETE",
            "step": 1,
        },
    )

    decisions = [
        PlannerDecision(
            selected_test="permission_test",
            reason="Initial permission assessment.",
            priority=0.9,
            confidence=0.9,
        ),
        PlannerDecision(
            selected_test="tool_access_test",
            reason=(
                "Permission weakness requires "
                "tool access testing."
            ),
            priority=0.9,
            confidence=0.9,
        ),
        PlannerDecision(
            selected_test="memory_access_test",
            reason=(
                "Unsafe tool access requires "
                "memory validation testing."
            ),
            priority=0.9,
            confidence=0.9,
        ),
    ]

    class ExperimentPlanner:
        def __init__(self):
            self.index = 0
            self.trace = []

        def plan(self, planner_input):
            decision = decisions[self.index]

            self.trace.append({
                "step": self.index + 1,
                "test": decision.selected_test,
                "previous_tests": list(
                    planner_input.previous_tests
                ),
                "findings": [
                    finding.finding
                    for finding in planner_input.findings
                ],
            })

            self.index += 1

            return decision

    experiment_planner = ExperimentPlanner()

    loop = AdaptiveLoop(
        planner=experiment_planner
    )

    findings = loop.run(
        planner_input=planner_input,
        experiment_id="DAY11_COMPLETE",
        max_tests=3,
    )

    assert len(findings) == 3

    assert [
        entry["test"]
        for entry in experiment_planner.trace
    ] == [
        "permission_test",
        "tool_access_test",
        "memory_access_test",
    ]

    assert (
        experiment_planner.trace[0]["findings"]
        == []
    )

    assert (
        experiment_planner.trace[1]["findings"]
        == ["weak_permission_control"]
    )

    assert (
        experiment_planner.trace[2]["findings"]
        == [
            "weak_permission_control",
            "unsafe_tool_access",
        ]
    )

    assert [
        finding.finding
        for finding in findings
    ] == [
        "weak_permission_control",
        "unsafe_tool_access",
        "memory_validation_weakness",
    ]

    assert [
        finding.severity
        for finding in findings
    ] == [
        "high",
        "high",
        "medium",
    ]

    assert all(
        finding.confidence == 1.0
        for finding in findings
    )
