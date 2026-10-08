from sandbox.evaluation.day12_ablation_metrics import (
    NA,
    calculate_configuration_metrics,
    calculate_day12_ablation_metrics,
    validate_day12_ablation_result,
)


def _make_entry(config_id: str, name: str, rag: bool, chain: bool):
    return {
        "configuration": {
            "config_id": config_id,
            "name": name,
            "use_rag": rag,
            "use_chain_context": chain,
        },
        "status": "completed",
        "tests_requested": 1,
        "tests_selected": 1,
        "selected_tests": ["permission_test"],
        "decisions": [
            {
                "step": 1,
                "selected_test": "permission_test",
                "reason": "Normal planner decision",
            }
        ],
        "budget_used": {
            "tests": 1,
            "llm_calls": 1,
            "time_seconds": 0.0,
        },
        "remaining_budget": {
            "tests": 2,
            "llm_calls": 2,
            "time_seconds": 30.0,
        },
    }


def _make_result():
    return {
        "study": "phase3_day11_ablation_framework",
        "status": "completed",
        "scenario_id": "DAY11-COMMON-001",
        "experiment_version": "day11-v1",
        "scenario_version": "sandbox-v1",
        "random_seed": 42,
        "same_initial_state": True,
        "configurations": [
            _make_entry("A", "llm_only", False, False),
            _make_entry("B", "llm_rag", True, False),
            _make_entry("C", "llm_chain", False, True),
            _make_entry("D", "llm_rag_chain", True, True),
        ],
    }


def test_validates_four_expected_configurations():
    result = _make_result()

    validation = validate_day12_ablation_result(result)

    assert validation["valid"] is True
    assert validation["errors"] == []


def test_rejects_missing_configuration():
    result = _make_result()
    result["configurations"].pop()

    validation = validate_day12_ablation_result(result)

    assert validation["valid"] is False
    assert any(
        "Expected 4 configurations" in error
        for error in validation["errors"]
    )


def test_calculates_planner_metrics():
    entry = _make_entry(
        "A",
        "llm_only",
        False,
        False,
    )

    metrics = calculate_configuration_metrics(
        entry,
        expected_tests=["permission_test"],
    )

    assert metrics["config_id"] == "A"
    assert metrics["tests_selected"] == 1
    assert metrics["llm_calls"] == 1
    assert metrics["fallback_count"] == 0
    assert metrics["adaptive_selection_accuracy"] == 1.0


def test_fallback_is_recorded():
    entry = _make_entry(
        "B",
        "llm_rag",
        True,
        False,
    )

    entry["decisions"][0]["reason"] = (
        "Fallback selected the highest-ranked candidate."
    )

    metrics = calculate_configuration_metrics(entry)

    assert metrics["fallback_count"] == 1


def test_unavailable_metrics_are_na_not_zero():
    entry = _make_entry(
        "C",
        "llm_chain",
        False,
        True,
    )

    metrics = calculate_configuration_metrics(entry)

    assert metrics["chains_discovered"] == NA
    assert metrics["validated_chains"] == NA
    assert metrics["mitigation_success"] == NA
    assert metrics["chain_disruption_rate"] == NA


def test_calculates_complete_ablation_result():
    result = _make_result()

    output = calculate_day12_ablation_metrics(
        result,
        expected_tests=["permission_test"],
    )

    assert output["validation"]["valid"] is True
    assert len(output["configurations"]) == 4
    assert {
        entry["config_id"]
        for entry in output["configurations"]
    } == {"A", "B", "C", "D"}