
import sys
import json
from pathlib import Path


# ============================================================
# PATH SETUP
# ============================================================

AI_ENGINE_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = Path(__file__).resolve().parents[2]

for path in (AI_ENGINE_ROOT, PROJECT_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))


# ============================================================
# IMPORT EVALUATION COMPONENTS
# ============================================================

from sandbox.evaluation.adaptive_evaluation import (
    run_adaptive_evaluation,
)
from sandbox.evaluation.static_evaluation import (
    run_static_evaluation,
)
from sandbox.evaluation.comparison import (
    compare_evaluations,
)


# ============================================================
# FILE PATHS
# ============================================================

RESULTS_DIR = AI_ENGINE_ROOT / "results"

# Use the backup experiment that contains execution results.
EXPERIMENT_FILE = RESULTS_DIR / "DAY14_FINAL_backup.json"

VALIDATION_FILE = RESULTS_DIR / "DAY14_FINAL_validation.json"

# Keep the established evaluation output filename.
OUTPUT_FILE = RESULTS_DIR / "DAY14_FINAL_evaluation.json"


# ============================================================
# LOAD JSON
# ============================================================

def load_json(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(
            f"Required file not found: {path}"
        )

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


# ============================================================
# BUILD ADAPTIVE EVALUATION
# ============================================================

def build_adaptive_evaluation(
    experiment: dict,
    validation: dict,
) -> dict:

    experiment_id = experiment["experiment_id"]
    executed_tests = experiment["test_sequence"]
    findings = experiment["finding_sequence"]

    candidate_chains = [executed_tests]

    validated_chains = []

    if validation["status"] == "validated":
        validated_chains.append(executed_tests)

    chain_lengths = [len(executed_tests)]
    validation_rates = [validation["validation_rate"]]

    # Pass recorded sandbox results into the evaluator.
    execution_results = experiment.get("execution_results", [])

    if not execution_results:
        print(
            "WARNING: The adaptive experiment contains no "
            "execution result records."
        )

    return run_adaptive_evaluation(
        experiment_id=experiment_id,
        executed_tests=executed_tests,
        findings=findings,
        candidate_chains=candidate_chains,
        validated_chains=validated_chains,
        chain_lengths=chain_lengths,
        validation_rates=validation_rates,
        execution_results=execution_results,
    )


# ============================================================
# BUILD STATIC EVALUATION
# ============================================================

def build_static_evaluation(experiment: dict) -> dict:
    experiment_id = experiment["experiment_id"]

    return run_static_evaluation(
        experiment_id=experiment_id,
        chain_id=experiment_id,
    )


# ============================================================
# EXECUTION-COST HELPERS
# ============================================================

def get_execution_cost(evaluation: dict) -> dict:
    cost = evaluation.get("execution_cost", {})

    if not isinstance(cost, dict):
        cost = {}

    return {
        "test_count": cost.get("test_count", 0),
        "execution_time_seconds": cost.get(
            "execution_time_seconds",
            0.0,
        ),
    }


# ============================================================
# BUILD FINAL COMPARISON
# ============================================================

def build_comparison(
    static_result: dict,
    adaptive_result: dict,
) -> dict:

    if static_result["status"] != "completed":
        raise RuntimeError(
            "Static evaluation failed: "
            + str(static_result.get("error", "unknown error"))
        )

    if adaptive_result["status"] != "completed":
        raise RuntimeError(
            "Adaptive evaluation failed: "
            + str(adaptive_result.get("error", "unknown error"))
        )

    static_evaluation = static_result["evaluation"]
    adaptive_evaluation = adaptive_result["evaluation"]

    comparison_result = compare_evaluations(
        static_evaluation,
        adaptive_evaluation,
    )

    static_cost = get_execution_cost(static_evaluation)
    adaptive_cost = get_execution_cost(adaptive_evaluation)

    comparison_result["comparison"].update({
        "static_execution_test_count": (
            static_cost["test_count"]
        ),
        "adaptive_execution_test_count": (
            adaptive_cost["test_count"]
        ),
        "execution_test_count_difference": (
            adaptive_cost["test_count"]
            - static_cost["test_count"]
        ),
        "static_execution_time_seconds": (
            static_cost["execution_time_seconds"]
        ),
        "adaptive_execution_time_seconds": (
            adaptive_cost["execution_time_seconds"]
        ),
        "execution_time_difference_seconds": (
            adaptive_cost["execution_time_seconds"]
            - static_cost["execution_time_seconds"]
        ),
        "adaptive_execution_results_available": (
            adaptive_cost["test_count"] > 0
        ),
        "static_execution_results_available": (
            static_cost["test_count"] > 0
        ),
    })

    return comparison_result


# ============================================================
# SAVE FINAL EVALUATION
# ============================================================

def save_evaluation(result: dict) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    with OUTPUT_FILE.open("w", encoding="utf-8") as file:
        json.dump(result, file, indent=2)

    print()
    print("[Evaluation] Saved to:")
    print(OUTPUT_FILE)


# ============================================================
# PRINT EVALUATION
# ============================================================

def print_evaluation(
    static_result: dict,
    adaptive_result: dict,
    comparison: dict,
) -> None:

    static = static_result["evaluation"]
    adaptive = adaptive_result["evaluation"]
    differences = comparison["comparison"]

    print()
    print("=" * 70)
    print("AGENTCHAIN DAY-14 EVALUATION")
    print("=" * 70)

    print()
    print("STATIC EVALUATION")
    print("-" * 70)

    print(f"Total tests       : {static['total_tests']}")
    print(f"Total findings    : {static['total_findings']}")
    print(f"Candidate chains  : {static['candidate_chains']}")
    print(f"Validated chains  : {static['validated_chains']}")
    print(f"Average chain len : {static['average_chain_length']}")
    print(f"Validation rate   : {static['validation_rate']}")

    print()
    print("ADAPTIVE EVALUATION")
    print("-" * 70)

    print(f"Total tests       : {adaptive['total_tests']}")
    print(f"Total findings    : {adaptive['total_findings']}")
    print(f"Candidate chains  : {adaptive['candidate_chains']}")
    print(f"Validated chains  : {adaptive['validated_chains']}")
    print(f"Average chain len : {adaptive['average_chain_length']}")
    print(f"Validation rate   : {adaptive['validation_rate']}")

    print()
    print("METRIC DIFFERENCES (ADAPTIVE - STATIC)")
    print("-" * 70)

    metric_names = [
        ("total_tests_difference", "Tests difference"),
        ("total_findings_difference", "Findings difference"),
        ("candidate_chains_difference", "Candidate chains difference"),
        ("validated_chains_difference", "Validated chains difference"),
        (
            "average_chain_length_difference",
            "Average chain length difference",
        ),
        ("validation_rate_difference", "Validation rate difference"),
    ]

    for key, label in metric_names:
        print(f"{label:<34}: {differences.get(key, 'N/A')}")

    print()
    print("SANDBOX EXECUTION COST")
    print("-" * 70)

    print(
        f"Static measured tests              : "
        f"{differences['static_execution_test_count']}"
    )
    print(
        f"Adaptive measured tests            : "
        f"{differences['adaptive_execution_test_count']}"
    )
    print(
        f"Execution test-count difference    : "
        f"{differences['execution_test_count_difference']}"
    )
    print(
        f"Static execution time (seconds)    : "
        f"{differences['static_execution_time_seconds']:.6f}"
    )
    print(
        f"Adaptive execution time (seconds)  : "
        f"{differences['adaptive_execution_time_seconds']:.6f}"
    )
    print(
        f"Execution-time difference (seconds): "
        f"{differences['execution_time_difference_seconds']:.6f}"
    )

    if not differences["adaptive_execution_results_available"]:
        print()
        print(
            "WARNING: Adaptive execution-cost measurements are missing."
        )
        print(
            "The adaptive execution-time comparison is not yet valid."
        )

    if not differences["static_execution_results_available"]:
        print()
        print(
            "WARNING: Static execution-cost measurements are missing."
        )

    print()
    print("=" * 70)


# ============================================================
# MAIN
# ============================================================

def main() -> None:

    # Load the backup adaptive experiment with execution results.
    experiment = load_json(EXPERIMENT_FILE)

    # Load the corresponding P4 validation results.
    validation = load_json(VALIDATION_FILE)

    # Build adaptive evaluation using recorded execution results.
    adaptive_result = build_adaptive_evaluation(
        experiment,
        validation,
    )

    # Run the existing static baseline evaluation.
    static_result = build_static_evaluation(experiment)

    # Compare research metrics and execution costs.
    comparison = build_comparison(
        static_result,
        adaptive_result,
    )

    final_result = {
        "experiment_id": experiment["experiment_id"],
        "adaptive": adaptive_result,
        "static": static_result,
        "comparison": comparison["comparison"],
    }

    print_evaluation(
        static_result,
        adaptive_result,
        comparison,
    )

    save_evaluation(final_result)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()
