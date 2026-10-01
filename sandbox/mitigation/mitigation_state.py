"""
Experiment-scoped mitigation state.

This module keeps track of which defensive controls are active
for each sandbox experiment.
"""

_ACTIVE_MITIGATIONS = {}


def activate_mitigation(experiment_id, control_name):
    """
    Activate a mitigation control for one experiment.
    """

    if not experiment_id:
        return {
            "status": "failed",
            "experiment_id": experiment_id,
            "control": control_name,
            "evidence": "experiment_id is required."
        }

    if not control_name:
        return {
            "status": "failed",
            "experiment_id": experiment_id,
            "control": control_name,
            "evidence": "control_name is required."
        }

    if experiment_id not in _ACTIVE_MITIGATIONS:
        _ACTIVE_MITIGATIONS[experiment_id] = set()

    _ACTIVE_MITIGATIONS[experiment_id].add(control_name)

    return {
        "status": "activated",
        "experiment_id": experiment_id,
        "control": control_name,
        "evidence": "Mitigation activated for experiment."
    }


def is_mitigation_active(experiment_id, control_name):
    """
    Check whether a mitigation is active for an experiment.
    """

    return (
        experiment_id in _ACTIVE_MITIGATIONS
        and control_name in _ACTIVE_MITIGATIONS[experiment_id]
    )


def get_active_mitigations(experiment_id):
    """
    Return all active mitigations for an experiment.
    """

    if experiment_id not in _ACTIVE_MITIGATIONS:
        return []

    return sorted(_ACTIVE_MITIGATIONS[experiment_id])


def reset_mitigations(experiment_id):
    """
    Reset all active mitigations for an experiment.
    """

    _ACTIVE_MITIGATIONS.pop(experiment_id, None)

    return {
        "status": "reset",
        "experiment_id": experiment_id,
        "evidence": "All mitigations reset for experiment."
    }