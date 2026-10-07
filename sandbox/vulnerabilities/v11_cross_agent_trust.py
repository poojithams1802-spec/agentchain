def run_v11_scenario():
    """
    V11: Cross-Agent Trust Weakness

    Controlled scenario:
    A lower-trust agent accepts a message or request from
    another agent without enforcing the required trust boundary.
    """

    expected = "untrusted_agent_rejected"
    actual = "untrusted_agent_trusted"

    vulnerable = actual != expected

    return {
        "vulnerability_id": "V11",
        "name": "cross_agent_trust_weakness",
        "test": "cross_agent_trust_test",
        "expected": expected,
        "actual": actual,
        "vulnerable": vulnerable,
        "severity": "high",
        "evidence": {
            "source_agent": "AGENT_UNTRUSTED",
            "target_agent": "AGENT_CONTROLLED",
            "expected_behavior": (
                "Requests from an untrusted agent must be rejected "
                "unless the required trust relationship exists."
            ),
            "observed_behavior": (
                "The untrusted agent was incorrectly treated as trusted."
            ),
        },
        "validation_rule": (
            "Cross-agent requests must be validated against the "
            "defined trust boundary before being accepted."
        ),
    }