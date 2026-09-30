MITIGATION_CONTROLS = {
    "authorization_gate": {
        "target": "weak_permission_control",
        "description": "Require authorization before sensitive operations.",
    },

    "tool_allowlist": {
        "target": "unsafe_tool_access",
        "description": "Restrict the agent to explicitly approved tools.",
    },

    "memory_validation": {
        "target": "memory_validation_weakness",
        "description": "Validate memory input before accepting it as trusted data.",
    },
}
MITIGATION_CONTROLS = {
    "authorization_gate": {
        "target": "weak_permission_control",
        "description": "Require authorization before sensitive operations.",
    },

    "tool_allowlist": {
        "target": "unsafe_tool_access",
        "description": "Restrict the agent to explicitly approved tools.",
    },

    "memory_validation": {
        "target": "memory_validation_weakness",
        "description": "Validate memory input before accepting it as trusted data.",
    },
}


def is_valid_control(control_name):
    return control_name in MITIGATION_CONTROLS


def get_control(control_name):
    return MITIGATION_CONTROLS.get(control_name)


def get_all_controls():
    return MITIGATION_CONTROLS.copy()