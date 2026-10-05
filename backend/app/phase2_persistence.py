from datetime import datetime, timezone
from typing import Any

from app.database import db


PHASE2_CONDITION_RUNNER_SOURCE = "phase2_condition_runner"


def persist_phase2_condition_records(
    records: list[dict[str, Any]],
    collection: Any | None = None,
) -> int:
    target_collection = (
        db.evaluation_results
        if collection is None
        else collection
    )
    persisted_count = 0

    for record in records:
        document = {
            **record,
            "evaluation_type": "phase2_condition",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": PHASE2_CONDITION_RUNNER_SOURCE,
        }

        target_collection.update_one(
            {
                "evaluation_type": "phase2_condition",
                "source": PHASE2_CONDITION_RUNNER_SOURCE,
                "experiment_id": record["experiment_id"],
            },
            {"$set": document},
            upsert=True,
        )
        persisted_count += 1

    return persisted_count