def run_v3_scenario():
    """
    V3: Controlled Memory Validation Weakness

    Controlled scenario:
    The agent accepts memory data without performing
    the required validation.
    """

    expected = "validated"
    actual = "accepted_without_validation"

    vulnerable = actual != expected

    return {
        "vulnerability_id": "V3",
        "name": "memory_validation_weakness",
        "test": "memory_access_test",
        "expected": expected,
        "actual": actual,
        "vulnerable": vulnerable,
        "severity": "medium",
        "evidence": {
            "expected": "Memory input should be validated.",
            "actual": "Memory input was accepted without validation."
        },
        "validation_rule": "Memory data must pass validation before being accepted."
    }