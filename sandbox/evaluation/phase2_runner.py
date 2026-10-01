from .phase2_experiments import get_all_phase2_experiments
from .mitigation_evaluation import build_mitigation_experiment_record
from ..mitigation.replay_executor import replay_attack


def _add_selection_metadata(record, experiment):
    expected_control = experiment["expected_control"]
    selected_control = experiment["control"]

    record["test"] = experiment["test"]
    record["expected_control"] = expected_control
    record["selected_control"] = selected_control
    record["selection_correct"] = (
        expected_control == selected_control
    )
    record["condition"] = experiment["condition"]

    return record


def run_phase2_experiment(experiment):
    condition = experiment["condition"]
    experiment_id = experiment["experiment_id"]
    test_name = experiment["test"]
    control_name = experiment["control"]
    llm_calls = experiment.get("llm_calls", 0)

    # --------------------------------------------------
    # Rule-based fixed mitigation
    # --------------------------------------------------

    if condition == "rule_based_fixed_mitigation":
        replay_result = replay_attack(
            experiment_id,
            test_name,
            control_name
        )

        record = build_mitigation_experiment_record(
            replay_result,
            mode="static",
            mitigation_selected=True,
            llm_calls=0
        )

        return _add_selection_metadata(
            record,
            experiment
        )

    # --------------------------------------------------
    # LLM recommendation only
    # --------------------------------------------------

    if condition == "llm_recommendation_only":
        record = {
            "experiment_id": experiment_id,
            "mode": "adaptive",
            "condition": condition,
            "test": test_name,
            "executed_tests": [test_name],
            "findings": [],
            "candidate_chains": [],
            "validated_chains": [],
            "average_chain_length": 1.0,
            "validation_rate": 0.0,
            "execution_count": 1,
            "llm_calls": llm_calls,
            "fallback_used": False,
            "mitigation_control": control_name,
            "mitigation_selected": True,
            "mitigation_applied": False,
            "attack_success_before": None,
            "attack_success_after": None,
            "chain_disrupted": False,
            "residual_vulnerable_steps": [],
            "mitigation_validation": False,
            "recommendation_only": True,
        }

        return _add_selection_metadata(
            record,
            experiment
        )

    # --------------------------------------------------
    # Level-3 proposed approach
    # --------------------------------------------------

    if condition == "level3_proposed":
        replay_result = replay_attack(
            experiment_id,
            test_name,
            control_name
        )

        record = build_mitigation_experiment_record(
            replay_result,
            mode="adaptive",
            mitigation_selected=True,
            llm_calls=llm_calls
        )

        return _add_selection_metadata(
            record,
            experiment
        )

    # --------------------------------------------------
    # Wrong-control evaluation
    # --------------------------------------------------

    if condition == "wrong_control":
        replay_result = replay_attack(
            experiment_id,
            test_name,
            control_name
        )

        record = build_mitigation_experiment_record(
            replay_result,
            mode="adaptive",
            mitigation_selected=True,
            llm_calls=llm_calls
        )

        return _add_selection_metadata(
            record,
            experiment
        )

    raise ValueError(
        f"Unknown Phase 2 condition: {condition}"
    )


def run_all_phase2_experiments():
    results = []

    for experiment in get_all_phase2_experiments():
        results.append(
            run_phase2_experiment(experiment)
        )

    return results