def run_v1_scenario():
    """
    V1: Weak Permission Control

    Controlled scenario:
    A protected tool is marked as denied, but a weak
    permission check incorrectly allows the operation.
    """

    expected = "denied"
    actual = "allowed"

    vulnerable = actual != expected

    return {
        "vulnerability_id": "V1",
        "name": "weak_permission_control",
        "test": "permission_test",
        "expected": expected,
        "actual": actual,
        "vulnerable": vulnerable,
        "severity": "high",
        "evidence": {
            "permission": "DENIED",
            "observed_behavior": "TOOL_ALLOWED"
        },
        "validation_rule": "Operation must be denied when permission is denied."
    }