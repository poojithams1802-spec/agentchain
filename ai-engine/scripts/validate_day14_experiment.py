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
# IMPORT P4 VALIDATOR
# ============================================================

from sandbox.validator.chain_validator import ChainValidator


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


# ============================================================
# LOAD EXPERIMENT RESULT
# ============================================================

def load_experiment_result() -> dict:

    if not EXPERIMENT_FILE.exists():
        raise FileNotFoundError(
            f"Experiment result not found: "
            f"{EXPERIMENT_FILE}"
        )

    with EXPERIMENT_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:

        return json.load(file)


# ============================================================
# VALIDATE DAY-14 CHAIN
# ============================================================

def validate_day14_chain(
    experiment_result: dict,
) -> dict:

    experiment_id = experiment_result[
        "experiment_id"
    ]

    test_sequence = experiment_result[
        "test_sequence"
    ]

    print()
    print("=" * 70)
    print("DAY 14 FINAL CHAIN VALIDATION")
    print("=" * 70)

    print(
        f"Experiment ID : {experiment_id}"
    )

    print()
    print("Candidate chain:")

    for index, test_name in enumerate(
        test_sequence,
        start=1,
    ):

        print(
            f"  {index}. {test_name}"
        )

    print()
    print("-" * 70)

    # --------------------------------------------------------
    # Create P4 validator
    # --------------------------------------------------------

    validator = ChainValidator(
        experiment_id
    )

    # --------------------------------------------------------
    # Validate chain
    # --------------------------------------------------------

    validation_result = (
        validator.validate_chain(
            chain_id=experiment_id,
            tests=test_sequence,
        )
    )

    return validation_result


# ============================================================
# PRINT VALIDATION RESULT
# ============================================================

def print_validation_result(
    validation_result: dict,
) -> None:

    print()
    print("=" * 70)
    print("VALIDATION RESULT")
    print("=" * 70)

    print(
        f"Chain ID          : "
        f"{validation_result.get('chain_id')}"
    )

    print(
        f"Status            : "
        f"{validation_result.get('status')}"
    )

    print(
        f"Validated steps   : "
        f"{validation_result.get('validated_steps')}"
    )

    print(
        f"Total steps       : "
        f"{validation_result.get('total_steps')}"
    )

    print(
        f"Chain length      : "
        f"{validation_result.get('chain_length')}"
    )

    print(
        f"Validation rate   : "
        f"{validation_result.get('validation_rate')}"
    )

    print(
        f"Findings reproduced: "
        f"{validation_result.get('all_findings_reproduced')}"
    )

    print()
    print("Step validation:")

    for index, step in enumerate(
        validation_result.get("steps", []),
        start=1,
    ):

        print()
        print(
            f"  STEP {index}"
        )

        print(
            f"    Test              : "
            f"{step.get('test')}"
        )

        print(
            f"    Status            : "
            f"{step.get('status')}"
        )

        print(
            f"    Finding           : "
            f"{step.get('finding')}"
        )

        print(
            f"    Expected finding  : "
            f"{step.get('expected_finding')}"
        )

        print(
            f"    Finding matches   : "
            f"{step.get('finding_matches')}"
        )

        print(
            f"    Dependency valid  : "
            f"{step.get('dependency_valid')}"
        )

        print(
            f"    Evidence exists   : "
            f"{step.get('evidence_exists')}"
        )

        print(
            f"    Valid             : "
            f"{step.get('valid')}"
        )

        if step.get("dependency_error"):
            print(
                f"    Dependency error  : "
                f"{step.get('dependency_error')}"
            )

    print()
    print("=" * 70)


# ============================================================
# SAVE VALIDATION RESULT
# ============================================================

def save_validation_result(
    validation_result: dict,
) -> None:

    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    with VALIDATION_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            validation_result,
            file,
            indent=2,
        )

    print()
    print(
        f"[Validation] Saved result to: "
        f"{VALIDATION_FILE}"
    )


# ============================================================
# MAIN
# ============================================================

def main() -> None:

    # --------------------------------------------------------
    # Load P3 experiment result
    # --------------------------------------------------------

    experiment_result = (
        load_experiment_result()
    )

    # --------------------------------------------------------
    # Validate using P4 validator
    # --------------------------------------------------------

    validation_result = (
        validate_day14_chain(
            experiment_result
        )
    )

    # --------------------------------------------------------
    # Display validation result
    # --------------------------------------------------------

    print_validation_result(
        validation_result
    )

    # --------------------------------------------------------
    # Save validation result
    # --------------------------------------------------------

    save_validation_result(
        validation_result
    )


if __name__ == "__main__":
    main()