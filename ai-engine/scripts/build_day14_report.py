import json
from pathlib import Path


# ============================================================
# PATHS
# ============================================================

AI_ENGINE_ROOT = Path(__file__).resolve().parents[1]

RESULTS_DIR = AI_ENGINE_ROOT / "results"

EXPERIMENT_FILE = (
    RESULTS_DIR / "DAY14_FINAL.json"
)

VALIDATION_FILE = (
    RESULTS_DIR / "DAY14_FINAL_validation.json"
)

REPORT_FILE = (
    RESULTS_DIR / "DAY14_FINAL_report.json"
)


# ============================================================
# LOAD JSON
# ============================================================

def load_json(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(
            f"Required result file not found: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


# ============================================================
# BUILD FINAL REPORT
# ============================================================

def build_report(
    experiment: dict,
    validation: dict,
) -> dict:

    return {
        "experiment": {
            "experiment_id": experiment[
                "experiment_id"
            ],

            "tests_executed": experiment[
                "tests_executed"
            ],

            "findings_count": experiment[
                "findings_count"
            ],

            "test_sequence": experiment[
                "test_sequence"
            ],
        },

        "findings": experiment[
            "finding_sequence"
        ],

        "planner_trace": experiment[
            "planner_trace"
        ],

        "validation": {
            "status": validation[
                "status"
            ],

            "validated_steps": validation[
                "validated_steps"
            ],

            "total_steps": validation[
                "total_steps"
            ],

            "validation_rate": validation[
                "validation_rate"
            ],

            "all_findings_reproduced": validation[
                "all_findings_reproduced"
            ],

            "steps": validation[
                "steps"
            ],
        },

        "p3_summary": {
            "adaptive_planning": True,
            "rag_retrieval": True,
            "candidate_scoring": True,
            "dependency_constraints": True,
            "sandbox_integration": True,
            "fallback_handling": True,
            "structured_experiment_output": True,
            "validator_integration": True,
        },
    }


# ============================================================
# PRINT REPORT
# ============================================================

def print_report(
    report: dict,
) -> None:

    experiment = report[
        "experiment"
    ]

    validation = report[
        "validation"
    ]

    print()
    print("=" * 70)
    print("AGENTCHAIN - PERSON 3 FINAL DAY-14 REPORT")
    print("=" * 70)

    print()
    print("EXPERIMENT")
    print("-" * 70)

    print(
        f"Experiment ID : "
        f"{experiment['experiment_id']}"
    )

    print(
        f"Tests executed: "
        f"{experiment['tests_executed']}"
    )

    print(
        f"Findings      : "
        f"{experiment['findings_count']}"
    )

    print()
    print("Test sequence:")

    for index, test in enumerate(
        experiment["test_sequence"],
        start=1,
    ):
        print(
            f"  {index}. {test}"
        )

    print()
    print("FINDINGS")
    print("-" * 70)

    for index, finding in enumerate(
        report["findings"],
        start=1,
    ):

        print(
            f"\nStep {index}"
        )

        print(
            f"  Finding   : "
            f"{finding['finding']}"
        )

        print(
            f"  Severity  : "
            f"{finding['severity']}"
        )

        print(
            f"  Confidence: "
            f"{finding['confidence']}"
        )

        print(
            f"  Evidence  : "
            f"{finding['evidence']}"
        )

    print()
    print("VALIDATION")
    print("-" * 70)

    print(
        f"Status             : "
        f"{validation['status']}"
    )

    print(
        f"Validated steps    : "
        f"{validation['validated_steps']}/"
        f"{validation['total_steps']}"
    )

    print(
        f"Validation rate    : "
        f"{validation['validation_rate']:.2%}"
    )

    print(
        f"Findings reproduced: "
        f"{validation['all_findings_reproduced']}"
    )

    print()
    print("P3 COMPONENTS")
    print("-" * 70)

    for name, enabled in report[
        "p3_summary"
    ].items():

        status = (
            "YES"
            if enabled
            else "NO"
        )

        print(
            f"{name:<30}: {status}"
        )

    print()
    print("=" * 70)


# ============================================================
# SAVE REPORT
# ============================================================

def save_report(
    report: dict,
) -> None:

    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    with REPORT_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            report,
            file,
            indent=2,
        )

    print()
    print(
        f"[Report] Saved to: "
        f"{REPORT_FILE}"
    )


# ============================================================
# MAIN
# ============================================================

def main() -> None:

    experiment = load_json(
        EXPERIMENT_FILE
    )

    validation = load_json(
        VALIDATION_FILE
    )

    report = build_report(
        experiment=experiment,
        validation=validation,
    )

    print_report(
        report
    )

    save_report(
        report
    )


if __name__ == "__main__":
    main()