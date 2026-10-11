
import json
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"

backup_path = RESULTS / "DAY14_FINAL_backup.json"
validation_path = RESULTS / "DAY14_FINAL_validation.json"
evaluation_path = RESULTS / "DAY14_FINAL_evaluation.json"

required_files = [
    backup_path,
    validation_path,
    evaluation_path,
]

missing = [str(path) for path in required_files if not path.exists()]

if missing:
    raise FileNotFoundError(
        "Required result files are missing:\n" + "\n".join(missing)
    )

def load_json(path):
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)

backup = load_json(backup_path)
validation = load_json(validation_path)
evaluation = load_json(evaluation_path)

report = {
    "report_date": datetime.now().astimezone().isoformat(),
    "phase": "AgentChain Phase 3",
    "regression_tests": {
        "passed": 249,
        "failed": 0,
        "status": "PASS",
        "note": "Recorded from the user's reported pytest output."
    },
    "p2_p3_integration": {
        "passed": 1,
        "failed": 0,
        "status": "PASS"
    },
    "p3_p4_e2e": {
        "scenarios": 3,
        "correct_fallback_selections": 3,
        "mitigations_applied": 3,
        "attacks_disrupted": 3,
        "residual_vulnerable_steps": 0,
        "fallback_cases": 3,
        "status": "COMPLETED_WITH_FALLBACK",
        "log": "logs/p3_p4_e2e_experiments.jsonl"
    },
    "day14_adaptive_run": {
        "test_sequence": backup.get("test_sequence"),
        "timing": backup.get("timing"),
        "fallback_used": backup.get("fallback_used"),
        "llm_calls_used": backup.get("llm_calls_used")
    },
    "day14_validation_file_exists": validation_path.exists(),
    "day14_evaluation": evaluation,
    "limitations": [
        "Gemini requests were rejected because of the free-tier quota.",
        "P3/P4 demo selections used fallback, not successful Gemini reasoning.",
        "The recorded Day 14 run is a single sample and does not establish "
        "that adaptive testing outperforms static testing.",
        "Gemini-backed A/B/C/D comparisons remain pending."
    ],
    "next_steps": [
        "Check Gemini API availability.",
        "Run comparable llm_only, llm_rag, llm_chain, and llm_rag_chain experiments.",
        "Analyze the resulting metrics and document limitations."
    ]
}

output_path = RESULTS / "PHASE3_DAY14_FINAL_REPORT.json"
with output_path.open("w", encoding="utf-8") as file:
    json.dump(report, file, indent=2, ensure_ascii=False)

print("Phase 3 report created successfully.")
print(f"Report: {output_path}")
print(f"Regression tests: {report['regression_tests']['passed']} passed")
print(f"P2/P3 integration: {report['p2_p3_integration']['status']}")
print(f"P3/P4 scenarios: {report['p3_p4_e2e']['scenarios']}")
print(f"Fallback used in Day 14 run: {report['day14_adaptive_run']['fallback_used']}")
print("Gemini-backed A/B/C/D: PENDING")
