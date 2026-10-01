from .mitigation_registry import is_valid_control
from .authorization_gate import check_authorization
from .tool_allowlist import check_tool_access
from .memory_validation import validate_memory
from .mitigation_state import activate_mitigation


def apply_mitigation(
    experiment_id,
    control_name,
    permission=None,
    required_permission=None,
    tool_name=None,
    allowed_tools=None,
    memory_value=None
):
    """
    Apply a registered mitigation control and activate it
    for the specified experiment.
    """

    if not experiment_id:
        return {
            "status": "failed",
            "experiment_id": experiment_id,
            "control": control_name,
            "target": None,
            "evidence": "experiment_id is required."
        }

    if not control_name:
        return {
            "status": "failed",
            "experiment_id": experiment_id,
            "control": control_name,
            "target": None,
            "evidence": "control_name is required."
        }

    if not is_valid_control(control_name):
        return {
            "status": "failed",
            "experiment_id": experiment_id,
            "control": control_name,
            "target": None,
            "evidence": "Control is not registered."
        }

    # ---------------------------------------------------------
    # Control 1: Authorization Gate
    # Target: weak_permission_control
    # ---------------------------------------------------------
    if control_name == "authorization_gate":

        if permission is None or required_permission is None:
            return {
                "status": "failed",
                "experiment_id": experiment_id,
                "control": control_name,
                "target": "weak_permission_control",
                "evidence": (
                    "permission and required_permission "
                    "are required for authorization_gate."
                )
            }

        result = check_authorization(
            permission,
            required_permission
        )

        activation = activate_mitigation(
            experiment_id,
            control_name
        )

        return {
            "status": "applied",
            "experiment_id": experiment_id,
            "control": control_name,
            "target": "weak_permission_control",
            "allowed": result["allowed"],
            "activation": activation,
            "evidence": result
        }

    # ---------------------------------------------------------
    # Control 2: Tool Allowlist
    # Target: unsafe_tool_access
    # ---------------------------------------------------------
    if control_name == "tool_allowlist":

        if tool_name is None or allowed_tools is None:
            return {
                "status": "failed",
                "experiment_id": experiment_id,
                "control": control_name,
                "target": "unsafe_tool_access",
                "evidence": (
                    "tool_name and allowed_tools are required."
                )
            }

        result = check_tool_access(
            tool_name,
            allowed_tools
        )

        activation = activate_mitigation(
            experiment_id,
            control_name
        )

        return {
            "status": "applied",
            "experiment_id": experiment_id,
            "control": control_name,
            "target": "unsafe_tool_access",
            "allowed": result["allowed"],
            "activation": activation,
            "evidence": result
        }

    # ---------------------------------------------------------
    # Control 3: Memory Validation
    # Target: memory_validation_weakness
    # ---------------------------------------------------------
    if control_name == "memory_validation":

        if memory_value is None:
            return {
                "status": "failed",
                "experiment_id": experiment_id,
                "control": control_name,
                "target": "memory_validation_weakness",
                "evidence": "memory_value is required."
            }

        result = validate_memory(memory_value)

        activation = activate_mitigation(
            experiment_id,
            control_name
        )

        return {
            "status": "applied",
            "experiment_id": experiment_id,
            "control": control_name,
            "target": "memory_validation_weakness",
            "valid": result["valid"],
            "activation": activation,
            "evidence": result
        }

    # ---------------------------------------------------------
    # Fallback
    # ---------------------------------------------------------
    return {
        "status": "ready",
        "experiment_id": experiment_id,
        "control": control_name,
        "target": None,
        "evidence": "Control is registered but implementation is pending."
    }