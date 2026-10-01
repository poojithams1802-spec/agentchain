import json
import sys
from pathlib import Path

AI_ENGINE_DIR = Path(__file__).resolve().parents[1]

if str(AI_ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(AI_ENGINE_DIR))

from mitigation_experiment_logger import MitigationExperimentLogger


def test_logger_writes_jsonl(tmp_path):
    log_path = tmp_path / "mitigation_experiments.jsonl"

    logger = MitigationExperimentLogger(
        log_path=str(log_path)
    )

    record = {
        "finding": "weak_permission_control",
        "selected_control": "authorization_gate",
        "confidence": 1.0,
        "attack_success_before": True,
        "attack_success_after": False,
    }

    logger.log(record)

    assert log_path.exists()

    lines = log_path.read_text(
        encoding="utf-8"
    ).splitlines()

    assert len(lines) == 1

    stored_record = json.loads(lines[0])

    assert stored_record["finding"] == "weak_permission_control"
    assert stored_record["selected_control"] == "authorization_gate"
    assert stored_record["confidence"] == 1.0
    assert stored_record["attack_success_before"] is True
    assert stored_record["attack_success_after"] is False

    assert "timestamp" in stored_record