def check_authorization(permission, required_permission):
    """
    Check whether the requested operation is authorized.
    """

    if permission != required_permission:
        return {
            "allowed": False,
            "status": "blocked",
            "reason": "Required authorization was not granted."
        }

    return {
        "allowed": True,
        "status": "allowed",
        "reason": "Required authorization was granted."
    }