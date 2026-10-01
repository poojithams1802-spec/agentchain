"""
Reusable same-attack replay and retest workflow.

The workflow:
1. Execute the baseline attack.
2. Activate the selected mitigation.
3. Execute the same attack again.
4. Compare the before/after results.
5. Return structured evidence.
"""

from ..execution.sandbox_executor import execute_sandbox_test
from .mitigation_state import activate_mitigation, reset_mitigations


def replay_attack(
    experiment_id,
    test_name,
    control_name
):
    """
    Execute the same attack before and after mitigation.

    Parameters:
        experiment_id: Unique experiment identifier.
        test_name: Controlled sandbox test to execute.
        control_name: Predefined mitigation control to activate.

    Returns:
        Structured before/after replay result.
    """

    if not experiment_id:
        return {
            "status": "failed",
            "experiment_id": experiment_id,
            "test": test_name,
            "control": control_name,
            "evidence": "experiment_id is required."
        }

    if not test_name:
        return {
            "status": "failed",
            "experiment_id": experiment_id,
            "test": test_name,
            "control": control_name,
            "evidence": "test_name is required."
        }

    if not control_name:
        return {
            "status": "failed",
            "experiment_id": experiment_id,
            "test": test_name,
            "control": control_name,
            "evidence": "control_name is required."
        }

    # Make sure this experiment starts without an active mitigation.
    reset_mitigations(experiment_id)

    # ---------------------------------------------------------
    # 1. BEFORE: Execute the original attack.
    # ---------------------------------------------------------
    before = execute_sandbox_test(
        experiment_id,
        test_name
    )

    # ---------------------------------------------------------
    # 2. Activate the selected defensive control.
    # ---------------------------------------------------------
    activation = activate_mitigation(
        experiment_id,
        control_name
    )

    if activation["status"] != "activated":
        reset_mitigations(experiment_id)

        return {
            "status": "failed",
            "experiment_id": experiment_id,
            "test": test_name,
            "control": control_name,
            "before": before,
            "activation": activation,
            "after": None,
            "evidence": "Mitigation activation failed."
        }

    # ---------------------------------------------------------
    # 3. AFTER: Replay the EXACT SAME attack.
    # ---------------------------------------------------------
    after = execute_sandbox_test(
        experiment_id,
        test_name
    )

    # ---------------------------------------------------------
    # 4. Determine whether the attack was disrupted.
    # ---------------------------------------------------------
    attack_disrupted = (
        "mitigation_applied" in after
        and after.get("evidence", {}).get("result")
        == "attack_blocked"
    )

    # ---------------------------------------------------------
    # 5. Reset experiment state.
    # ---------------------------------------------------------
    reset_result = reset_mitigations(
        experiment_id
    )

    return {
        "status": "completed",
        "experiment_id": experiment_id,
        "test": test_name,
        "control": control_name,
        "before": before,
        "activation": activation,
        "after": after,
        "attack_disrupted": attack_disrupted,
        "reset": reset_result
    }