import sys
from pathlib import Path

AI_ENGINE_DIR = Path(__file__).resolve().parents[1]

if str(AI_ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(AI_ENGINE_DIR))

from mitigation_selector import MitigationSelector
from mitigation_schemas import MitigationSelectorInput
from mitigation_reasoning import MitigationReasoning
from mitigation_experiment_logger import MitigationExperimentLogger


APPROVED_CONTROLS = {
    "authorization_gate",
    "tool_allowlist",
    "memory_validation",
}


EXPERIMENTS = [
    {
        "finding": "weak_permission_control",
        "severity": "high",
        "evidence": (
            "Permission was DENIED, but the protected "
            "operation was still executed."
        ),
        "attack_chain": [
            "permission_test",
            "protected_operation",
        ],
        "expected_control": "authorization_gate",
    },
    {
        "finding": "unsafe_tool_access",
        "severity": "high",
        "evidence": (
            "A restricted tool was exposed and could be "
            "invoked without being present in the approved allowlist."
        ),
        "attack_chain": [
            "tool_access_test",
            "restricted_tool_execution",
        ],
        "expected_control": "tool_allowlist",
    },
    {
        "finding": "memory_validation_weakness",
        "severity": "high",
        "evidence": (
            "Untrusted memory content was accepted as trusted "
            "agent state without validation."
        ),
        "attack_chain": [
            "memory_injection_test",
            "untrusted_memory_acceptance",
        ],
        "expected_control": "memory_validation",
    },
]


def run_experiment(selector, experiment):
    request = MitigationSelectorInput(
        findings=[
            {
                "finding": experiment["finding"],
                "severity": experiment["severity"],
                "evidence": experiment["evidence"],
                "confidence": 1.0,
            }
        ],
        attack_chain=experiment["attack_chain"],
        available_controls=list(APPROVED_CONTROLS),
    )

    decision = selector.select(request)

    metrics = selector.last_metrics.copy()

    return request, decision, metrics


