from ..execution.sandbox_executor import execute_sandbox_test


EXPECTED_FINDINGS = {
    "permission_test": "weak_permission_control",
    "tool_access_test": "unsafe_tool_access",
    "memory_access_test": "memory_validation_weakness",
}


CHAIN_DEPENDENCIES = {
    "permission_test": [],
    "tool_access_test": ["permission_test"],
    "memory_access_test": ["tool_access_test"],
}


class ChainValidator:
    """
    Validates a candidate attack chain by replaying
    its individual security tests in the controlled sandbox.
    """

    def __init__(self, experiment_id):
        self.experiment_id = experiment_id

    def _check_dependencies(self, tests):
        """
        Check whether the ordered chain satisfies
        the required dependencies.

        Returns:
            (True, None) if dependencies are valid.
            (False, error_message) otherwise.
        """

        completed_tests = set()

        for test_name in tests:

            dependencies = CHAIN_DEPENDENCIES.get(test_name)

            # Unknown test
            if dependencies is None:
                return False, f"Unknown test: {test_name}"

            # Check required previous tests
            missing_dependencies = [
                dependency
                for dependency in dependencies
                if dependency not in completed_tests
            ]

            if missing_dependencies:
                return (
                    False,
                    f"{test_name} requires: "
                    f"{', '.join(missing_dependencies)}"
                )

            completed_tests.add(test_name)

        return True, None

    def validate_chain(self, chain_id, tests):
        """
        Replay all tests and verify:

        1. Chain input is valid.
        2. Tests can be executed.
        3. Expected findings are reproduced.
        4. Evidence is produced.
        5. Dependencies are checked for multi-step chains.
        """

        # ---------------------------------------------------------
        # 1. Check chain ID
        # ---------------------------------------------------------

        if not chain_id:
            return {
                "chain_id": chain_id,
                "status": "invalid",
                "validated_steps": 0,
                "total_steps": 0,
                "steps": [],
                "error": "chain_id is required."
            }

        # ---------------------------------------------------------
        # 2. Check that tests is a list
        # ---------------------------------------------------------

        if not isinstance(tests, list):
            return {
                "chain_id": chain_id,
                "status": "invalid",
                "validated_steps": 0,
                "total_steps": 0,
                "steps": [],
                "error": "tests must be a list."
            }

        # ---------------------------------------------------------
        # 3. Check that chain contains at least one test
        # ---------------------------------------------------------

        if not tests:
            return {
                "chain_id": chain_id,
                "status": "invalid",
                "validated_steps": 0,
                "total_steps": 0,
                "steps": [],
                "error": "Attack chain must contain at least one test."
            }

        # ---------------------------------------------------------
        # 4. Check that every test name is valid text
        # ---------------------------------------------------------

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

        # ---------------------------------------------------------
        # 5. Replay each test
        #
        # A single test is allowed to run independently.
        # Dependencies are enforced only for multi-step chains.
        # ---------------------------------------------------------

        step_results = []
        completed_tests = set()

        for test_name in tests:

            dependencies = CHAIN_DEPENDENCIES.get(test_name)

            dependency_error = None

            # Unknown test
            if dependencies is None:
                dependency_error = f"Unknown test: {test_name}"

            # Check dependencies only for multi-step chains
            elif len(tests) > 1:

                missing_dependencies = [
                    dependency
                    for dependency in dependencies
                    if dependency not in completed_tests
                ]

                if missing_dependencies:
                    dependency_error = (
                        f"{test_name} requires: "
                        f"{', '.join(missing_dependencies)}"
                    )

            # -----------------------------------------------------
            # Dependency failure
            # -----------------------------------------------------

            if dependency_error:

                step_results.append({
                    "test": test_name,
                    "status": "invalid",
                    "finding": None,
                    "expected_finding": EXPECTED_FINDINGS.get(test_name),
                    "finding_matches": False,
                    "severity": None,
                    "evidence": dependency_error,
                    "evidence_exists": False,
                    "dependency_valid": False,
                    "dependency_error": dependency_error,
                    "valid": False
                })

                continue

            # -----------------------------------------------------
            # Execute sandbox test
            # -----------------------------------------------------

            result = execute_sandbox_test(
                self.experiment_id,
                test_name
            )

            expected_finding = EXPECTED_FINDINGS.get(test_name)

            # -----------------------------------------------------
            # Validate finding
            # -----------------------------------------------------

            finding_matches = (
                result["finding"] == expected_finding
            )

            # -----------------------------------------------------
            # Validate evidence
            # -----------------------------------------------------

            evidence_exists = bool(result["evidence"])

            # -----------------------------------------------------
            # Dependency passed
            # -----------------------------------------------------

            dependency_valid = True

            # -----------------------------------------------------
            # Determine whether this step is valid
            # -----------------------------------------------------

            step_valid = (
                result["status"] == "completed"
                and finding_matches
                and evidence_exists
                and dependency_valid
            )

            # -----------------------------------------------------
            # Store step result
            # -----------------------------------------------------

            step_results.append({
                "test": test_name,
                "status": result["status"],
                "finding": result["finding"],
                "expected_finding": expected_finding,
                "finding_matches": finding_matches,
                "severity": result["severity"],
                "evidence": result["evidence"],
                "evidence_exists": evidence_exists,
                "dependency_valid": dependency_valid,
                "dependency_error": None,
                "valid": step_valid
            })

            # -----------------------------------------------------
            # Add successful test to completed dependencies
            # -----------------------------------------------------

            if step_valid:
                completed_tests.add(test_name)

        # ---------------------------------------------------------
        # 6. Determine overall chain status
        # ---------------------------------------------------------

        all_steps_valid = (
            len(step_results) > 0
            and all(
                step["valid"]
                for step in step_results
            )
        )

        # ---------------------------------------------------------
        # 7. Return validation result
        # ---------------------------------------------------------

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