from execution.sandbox_executor import execute_sandbox_test


EXPECTED_FINDINGS = {
    "permission_test": "weak_permission_control",
    "tool_access_test": "unsafe_tool_access",
    "memory_access_test": "memory_validation_weakness",
}


class ChainValidator:
    """
    Validates a candidate attack chain by replaying
    its individual security tests in the controlled sandbox.
    """

    def __init__(self, experiment_id):
        self.experiment_id = experiment_id

    def validate_chain(self, chain_id, tests):
        """
        Replay all tests and verify:
        1. Chain input is valid.
        2. Test completed successfully.
        3. Expected finding was reproduced.
        4. Evidence was produced.
        """

        # Check chain ID
        if not chain_id:
            return {
                "chain_id": chain_id,
                "status": "invalid",
                "validated_steps": 0,
                "total_steps": 0,
                "steps": [],
                "error": "chain_id is required."
            }

        # Check that tests is a list
        if not isinstance(tests, list):
            return {
                "chain_id": chain_id,
                "status": "invalid",
                "validated_steps": 0,
                "total_steps": 0,
                "steps": [],
                "error": "tests must be a list."
            }

        # Check that chain contains at least one test
        if not tests:
            return {
                "chain_id": chain_id,
                "status": "invalid",
                "validated_steps": 0,
                "total_steps": 0,
                "steps": [],
                "error": "Attack chain must contain at least one test."
            }

        # Check that every test name is valid text
        if any(
            not isinstance(test, str) or not test.strip()
            for test in tests
        ):
            return {
                "chain_id": chain_id,
                "status": "invalid",
                "validated_steps": 0,
                "total_steps": len(tests),
                "steps": [],
                "error": "Every chain step must contain a valid test name."
            }

        step_results = []

        # Replay each test
        for test_name in tests:

            result = execute_sandbox_test(
                self.experiment_id,
                test_name
            )

            expected_finding = EXPECTED_FINDINGS.get(test_name)

            finding_matches = (
                result["finding"] == expected_finding
            )

            evidence_exists = bool(result["evidence"])

            step_valid = (
                result["status"] == "completed"
                and finding_matches
                and evidence_exists
            )

            step_results.append({
                "test": test_name,
                "status": result["status"],
                "finding": result["finding"],
                "expected_finding": expected_finding,
                "finding_matches": finding_matches,
                "severity": result["severity"],
                "evidence": result["evidence"],
                "evidence_exists": evidence_exists,
                "valid": step_valid
            })

        # Determine overall chain status
        all_steps_valid = (
            len(step_results) > 0
            and all(
                step["valid"]
                for step in step_results
            )
        )

        return {
            "chain_id": chain_id,
            "status": "validated" if all_steps_valid else "invalid",
            "validated_steps": sum(
                step["valid"]
                for step in step_results
            ),
            "total_steps": len(step_results),
            "steps": step_results
        }