def main():
    print("=" * 70)
    print("AGENTCHAIN PHASE 2")
    print("PERSON 3 - MITIGATION EXPERIMENT + METRICS")
    print("=" * 70)

    selector = MitigationSelector()
    reasoning = MitigationReasoning()

    logger = MitigationExperimentLogger(
        log_path="logs/mitigation_experiments.jsonl"
    )

    total = len(EXPERIMENTS)

    final_correct = 0
    llm_successes = 0
    fallback_cases = 0
    llm_direct_correct = 0
    llm_decision_count = 0

    total_llm_time = 0.0
    total_rag_time = 0.0
    total_execution_time = 0.0

    for index, experiment in enumerate(EXPERIMENTS, start=1):

        print()
        print("-" * 70)
        print(f"EXPERIMENT {index}/{total}")
        print("-" * 70)

        print(f"Finding:          {experiment['finding']}")
        print(f"Expected control: {experiment['expected_control']}")

        request, decision, metrics = run_experiment(
            selector,
            experiment,
        )

        selected = decision.selected_control

        final_is_correct = (
            selected == experiment["expected_control"]
        )

        llm_success = metrics.get(
            "llm_success",
            False,
        )

        fallback_used = metrics.get(
            "fallback_used",
            False,
        )

        if final_is_correct:
            final_correct += 1

        if llm_success:
            llm_successes += 1
            llm_decision_count += 1

            if selected == experiment["expected_control"]:
                llm_direct_correct += 1

        if fallback_used:
            fallback_cases += 1

        total_llm_time += metrics.get(
            "llm_time_seconds",
            0.0,
        )

        total_rag_time += metrics.get(
            "rag_time_seconds",
            0.0,
        )

        total_execution_time += metrics.get(
            "total_time_seconds",
            0.0,
        )

        result = "PASS" if final_is_correct else "FAIL"

        print(f"Selected control: {selected}")
        print(f"Confidence:       {decision.confidence}")
        print(f"Result:           {result}")

        print()
        print("LLM/RAG metrics:")
        print(f"  LLM called:       {metrics.get('llm_called')}")
        print(f"  LLM success:      {llm_success}")
        print(f"  Fallback used:    {fallback_used}")
        print(
            f"  RAG time:         "
            f"{metrics.get('rag_time_seconds', 0.0):.6f}s"
        )
        print(
            f"  LLM time:         "
            f"{metrics.get('llm_time_seconds', 0.0):.6f}s"
        )
        print(
            f"  Total time:       "
            f"{metrics.get('total_time_seconds', 0.0):.6f}s"
        )
        print(
            f"  Retrieved docs:   "
            f"{metrics.get('retrieved_documents')}"
        )

        if metrics.get("llm_error"):
            print(
                f"  LLM error:        "
                f"{metrics['llm_error']}"
            )

        # Build the structured reasoning record.
        finding_data = request.findings[0]

        reasoning_record = reasoning.build_record(
            finding=finding_data.finding,
            severity=finding_data.severity,
            evidence=finding_data.evidence,
            attack_chain=request.attack_chain,
            selected_control=decision.selected_control,
            reason=decision.reason,
            priority=decision.priority,
            confidence=decision.confidence,
            retrieved_knowledge=request.retrieved_knowledge,
            llm_used=metrics.get("llm_called", False),
            fallback_used=metrics.get("fallback_used", False),
        )

        # Add experiment/evaluation metrics.
        reasoning_record.update(
            {
                "expected_control": experiment["expected_control"],
                "final_selection_correct": final_is_correct,
                "llm_success": llm_success,
                "llm_direct_selection_correct": (
                    llm_success
                    and selected == experiment["expected_control"]
                ),
                "metrics": metrics,
            }
        )

        logger.log(reasoning_record)

    final_accuracy = final_correct / total

    llm_success_rate = (
        llm_successes / total
        if total
        else 0.0
    )

    fallback_rate = (
        fallback_cases / total
        if total
        else 0.0
    )

    llm_direct_accuracy = (
        llm_direct_correct / llm_decision_count
        if llm_decision_count
        else 0.0
    )

    average_llm_time = (
        total_llm_time / total
        if total
        else 0.0
    )

    average_rag_time = (
        total_rag_time / total
        if total
        else 0.0
    )

    average_total_time = (
        total_execution_time / total
        if total
        else 0.0
    )

    print()
    print("=" * 70)
    print("EXPERIMENT SUMMARY")
    print("=" * 70)

    print(f"Total experiments:           {total}")
    print(
        f"Final correct selections:    "
        f"{final_correct}/{total}"
    )
    print(
        f"Final selection accuracy:    "
        f"{final_accuracy:.2%}"
    )

    print()
    print("LLM METRICS")
    print("-" * 70)

    print(
        f"LLM successful decisions:    "
        f"{llm_successes}/{total}"
    )

    print(
        f"LLM success rate:            "
        f"{llm_success_rate:.2%}"
    )

    print(
        f"LLM direct correct:           "
        f"{llm_direct_correct}/{llm_decision_count}"
    )

    print(
        f"LLM direct accuracy:          "
        f"{llm_direct_accuracy:.2%}"
    )

    print(
        f"Fallback cases:              "
        f"{fallback_cases}/{total}"
    )

    print(
        f"Fallback rate:               "
        f"{fallback_rate:.2%}"
    )

    print()
    print("TIMING")
    print("-" * 70)

    print(
        f"Average RAG time:            "
        f"{average_rag_time:.6f}s"
    )

    print(
        f"Average LLM time:            "
        f"{average_llm_time:.6f}s"
    )

    print(
        f"Average total selector time: "
        f"{average_total_time:.6f}s"
    )

    print()
    print("=" * 70)

    if final_correct == total:
        print("FINAL RESULT: PASS")
    else:
        print("FINAL RESULT: REVIEW")

    print()
    print(
        "Experiment records written to:"
    )
    print(
        "logs/mitigation_experiments.jsonl"
    )


if __name__ == "__main__":
    main()