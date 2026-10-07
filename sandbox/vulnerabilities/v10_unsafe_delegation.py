def run_v10_scenario():
    """
    V10: Unsafe Delegation

    Controlled scenario:
    A lower-trust agent delegates an operation to a higher-trust
    agent without enforcing the required authorization boundary.
    """

    expected = "delegation_denied"
    actual = "delegation_allowed"

    vulnerable = actual != expected

    return {
        "vulnerability_id": "V10",
        "name": "unsafe_delegation",
        "test": "unsafe_delegation_test",
        "expected": expected,
        "actual": actual,
        "vulnerable": vulnerable,
        "severity": "high",
        "evidence": {
            "delegating_agent": "AGENT_LOW_TRUST",
            "target_agent": "AGENT_HIGH_TRUST",
            "expected_behavior": (
                "Delegation must be denied when the delegating "
                "agent lacks the required authority."
            ),
            "observed_behavior": (
                "The lower-trust agent successfully delegated "
                "the operation to the higher-trust agent."
            ),
        },
        "validation_rule": (
            "Delegation must not cross a trust or authorization "
            "boundary without explicit authorization."
        ),
    }