def memory_tool(state, action, key=None, value=None):

    if action == "write":
        state.set_memory(key, value)

        return {
            "action": "write",
            "key": key,
            "value": value
        }

    if action == "read":
        return {
            "action": "read",
            "key": key,
            "value": state.get_memory(key)
        }

    return {
        "error": "Unsupported memory action."
    }