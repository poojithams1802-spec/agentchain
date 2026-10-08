"""
Phase 3 ablation aggregation helpers.

P2 owns aggregation of persisted Phase 3 ablation records.

P3 owns planner execution and produces comparison metrics.
P4 owns controlled execution and metric calculation.

This module does not recalculate research metrics. It only organizes
persisted A-D results into a comparison-ready response.
"""

from typing import Any

from app.database import db


CONFIGURATION_ORDER = (
    "llm_only",
    "llm_rag",
    "llm_chain_context",
    "llm_rag_chain_context",
)


def _comparison_record(record: dict[str, Any]) -> dict[str, Any]:
    """Extract comparison-ready fields without recalculating metrics."""

    chain_metrics = record.get("chain_metrics") or {}

    return {
        "ablation_run_id": record.get("ablation_run_id"),
        "experiment_id": record.get("experiment_id"),
        "configuration": record.get("configuration"),
        "status": record.get("status"),
        "selected_tests": record.get("selected_tests", []),
        "tests_required": record.get(
            "tests_required",
            record.get("tests_selected"),
        ),
        "selection_accuracy": record.get("selection_accuracy"),
        "chain_discovery_rate": record.get(
            "chain_discovery_rate"
        ),
        "mitigation_success": record.get("mitigation_success"),
        "chain_disruption": record.get("chain_disruption"),
        "llm_calls": record.get("llm_calls"),
        "latency": record.get(
            "latency",
            record.get("total_time_seconds"),
        ),
        "validation_rate": record.get(
            "validation_rate",
            chain_metrics.get("validation_rate"),
        ),
        "residual_vulnerable_steps": record.get(
            "residual_vulnerable_steps",
            (
                len(chain_metrics["residual_vulnerable_steps"])
                if isinstance(
                    chain_metrics.get("residual_vulnerable_steps"),
                    list,
                )
                else chain_metrics.get(
                    "residual_vulnerable_steps"
                )
            ),
        ),
        "planner_time_seconds": record.get(
            "planner_time_seconds"
        ),
        "execution_time_seconds": record.get(
            "execution_time_seconds"
        ),
        "total_time_seconds": record.get(
            "total_time_seconds"
        ),
        "execution_success_rate": record.get(
            "execution_success_rate"
        ),
        "fallback_used": record.get("fallback_used"),
    }


def aggregate_ablation_results(
    records: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Aggregate persisted A-D ablation results.

    Records are ordered according to the controlled Phase 3
    configuration order. No missing metric is fabricated.
    """

    grouped = {
        configuration: []
        for configuration in CONFIGURATION_ORDER
    }

    for record in records:
        configuration = record.get("configuration")

        if configuration in grouped:
            grouped[configuration].append(
                _comparison_record(record)
            )

    comparisons: list[dict[str, Any]] = []

    for configuration in CONFIGURATION_ORDER:
        comparisons.extend(grouped[configuration])

    return {
        "study": "phase3_ablation",
        "configuration_order": list(CONFIGURATION_ORDER),
        "configuration_count": len(comparisons),
        "comparisons": comparisons,
    }


def get_persisted_ablation_aggregation(
    collection: Any | None = None,
) -> dict[str, Any]:
    """Load persisted Phase 3 ablation records and aggregate them."""

    target_collection = (
        db.evaluation_results
        if collection is None
        else collection
    )

    records = list(
        target_collection.find(
            {
                "evaluation_type": "phase3_ablation",
            },
            {"_id": 0},
        )
    )

    return aggregate_ablation_results(records)