import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


class MitigationExperimentLogger:
    """
    Persists mitigation experiment records as JSON Lines.

    Each call to log() appends one independent JSON object
    to the log file.
    """

    def __init__(self, log_path: str = "logs/mitigation_experiments.jsonl"):
        self.log_path = Path(log_path)

        self.log_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

    def log(self, record: Dict[str, Any]) -> None:
        """
        Append one experiment record to the JSONL log.
        """

        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **record,
        }

        with self.log_path.open(
            "a",
            encoding="utf-8",
        ) as file:
            file.write(
                json.dumps(
                    entry,
                    ensure_ascii=False,
                )
                + "\n"
            )