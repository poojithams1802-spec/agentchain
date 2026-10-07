"""
Phase 3 ablation persistence helpers.

P2 owns ablation run identifiers and persistence.
P3 owns the actual planner configuration behavior and
produces the planner/evaluation results.
"""

from datetime import datetime, timezone
from typing import Any

from app.database import db


ALLOWED_CONFIGURATIONS = {
    "llm_only",
    "llm_rag",
    "llm_chain_context",
    "llm_rag_chain_context",
}


def generate_ablation_run_id(collection: Any | None = None) -> str:
    """Generate the next P2-owned ablation run identifier."""
    target_collection = (
        db.evaluation_results if collection is None else collection
    )

    count = target_collection.count_documents(
        {"evaluation_type": "phase3_ablation"}
    )

    return f"ABL{count + 1:03d}"


def persist_ablation_result(
    result: dict[str, Any],
    collection: Any | None = None,
) -> dict[str, Any]:
    """
    Persist one Phase 3 ablation result.

    P3 supplies the configuration and result values.
    P2 adds the ablation run ID, evaluation type, and timestamp.
    """
    configuration = result.get("configuration")

    if configuration not in ALLOWED_CONFIGURATIONS:
        raise ValueError(
            f"Unsupported ablation configuration: {configuration}"
        )

    target_collection = (
        db.evaluation_results if collection is None else collection
    )

    ablation_run_id = generate_ablation_run_id(target_collection)

    document = {
        "ablation_run_id": ablation_run_id,
        **result,
        "evaluation_type": "phase3_ablation",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    target_collection.insert_one(document)

    return document