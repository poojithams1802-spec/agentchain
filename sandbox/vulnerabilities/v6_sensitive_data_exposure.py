def run_v6_scenario():
    """
    V6: Sensitive Data Exposure

    Controlled scenario:
    Sensitive synthetic data is returned to an agent/tool
    even though the data should have been protected.
    """

    expected = "sensitive_data_protected"
    actual = "sensitive_data_exposed"

    vulnerable = actual != expected

    return {
        "vulnerability_id": "V6",
        "name": "sensitive_data_exposure",
        "test": "sensitive_data_test",
        "expected": expected,
        "actual": actual,
        "vulnerable": vulnerable,
        "severity": "high",
        "evidence": {
            "data_classification": "SYNTHETIC_SENSITIVE",
            "expected_behavior": (
                "Sensitive data must remain protected."
            ),
            "observed_behavior": (
                "Sensitive data was exposed to the agent."
            ),
        },
        "validation_rule": (
            "Sensitive data must not be exposed to an "
            "unauthorized agent or tool."
        ),
    }