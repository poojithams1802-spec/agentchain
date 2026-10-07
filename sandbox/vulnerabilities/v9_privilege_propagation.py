def run_v9_scenario():
    """
    V9: Privilege Propagation

    Controlled scenario:
    A lower-privileged agent operation inherits or propagates
    privileges that should not be available to it.
    """

    expected = "privilege_not_propagated"
    actual = "privilege_propagated"

    vulnerable = actual != expected

    return {
        "vulnerability_id": "V9",
        "name": "privilege_propagation",
        "test": "privilege_propagation_test",
        "expected": expected,
        "actual": actual,
        "vulnerable": vulnerable,
        "severity": "high",
        "evidence": {
            "source_privilege": "LOW",
            "expected_behavior": (
                "Higher privileges must not propagate "
                "to the lower-privileged operation."
            ),
            "observed_behavior": (
                "Higher privileges were propagated "
                "to the lower-privileged operation."
            ),
        },
        "validation_rule": (
            "Privileges must not propagate beyond the "
            "authorization boundary of the operation."
        ),
    }