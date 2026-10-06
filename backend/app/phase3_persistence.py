from datetime import datetime, timezone
from typing import Any

from app.database import db


def persist_phase3_chain_result(
    result: dict[str, Any],
    collection: Any | None = None,
) -> Any:
    target_collection = (
        db.evaluation_results
        if collection is None
        else collection
    )
    document = {
        **result,
        "evaluation_type": "phase3_chain",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    return target_collection.insert_one(document)
