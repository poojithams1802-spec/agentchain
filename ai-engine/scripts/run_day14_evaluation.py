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
# IMPORT EXISTING EVALUATION COMPONENTS
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
# PATHS
# ============================================================

RESULTS_DIR = AI_ENGINE_ROOT / "results"

EXPERIMENT_FILE = (
    RESULTS_DIR / "DAY14_FINAL.json"
)

VALIDATION_FILE = (
    RESULTS_DIR / "DAY14_FINAL_validation.json"
)

OUTPUT_FILE = (
    RESULTS_DIR / "DAY14_FINAL_evaluation.json"
)


# ============================================================
# LOAD JSON
# ============================================================

def load_json(path: Path) -> dict:

    if not path.exists():
        raise FileNotFoundError(
            f"Required file not found: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:

        return json.load(file)


# ============================================================
# BUILD ADAPTIVE EVALUATION
# ============================================================

def build_adaptive_evaluation(
    experiment: dict,
    validation: dict,
) -> dict:

    experiment_id = experiment[
        "experiment_id"
    ]

    executed_tests = experiment[
        "test_sequence"
    ]

    findings = experiment[
        "finding_sequence"
    ]

    # One actual candidate chain:
    candidate_chains = [
        executed_tests
    ]

    # The actual chain was validated,
    # so include it as one validated chain.
    validated_chains = []

    if validation["status"] == "validated":
        validated_chains.append(
            executed_tests
        )

    chain_lengths = [
        len(executed_tests)
    ]

    validation_rates = [
        validation["validation_rate"]
    ]

    return run_adaptive_evaluation(

        experiment_id=experiment_id,

        executed_tests=executed_tests,

        findings=findings,

        candidate_chains=candidate_chains,

        validated_chains=validated_chains,

        chain_lengths=chain_lengths,

        validation_rates=validation_rates,
    )


# ============================================================
# BUILD STATIC EVALUATION
# ============================================================

def build_static_evaluation(
    experiment: dict,
) -> dict:

    experiment_id = experiment[
        "experiment_id"
    ]

    # The existing static evaluator expects
    # an experiment ID and chain ID.
    #
    # We use the same final experiment/chain
    # identifier so the existing P4 baseline
    # can evaluate it.

    return run_static_evaluation(

        experiment_id=experiment_id,

        chain_id=experiment_id,
    )


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
            + static_result.get(
                "error",
                "unknown error",
            )
        )

    if adaptive_result["status"] != "completed":
        raise RuntimeError(
            "Adaptive evaluation failed: "
            + adaptive_result.get(
                "error",
                "unknown error",
            )
        )

    static_evaluation = (
        static_result["evaluation"]
    )

    adaptive_evaluation = (
        adaptive_result["evaluation"]
    )

    return compare_evaluations(
        static_evaluation,
        adaptive_evaluation,
    )


# ============================================================
# SAVE FINAL EVALUATION
# ============================================================

def save_evaluation(
    result: dict,
) -> None:

    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            result,
            file,
            indent=2,
        )

    print()
    print(
        "[Evaluation] Saved to:"
    )
    print(
        OUTPUT_FILE
    )


# ============================================================
# PRINT EVALUATION
# ============================================================

def print_evaluation(
    static_result: dict,
    adaptive_result: dict,
    comparison: dict,
) -> None:

    static = static_result[
        "evaluation"
    ]

    adaptive = adaptive_result[
        "evaluation"
    ]

    differences = comparison[
        "comparison"
    ]

    print()
    print("=" * 70)
    print("AGENTCHAIN DAY-14 EVALUATION")
    print("=" * 70)

    print()
    print("STATIC EVALUATION")
    print("-" * 70)

    print(
        f"Total tests       : "
        f"{static['total_tests']}"
    )

    print(
        f"Total findings    : "
        f"{static['total_findings']}"
    )

    print(
        f"Candidate chains  : "
        f"{static['candidate_chains']}"
    )

    print(
        f"Validated chains  : "
        f"{static['validated_chains']}"
    )

    print(
        f"Average chain len : "
        f"{static['average_chain_length']}"
    )

    print(
        f"Validation rate   : "
        f"{static['validation_rate']}"
    )

    print()
    print("ADAPTIVE EVALUATION")
    print("-" * 70)

    print(
        f"Total tests       : "
        f"{adaptive['total_tests']}"
    )

    print(
        f"Total findings    : "
        f"{adaptive['total_findings']}"
    )

    print(
        f"Candidate chains  : "
        f"{adaptive['candidate_chains']}"
    )

    print(
        f"Validated chains  : "
        f"{adaptive['validated_chains']}"
    )

    print(
        f"Average chain len : "
        f"{adaptive['average_chain_length']}"
    )

    print(
        f"Validation rate   : "
        f"{adaptive['validation_rate']}"
    )

    print()
    print("METRIC DIFFERENCES")
    print("-" * 70)

    print(
        f"Tests difference          : "
        f"{differences['total_tests_difference']}"
    )

    print(
        f"Findings difference       : "
        f"{differences['total_findings_difference']}"
    )

    print(
        f"Candidate chains diff.    : "
        f"{differences['candidate_chains_difference']}"
    )

    print(
        f"Validated chains diff.    : "
        f"{differences['validated_chains_difference']}"
    )

    print(
        f"Average chain length diff.: "
        f"{differences['average_chain_length_difference']}"
    )

    print(
        f"Validation rate diff.     : "
        f"{differences['validation_rate_difference']}"
    )

    print()
    print("=" * 70)


# ============================================================
# MAIN
# ============================================================

def main() -> None:

    # --------------------------------------------------------
    # Load actual P3 experiment result
    # --------------------------------------------------------

    experiment = load_json(
        EXPERIMENT_FILE
    )

    # --------------------------------------------------------
    # Load actual P4 validation result
    # --------------------------------------------------------

    validation = load_json(
        VALIDATION_FILE
    )

    # --------------------------------------------------------
    # Adaptive evaluation
    # --------------------------------------------------------

    adaptive_result = (
        build_adaptive_evaluation(
            experiment,
            validation,
        )
    )

    # --------------------------------------------------------
    # Static baseline evaluation
    # --------------------------------------------------------

    static_result = (
        build_static_evaluation(
            experiment,
        )
    )

    # --------------------------------------------------------
    # Compare using existing P4 comparison
    # --------------------------------------------------------

    comparison = build_comparison(
        static_result,
        adaptive_result,
    )

    # --------------------------------------------------------
    # Build final result
    # --------------------------------------------------------

    final_result = {
        "experiment_id": experiment[
            "experiment_id"
        ],

        "adaptive": adaptive_result,

        "static": static_result,

        "comparison": comparison[
            "comparison"
        ],
    }

    # --------------------------------------------------------
    # Print
    # --------------------------------------------------------

    print_evaluation(
        static_result,
        adaptive_result,
        comparison,
    )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    save_evaluation(
        final_result
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()
    