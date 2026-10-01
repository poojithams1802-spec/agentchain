def check_tool_access(tool_name, allowed_tools):
    """
    Check whether a tool is explicitly allowed.
    """

    if tool_name not in allowed_tools:
        return {
            "allowed": False,
            "status": "blocked",
            "reason": "Tool is not present in the allowlist."
        }

    return {
        "allowed": True,
        "status": "allowed",
        "reason": "Tool is present in the allowlist."
    }