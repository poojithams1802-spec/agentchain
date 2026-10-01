from datetime import datetime, timezone
from typing import Any
import uuid

from app.database import db


def create_mitigation_run(
    experiment_id: str,
    chain_id: str,
    finding_context: dict[str, Any],
    attack_chain_context: dict[str, Any],
    status: str = "created",
) -> dict[str, Any]:
    mitigation_run_id = f"MIT-{uuid.uuid4().hex[:8]}"
    timestamp = datetime.now(timezone.utc).isoformat()

    mitigation_run = {
        "mitigation_run_id": mitigation_run_id,
        "experiment_id": experiment_id,
        "chain_id": chain_id,
        "status": status,
        "finding_context": finding_context,
        "attack_chain_context": attack_chain_context,
        "created_at": timestamp,
        "updated_at": timestamp,
    }

    db.mitigation_runs.insert_one(mitigation_run)

    return mitigation_run


def update_mitigation_run(
    mitigation_run_id: str,
    *,
    status: str | None = None,
    finding_context: dict[str, Any] | None = None,
    attack_chain_context: dict[str, Any] | None = None,
    selection: dict[str, Any] | None = None,
    application: dict[str, Any] | None = None,
    replay: dict[str, Any] | None = None,
    disruption: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    workflow_fields = {
        "status": status,
        "finding_context": finding_context,
        "attack_chain_context": attack_chain_context,
        "selection": selection,
        "application": application,
        "replay": replay,
        "disruption": disruption,
    }

    updates = {
        field: value
        for field, value in workflow_fields.items()
        if value is not None
    }

    if not updates:
        return get_mitigation_run(mitigation_run_id)

    updates["updated_at"] = datetime.now(timezone.utc).isoformat()

    db.mitigation_runs.update_one(
        {"mitigation_run_id": mitigation_run_id},
        {"$set": updates},
    )

    return get_mitigation_run(mitigation_run_id)


def get_mitigation_run(
    mitigation_run_id: str,
) -> dict[str, Any] | None:
    return db.mitigation_runs.find_one(
        {"mitigation_run_id": mitigation_run_id},
        {"_id": 0},
    )