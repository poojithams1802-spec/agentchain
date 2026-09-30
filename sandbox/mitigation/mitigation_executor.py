from .mitigation_registry import is_valid_control


def apply_mitigation(experiment_id, control_name):
    """
    Apply a registered mitigation control to a sandbox experiment.

    Actual control implementations will be added on Day 2.
    """

    if not experiment_id:
        return {
            "status": "failed",
            "experiment_id": experiment_id,
            "control": control_name,
            "target": None,
            "evidence": "experiment_id is required.",
        }

    if not control_name:
        return {
            "status": "failed",
            "experiment_id": experiment_id,
            "control": control_name,
            "target": None,
            "evidence": "control_name is required.",
        }

    if not is_valid_control(control_name):
        return {
            "status": "failed",
            "experiment_id": experiment_id,
            "control": control_name,
            "target": None,
            "evidence": "Control is not registered.",
        }

    return {
        "status": "ready",
        "experiment_id": experiment_id,
        "control": control_name,
        "target": None,
        "evidence": "Control is registered and ready for implementation.",
    }