def run_v12_scenario():
    """
    V12: Tool Parameter Validation Weakness

    Controlled scenario:
    A tool accepts an invalid or unsafe parameter without
    performing the required validation.
    """

    expected = "invalid_parameter_rejected"
    actual = "invalid_parameter_accepted"

    vulnerable = actual != expected

    return {
        "vulnerability_id": "V12",
        "name": "tool_parameter_validation_weakness",
        "test": "tool_parameter_validation_test",
        "expected": expected,
        "actual": actual,
        "vulnerable": vulnerable,
        "severity": "high",
        "evidence": {
            "parameter": "SYNTHETIC_INVALID_PARAMETER",
            "expected_behavior": (
                "Invalid tool parameters must be rejected."
            ),
            "observed_behavior": (
                "The invalid tool parameter was accepted."
            ),
        },
        "validation_rule": (
            "Tool parameters must be validated before "
            "the tool operation is executed."
        ),
    }