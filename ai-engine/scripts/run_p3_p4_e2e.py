
import sys
import time
import uuid
from collections import Counter
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
        "attack_chain": ["permission_test"],
        "test_name": "permission_test",
        "expected_control": "authorization_gate",
    },
    {
        "finding": "unsafe_tool_access",
        "severity": "high",
        "evidence": (
            "A tool can be accessed without sufficient allowlisting."
        ),
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
# Helpers
# ---------------------------------------------------------

def percentage(count, total):
    return count / total * 100 if total else 0.0


def is_quota_error(error):
    if not error:
        return False

    error_text = str(error).upper()

    return (
        "RESOURCE_EXHAUSTED" in error_text
        or "429" in error_text
        or "QUOTA" in error_text
    )


# ---------------------------------------------------------
# P3 -> P4 E2E runner
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

    llm_error = selector_metrics.get("llm_error")
    rag_error = selector_metrics.get("rag_retrieval_error")

    # -----------------------------------------------------
    # P4 replay/evaluation
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

    if replay_result.get("status") != "completed":
        raise RuntimeError(
            f"P4 replay failed for {scenario['finding']}: "
            f"{replay_result}"
        )

    # -----------------------------------------------------
    # P4 evaluation record
    # -----------------------------------------------------

    record = build_mitigation_experiment_record(
        replay_result,
        mode="adaptive",
        mitigation_selected=True,
        llm_calls=(
            1 if selector_metrics.get("llm_called") else 0
        ),
        fallback_used=bool(
            selector_metrics.get("fallback_used", False)
        ),
    )

    # -----------------------------------------------------
    # P3 evaluation metadata
    # -----------------------------------------------------

    record.update(
        {
            "experiment_id": experiment_id,
            "p3_finding": scenario["finding"],
            "p3_selection_correct": selection_correct,
            "p3_expected_control": scenario["expected_control"],
            "p3_selected_control": selected_control,
            "p3_selection_time_seconds": round(
                selection_time, 6
            ),
            "p4_replay_time_seconds": round(
                replay_time, 6
            ),

            # Full selector metrics remain available.
            "p3_selector_metrics": selector_metrics,

            # Also persist important metrics at top level.
            "rag_retrieval_status": selector_metrics.get(
                "rag_retrieval_status", "unknown"
            ),
            "rag_retrieval_error": rag_error,
            "rag_context_in_prompt": selector_metrics.get(
                "rag_context_in_prompt", False
            ),
            "retrieved_documents": selector_metrics.get(
                "retrieved_documents", 0
            ),
            "llm_called": selector_metrics.get(
                "llm_called", False
            ),
            "llm_success": selector_metrics.get(
                "llm_success", False
            ),
            "llm_error": llm_error,
            "fallback_used": selector_metrics.get(
                "fallback_used", False
            ),
            "llm_quota_error": is_quota_error(llm_error),
        }
    )

    return record


# ---------------------------------------------------------
# Print one scenario
# ---------------------------------------------------------

def print_scenario(record, index):
    print()
    print("-" * 70)
    print(f"SCENARIO {index}: {record.get('p3_finding')}")
    print("-" * 70)

    print(f"Expected control       : {record['p3_expected_control']}")
    print(f"Selected control       : {record['p3_selected_control']}")
    print(f"Selection correct      : {record['p3_selection_correct']}")

    print(f"RAG retrieval status   : {record['rag_retrieval_status']}")
    print(f"Retrieved documents    : {record['retrieved_documents']}")
    print(f"RAG context in prompt  : {record['rag_context_in_prompt']}")

    print(f"LLM called             : {record['llm_called']}")
    print(f"LLM decision successful: {record['llm_success']}")
    print(f"Fallback used          : {record['fallback_used']}")
    print(f"Gemini quota error     : {record['llm_quota_error']}")

    if record.get("rag_retrieval_error"):
        print(f"RAG error              : {record['rag_retrieval_error']}")

    if record.get("llm_error"):
        print(f"LLM error              : {record['llm_error']}")

    print(f"Mitigation applied     : {record.get('mitigation_applied')}")
    print(f"Attack before          : {record.get('attack_success_before')}")
    print(f"Attack after           : {record.get('attack_success_after')}")
    print(f"Chain disrupted        : {record.get('chain_disrupted')}")
    print(f"Residual steps         : {record.get('residual_vulnerable_steps')}")
    print(f"Validation             : {record.get('mitigation_validation')}")
    print(f"Validation rate        : {record.get('validation_rate')}")

    print(
        f"Selection time         : "
        f"{record['p3_selection_time_seconds']:.4f}s"
    )
    print(
        f"Replay time            : "
        f"{record['p4_replay_time_seconds']:.4f}s"
    )


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

def main():
    print("=" * 70)
    print("P3 -> P4 LEVEL-3 END-TO-END MITIGATION TEST")
    print("=" * 70)

    selector = MitigationSelector()

    log_path = AI_ENGINE_DIR / "logs" / "p3_p4_e2e_experiments.jsonl"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger = MitigationExperimentLogger(str(log_path))

    records = []

    for index, scenario in enumerate(SCENARIOS, start=1):
        print()
        print(f"Running scenario {index}/{len(SCENARIOS)}...")

        record = run_scenario(selector, scenario)

        records.append(record)
        logger.log(record)

        print_scenario(record, index)

    # -----------------------------------------------------
    # Aggregate evaluation
    # -----------------------------------------------------

    total = len(records)

    selection_correct = sum(
        bool(record.get("p3_selection_correct"))
        for record in records
    )

    mitigation_applied = sum(
        bool(record.get("mitigation_applied"))
        for record in records
    )

    disrupted = sum(
        bool(record.get("chain_disrupted"))
        for record in records
    )

    validated = sum(
        bool(record.get("mitigation_validation"))
        for record in records
    )

    total_residual_steps = sum(
        len(record.get("residual_vulnerable_steps") or [])
        for record in records
    )

    llm_successes = sum(
        bool(record.get("llm_success"))
        for record in records
    )

    fallback_cases = sum(
        bool(record.get("fallback_used"))
        for record in records
    )

    quota_errors = sum(
        bool(record.get("llm_quota_error"))
        for record in records
    )

    rag_status_counts = Counter(
        record.get("rag_retrieval_status", "unknown")
        for record in records
    )

    # Accuracy among successful LLM decisions only.
    llm_driven_records = [
        record
        for record in records
        if record.get("llm_success")
        and not record.get("fallback_used")
    ]

    llm_driven_correct = sum(
        bool(record.get("p3_selection_correct"))
        for record in llm_driven_records
    )

    llm_driven_total = len(llm_driven_records)

    print()
    print("=" * 70)
    print("P3 -> P4 E2E SUMMARY")
    print("=" * 70)

    print(
        f"Overall control match: {selection_correct}/{total} "
        f"({percentage(selection_correct, total):.2f}%)"
    )
    print(
        f"Mitigation application success: {mitigation_applied}/{total} "
        f"({percentage(mitigation_applied, total):.2f}%)"
    )
    print(
        f"Attack disruption rate: {disrupted}/{total} "
        f"({percentage(disrupted, total):.2f}%)"
    )
    print(
        f"Mitigation validation rate: {validated}/{total} "
        f"({percentage(validated, total):.2f}%)"
    )
    print(f"Residual vulnerable steps: {total_residual_steps}")

    print()
    print("--- LLM versus fallback ---")
    print(f"Successful validated LLM decisions: {llm_successes}/{total}")
    print(f"Deterministic fallback cases       : {fallback_cases}/{total}")
    print(f"Gemini quota errors                : {quota_errors}/{total}")
    print(
        "Accuracy among successful LLM decisions: "
        f"{llm_driven_correct}/{llm_driven_total} "
        f"({percentage(llm_driven_correct, llm_driven_total):.2f}%)"
    )

    print()
    print("--- RAG retrieval status ---")
    for status, count in sorted(rag_status_counts.items()):
        print(f"{status}: {count}/{total}")

    print()
    print("Experiment records:", log_path)
    print("=" * 70)
    print("P3 -> P4 E2E TEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
