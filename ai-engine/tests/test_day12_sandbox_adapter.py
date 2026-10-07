from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("GEMINI_API_KEY", "test-key")

AI_ENGINE_DIR = Path(__file__).resolve().parents[1]
if str(AI_ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(AI_ENGINE_DIR))

from sandbox_adapter import execute_planned_test
from schemas import PlannerDecision


EXPECTED = {
    "permission_test": "weak_permission_control",
    "tool_access_test": "unsafe_tool_access",
    "memory_access_test": "memory_validation_weakness",
}


def test_p4_sandbox_adapter_executes_all_phase2_tests():
    for test_name, expected_finding in EXPECTED.items():
        decision = PlannerDecision(
            selected_test=test_name,
            reason="Day 12 P4 adapter smoke test.",
            priority=1.0,
            confidence=1.0,
        )

        result = execute_planned_test(
            decision,
            "DAY12-ADAPTER-SMOKE",
        )

        assert result["status"] == "completed"
        assert result["test"] == test_name
        assert result["finding"] == expected_finding
        assert result["confidence"] == 1.0
        assert "evidence" in result


def test_p4_sandbox_adapter_keeps_extra_execution_metadata():
    decision = PlannerDecision(
        selected_test="permission_test",
        reason="Day 12 metadata compatibility test.",
        priority=1.0,
        confidence=1.0,
    )

    result = execute_planned_test(
        decision,
        "DAY12-ADAPTER-METADATA",
    )

    # P4 Day 5 may return execution-cost metadata. The adapter must
    # preserve additional response fields rather than stripping them.
    assert isinstance(result, dict)
    assert result["status"] == "completed"
    assert result["test"] == "permission_test"
