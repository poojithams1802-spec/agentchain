from .mitigation_registry import is_valid_control
from .authorization_gate import check_authorization
from .tool_allowlist import check_tool_access
from .memory_validation import validate_memory
from .mitigation_state import activate_mitigation


CONTROL_TARGETS = {
    "authorization_gate": {
        "target": "weak_permission_control",
        "test": "permission_test"
    },
    "tool_allowlist": {
        "target": "unsafe_tool_access",
        "test": "tool_access_test"
    },
    "memory_validation": {
        "target": "memory_validation_weakness",
        "test": "memory_access_test"
    }
}


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
    Apply a predefined mitigation.

    Primary interface used by the backend/P2:

        apply_mitigation(experiment_id, control_name)

    Optional control-specific arguments are supported for
    backward-compatible validation tests.
    """

    # ---------------------------------------------------------
    # Validate experiment ID
    # ---------------------------------------------------------

    if not experiment_id:
        return {
            "status": "failed",
            "experiment_id": experiment_id,
            "control": control_name,
            "target": None,
            "evidence": "experiment_id is required."
        }

    # ---------------------------------------------------------
    # Validate control name
    # ---------------------------------------------------------

    if not control_name:
        return {
            "status": "failed",
            "experiment_id": experiment_id,
            "control": control_name,
            "target": None,
            "evidence": "control_name is required."
        }

    # ---------------------------------------------------------
    # Validate registered control
    # ---------------------------------------------------------

    if not is_valid_control(control_name):
        return {
            "status": "failed",
            "experiment_id": experiment_id,
            "control": control_name,
            "target": None,
            "evidence": "Control is not registered."
        }

    mapping = CONTROL_TARGETS[control_name]

    # ---------------------------------------------------------
    # Detect whether control-specific validation data
    # was supplied.
    # ---------------------------------------------------------

    validation_requested = any([
        permission is not None,
        required_permission is not None,
        tool_name is not None,
        allowed_tools is not None,
        memory_value is not None
    ])

    # =========================================================
    # AUTHORIZATION GATE
    # =========================================================

    if control_name == "authorization_gate" and validation_requested:

        if permission is None or required_permission is None:
            return {
                "status": "failed",
                "experiment_id": experiment_id,
                "control": control_name,
                "target": mapping["target"],
                "evidence": (
                    "permission and required_permission "
                    "are required for authorization_gate."
                )
            }

        validation = check_authorization(
            permission,
            required_permission
        )

        activation = activate_mitigation(
            experiment_id,
            control_name
        )

        if activation["status"] != "activated":
            return {
                "status": "failed",
                "experiment_id": experiment_id,
                "control": control_name,
                "target": mapping["target"],
                "test": mapping["test"],
                "evidence": "Mitigation activation failed."
            }

        return {
            "status": "applied",
            "experiment_id": experiment_id,
            "control": control_name,
            "target": mapping["target"],
            "test": mapping["test"],
            "allowed": validation["allowed"],
            "activation": activation,
            "evidence": validation
        }

    # =========================================================
    # TOOL ALLOWLIST
    # =========================================================

    if control_name == "tool_allowlist" and validation_requested:

        if tool_name is None or allowed_tools is None:
            return {
                "status": "failed",
                "experiment_id": experiment_id,
                "control": control_name,
                "target": mapping["target"],
                "evidence": (
                    "tool_name and allowed_tools "
                    "are required for tool_allowlist."
                )
            }

        validation = check_tool_access(
            tool_name,
            allowed_tools
        )

        activation = activate_mitigation(
            experiment_id,
            control_name
        )

        if activation["status"] != "activated":
            return {
                "status": "failed",
                "experiment_id": experiment_id,
                "control": control_name,
                "target": mapping["target"],
                "test": mapping["test"],
                "evidence": "Mitigation activation failed."
            }

        return {
            "status": "applied",
            "experiment_id": experiment_id,
            "control": control_name,
            "target": mapping["target"],
            "test": mapping["test"],
            "allowed": validation["allowed"],
            "activation": activation,
            "evidence": validation
        }

    # =========================================================
    # MEMORY VALIDATION
    # =========================================================

    if control_name == "memory_validation" and validation_requested:

        if memory_value is None:
            return {
                "status": "failed",
                "experiment_id": experiment_id,
                "control": control_name,
                "target": mapping["target"],
                "evidence": (
                    "memory_value is required "
                    "for memory_validation."
                )
            }

        validation = validate_memory(
            memory_value
        )

        activation = activate_mitigation(
            experiment_id,
            control_name
        )

        if activation["status"] != "activated":
            return {
                "status": "failed",
                "experiment_id": experiment_id,
                "control": control_name,
                "target": mapping["target"],
                "test": mapping["test"],
                "evidence": "Mitigation activation failed."
            }

        return {
            "status": "applied",
            "experiment_id": experiment_id,
            "control": control_name,
            "target": mapping["target"],
            "test": mapping["test"],
            "valid": validation["valid"],
            "activation": activation,
            "evidence": validation
        }

    # =========================================================
    # PRIMARY TWO-ARGUMENT INTERFACE
    #
    # This is the interface Person 2 will use:
    #
    # apply_mitigation(experiment_id, control_name)
    # =========================================================

    activation = activate_mitigation(
        experiment_id,
        control_name
    )

    if activation["status"] != "activated":
        return {
            "status": "failed",
            "experiment_id": experiment_id,
            "control": control_name,
            "target": mapping["target"],
            "test": mapping["test"],
            "activation": activation,
            "evidence": "Mitigation activation failed."
        }

    return {
        "status": "applied",
        "experiment_id": experiment_id,
        "control": control_name,
        "target": mapping["target"],
        "test": mapping["test"],
        "activation": activation,
        "evidence": (
            "Predefined mitigation activated for the experiment."
        )
    }


def validate_mitigation_control(
    control_name,
    permission=None,
    required_permission=None,
    tool_name=None,
    allowed_tools=None,
    memory_value=None
):
    """
    Optional direct validation helper.

    This function validates the actual defensive control
    without activating experiment mitigation state.
    """

    if not is_valid_control(control_name):
        return {
            "status": "failed",
            "control": control_name,
            "evidence": "Control is not registered."
        }

    # ---------------------------------------------------------
    # Authorization Gate
    # ---------------------------------------------------------

    if control_name == "authorization_gate":

        if permission is None or required_permission is None:
            return {
                "status": "failed",
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

        return {
            "status": "validated",
            "control": control_name,
            "target": "weak_permission_control",
            "allowed": result["allowed"],
            "evidence": result
        }

    # ---------------------------------------------------------
    # Tool Allowlist
    # ---------------------------------------------------------

    if control_name == "tool_allowlist":

        if tool_name is None or allowed_tools is None:
            return {
                "status": "failed",
                "control": control_name,
                "target": "unsafe_tool_access",
                "evidence": (
                    "tool_name and allowed_tools "
                    "are required."
                )
            }

        result = check_tool_access(
            tool_name,
            allowed_tools
        )

        return {
            "status": "validated",
            "control": control_name,
            "target": "unsafe_tool_access",
            "allowed": result["allowed"],
            "evidence": result
        }

    # ---------------------------------------------------------
    # Memory Validation
    # ---------------------------------------------------------

    if control_name == "memory_validation":

        if memory_value is None:
            return {
                "status": "failed",
                "control": control_name,
                "target": "memory_validation_weakness",
                "evidence": "memory_value is required."
            }

        result = validate_memory(
            memory_value
        )

        return {
            "status": "validated",
            "control": control_name,
            "target": "memory_validation_weakness",
            "valid": result["valid"],
            "evidence": result
        }

    return {
        "status": "failed",
        "control": control_name,
        "evidence": "Unsupported control."
    }