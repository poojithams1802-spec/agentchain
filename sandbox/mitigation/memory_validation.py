def validate_memory(memory_value):
    """
    Validate memory input before accepting it as trusted data.
    """

    if memory_value is None:
        return {
            "valid": False,
            "status": "blocked",
            "reason": "Memory value cannot be empty."
        }

    if not isinstance(memory_value, str):
        return {
            "valid": False,
            "status": "blocked",
            "reason": "Memory value must be a string."
        }

    if not memory_value.strip():
        return {
            "valid": False,
            "status": "blocked",
            "reason": "Memory value cannot be empty."
        }

    return {
        "valid": True,
        "status": "validated",
        "reason": "Memory value passed validation."
    }