import json
import sys
import time
import uuid
from pathlib import Path


# ---------------------------------------------------------
# Make project root importable
# ---------------------------------------------------------

AI_ENGINE_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = AI_ENGINE_DIR.parent

if str(AI_ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(AI_ENGINE_DIR))

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ---------------------------------------------------------
# P3 imports
# ---------------------------------------------------------

from mitigation_selector import MitigationSelector
from mitigation_schemas import (
    MitigationFinding,
    MitigationSelectorInput,
)


# ---------------------------------------------------------
# P4 imports
# ---------------------------------------------------------

from sandbox.mitigation.replay_executor import replay_attack
from sandbox.evaluation.mitigation_evaluation import (
    build_mitigation_experiment_record,
)


# ---------------------------------------------------------
# Experiment logger
# ---------------------------------------------------------

from mitigation_experiment_logger import MitigationExperimentLogger


# ---------------------------------------------------------
# Scenario definitions
# ---------------------------------------------------------

SCENARIOS = [
    {
        "finding": "weak_permission_control",
        "severity": "high",
        "evidence": "Permission boundary is insufficiently enforced.",
        "attack_chain": [
            "permission_test",
        ],
        "test_name": "permission_test",
        "expected_control": "authorization_gate",
    },
    {
        "finding": "unsafe_tool_access",
        "severity": "high",
        "evidence": "A tool can be accessed without sufficient allowlisting.",
        "attack_chain": [
            "permission_test",
            "tool_access_test",
        ],
        "test_name": "tool_access_test",
        "expected_control": "tool_allowlist",
    },
    {
        "finding": "memory_validation_weakness",
        "severity": "high",
        "evidence": "Memory input is insufficiently validated.",
        "attack_chain": [
            "permission_test",
            "tool_access_test",
            "memory_access_test",
        ],
        "test_name": "memory_access_test",
        "expected_control": "memory_validation",
    },
]


# ---------------------------------------------------------
# P3 → P4 E2E runner
# ---------------------------------------------------------

def run_scenario(selector, scenario):
    finding = MitigationFinding(
        finding=scenario["finding"],
        severity=scenario["severity"],
        evidence=scenario["evidence"],
        confidence=1.0,
    )

    request = MitigationSelectorInput(
        findings=[finding],
        attack_chain=scenario["attack_chain"],
        available_controls=[
            "authorization_gate",
            "tool_allowlist",
            "memory_validation",
        ],
        chain_state={"status": "active"},
    )

    # -----------------------------------------------------
    # P3 mitigation selection
    # -----------------------------------------------------

    selection_start = time.perf_counter()

    decision = selector.select(request)

    selection_time = time.perf_counter() - selection_start

    selected_control = decision.selected_control

    selection_correct = (
        selected_control == scenario["expected_control"]
    )

    selector_metrics = dict(
        getattr(selector, "last_metrics", {})
    )

    # -----------------------------------------------------
    # P4 complete replay/evaluation
    # -----------------------------------------------------

    experiment_id = (
        f"P3-P4-E2E-{scenario['finding']}-"
        f"{uuid.uuid4().hex[:8]}"
    )

    replay_start = time.perf_counter()

    replay_result = replay_attack(
        experiment_id=experiment_id,
        test_name=scenario["test_name"],
        control_name=selected_control,
    )

    replay_time = time.perf_counter() - replay_start

    # -----------------------------------------------------
    # Validate P4 boundary result
    # -----------------------------------------------------

    if replay_result.get("status") != "completed":
        raise RuntimeError(
            f"P4 replay failed for {scenario['finding']}: "
            f"{replay_result}"
        )

    # -----------------------------------------------------
    # Use P4 evaluation helper
    # -----------------------------------------------------

    record = build_mitigation_experiment_record(
        replay_result,
        mode="adaptive",
        mitigation_selected=True,
        llm_calls=1 if selector_metrics.get("llm_called") else 0,
        fallback_used=bool(
            selector_metrics.get("fallback_used", False)
        ),
    )

    # -----------------------------------------------------
    # Add P3-specific evaluation metadata
    # -----------------------------------------------------

    record.update(
        {
            "p3_selection_correct": selection_correct,
            "p3_expected_control": scenario["expected_control"],
            "p3_selected_control": selected_control,
            "p3_selection_time_seconds": selection_time,
            "p4_replay_time_seconds": replay_time,
            "p3_selector_metrics": selector_metrics,
        }
    )

    return record, replay_result


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

