
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = ROOT / "results" / "phase3_ablation_gemini_20261011.json"
OUTPUT_JSON = ROOT / "results" / "phase3_ablation_evaluation_20261011.json"
OUTPUT_MD = ROOT / "results" / "phase3_ablation_evaluation_20261011.md"

EXPECTED_CONFIGS = {"A", "B", "C", "D"}
EXPECTED_TESTS = 3


def evaluate_experiment(raw):
    config = raw.get("configuration", {})
    config_id = config.get("config_id", "unknown")
    name = config.get("name", "unknown")

    selected_count = raw.get("tests_selected", 0)
    requested_count = raw.get("tests_requested", EXPECTED_TESTS)
    status = raw.get("status", "unknown")

    fallback_count = raw.get("fallback_decisions")
    if fallback_count is None:
        fallback_count = (
            "unknown" if raw.get("fallback_used") else 0
        )

    non_fallback_count = raw.get("non_fallback_decisions", "unknown")
    llm_calls = raw.get("llm_calls", "unknown")

    accuracy = raw.get("selection_accuracy")
    total_time = raw.get("total_time_seconds")
    planner_time = raw.get("planner_time_seconds")

    # Strict eligibility: all requested tests selected, no fallback,
    # and at least one confirmed non-fallback decision.
    comparison_eligible = (
        status == "completed"
        and selected_count == EXPECTED_TESTS
        and fallback_count == 0
        and isinstance(non_fallback_count, int)
        and non_fallback_count > 0
    )

    return {
        "config_id": config_id,
        "name": name,
        "use_rag": config.get("use_rag"),
        "use_chain_context": config.get("use_chain_context"),
        "experiment_id": raw.get("experiment_id"),
        "status": status,
        "tests_requested": requested_count,
        "tests_selected": selected_count,
        "llm_calls": llm_calls,
        "fallback_used": raw.get("fallback_used"),
        "fallback_decisions": fallback_count,
        "non_fallback_decisions": non_fallback_count,
        "reported_selection_accuracy": accuracy,
        "execution_success_rate": raw.get("execution_success_rate"),
        "planner_time_seconds": planner_time,
        "total_time_seconds": total_time,
        "comparison_eligible": comparison_eligible,
        "accuracy_independently_validated": False,
        "comparison_note": (
            "No fallback reported and all tests selected; independent "
            "ground-truth validation is still required."
            if comparison_eligible
            else "Not eligible for a clean comparison: incomplete run, "
            "fallback use, or insufficient decision evidence."
        ),
    }


def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Missing input file: {INPUT_FILE}")

    data = json.loads(INPUT_FILE.read_text(encoding="utf-8"))
    raw_results = data.get("results", [])

    if not isinstance(raw_results, list):
        raise ValueError("Expected the JSON 'results' field to be a list.")

    evaluated = [evaluate_experiment(item) for item in raw_results]

    by_config = {}
    for item in evaluated:
        by_config[item["config_id"]] = item

    missing = sorted(EXPECTED_CONFIGS - set(by_config))
    ordered = [
        by_config[key]
        for key in sorted(by_config)
    ]

    all_eligible = (
        not missing
        and len(ordered) == 4
        and all(item["comparison_eligible"] for item in ordered)
    )

    report = {
        "source_file": INPUT_FILE.name,
        "found_configurations": sorted(by_config),
        "missing_configurations": missing,
        "all_configurations_present": not missing,
        "performance_comparison_valid": all_eligible,
        "accuracy_warning": (
            "Selection accuracy is copied from the original result. "
            "This script does not independently validate ground truth. "
            "The expected sequence must not merely duplicate candidate order."
        ),
        "experiments": ordered,
    }

    OUTPUT_JSON.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    lines = [
        "# Phase 3 Ablation Evaluation",
        "",
        f"Source: `{INPUT_FILE.name}`",
        "",
        f"All configurations present: **{not missing}**",
        f"Performance comparison valid: **{all_eligible}**",
        "",
        "| Config | Status | Tests | LLM calls | Fallbacks | Accuracy (reported) | Eligible |",
        "|---|---|---:|---:|---:|---:|---|",
    ]

    for item in ordered:
        accuracy = item["reported_selection_accuracy"]
        accuracy_text = "N/A" if accuracy is None else str(accuracy)

        lines.append(
            f"| {item['config_id']} — {item['name']} "
            f"| {item['status']} "
            f"| {item['tests_selected']}/{item['tests_requested']} "
            f"| {item['llm_calls']} "
            f"| {item['fallback_decisions']} "
            f"| {accuracy_text} "
            f"| {'Yes' if item['comparison_eligible'] else 'No'} |"
        )

    lines += [
        "",
        "## Interpretation",
        "",
        "- A completed run is not automatically a valid comparison.",
        "- Fallback decisions are reported separately from LLM calls.",
        "- Reported selection accuracy is not independently validated.",
        "- Do not claim RAG or chain-context improvements from ineligible runs.",
        "",
    ]

    OUTPUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print("Configurations found:", ", ".join(sorted(by_config)))
    print("Missing configurations:", missing or "none")
    print("Performance comparison valid:", all_eligible)

    for item in ordered:
        print(
            f"{item['config_id']} ({item['name']}): "
            f"status={item['status']}, "
            f"tests={item['tests_selected']}/{item['tests_requested']}, "
            f"fallbacks={item['fallback_decisions']}, "
            f"accuracy={item['reported_selection_accuracy']}, "
            f"eligible={item['comparison_eligible']}"
        )

    print("\nSaved evaluation files:")
    print(OUTPUT_JSON)
    print(OUTPUT_MD)


if __name__ == "__main__":
    main()