def main():
    print("=" * 70)
    print("P3 → P4 LEVEL-3 END-TO-END MITIGATION TEST")
    print("=" * 70)

    selector = MitigationSelector()

    logger = MitigationExperimentLogger(
        "logs/p3_p4_e2e_experiments.jsonl"
    )

    records = []

    for index, scenario in enumerate(SCENARIOS, start=1):
        print()
        print("-" * 70)
        print(f"SCENARIO {index}: {scenario['finding']}")
        print("-" * 70)

        record, replay_result = run_scenario(
            selector,
            scenario,
        )

        records.append(record)

        logger.log(record)

        print(
            f"Expected control : "
            f"{record['p3_expected_control']}"
        )

        print(
            f"Selected control : "
            f"{record['p3_selected_control']}"
        )

        print(
            f"Selection correct: "
            f"{record['p3_selection_correct']}"
        )

        print(
            f"Mitigation applied: "
            f"{record['mitigation_applied']}"
        )

        print(
            f"Attack before    : "
            f"{record['attack_success_before']}"
        )

        print(
            f"Attack after     : "
            f"{record['attack_success_after']}"
        )

        print(
            f"Chain disrupted  : "
            f"{record['chain_disrupted']}"
        )

        print(
            f"Residual steps   : "
            f"{record['residual_vulnerable_steps']}"
        )

        print(
            f"Validation       : "
            f"{record['mitigation_validation']}"
        )

        print(
            f"Validation rate  : "
            f"{record['validation_rate']}"
        )

        print(
            f"Selection time   : "
            f"{record['p3_selection_time_seconds']:.4f}s"
        )

        print(
            f"Replay time      : "
            f"{record['p4_replay_time_seconds']:.4f}s"
        )

    # -----------------------------------------------------
    # Aggregate metrics
    # -----------------------------------------------------

    total = len(records)

    selection_correct = sum(
        record["p3_selection_correct"]
        for record in records
    )

    mitigation_applied = sum(
        record["mitigation_applied"]
        for record in records
    )

    disrupted = sum(
        record["chain_disrupted"]
        for record in records
    )

    validated = sum(
        record["mitigation_validation"]
        for record in records
    )

    total_residual_steps = sum(
        len(record["residual_vulnerable_steps"])
        for record in records
    )

    fallback_cases = sum(
        record["fallback_used"]
        for record in records
    )

    print()
    print("=" * 70)
    print("P3 → P4 E2E SUMMARY")
    print("=" * 70)

    print(
        f"Mitigation selection accuracy: "
        f"{selection_correct}/{total} "
        f"({selection_correct / total * 100:.2f}%)"
    )

    print(
        f"Mitigation application success: "
        f"{mitigation_applied}/{total} "
        f"({mitigation_applied / total * 100:.2f}%)"
    )

    print(
        f"Attack disruption rate: "
        f"{disrupted}/{total} "
        f"({disrupted / total * 100:.2f}%)"
    )

    print(
        f"Mitigation validation rate: "
        f"{validated}/{total} "
        f"({validated / total * 100:.2f}%)"
    )

    print(
        f"Residual vulnerable steps: "
        f"{total_residual_steps}"
    )

    print(
        f"Fallback cases: "
        f"{fallback_cases}/{total}"
    )

    print()
    print(
        "E2E experiment log:"
        " logs/p3_p4_e2e_experiments.jsonl"
    )

    print()
    print("=" * 70)
    print("P3 → P4 E2E TEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()