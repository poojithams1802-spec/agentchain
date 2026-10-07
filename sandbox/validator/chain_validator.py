from ..execution.sandbox_executor import (
    execute_sandbox_test,
)
from ..chains.chain_registry import get_chain


EXPECTED_FINDINGS = {
    "permission_test": "weak_permission_control",
    "tool_access_test": "unsafe_tool_access",
    "memory_access_test": "memory_validation_weakness",
    "prompt_injection_test": "prompt_injection",
    "indirect_prompt_injection_test": (
        "indirect_prompt_injection"
    ),
    "sensitive_data_test": "sensitive_data_exposure",
    "file_operation_test": "unsafe_file_operation",
    "context_manipulation_test": "context_manipulation",
    "privilege_propagation_test": "privilege_propagation",
    "unsafe_delegation_test": "unsafe_delegation",
    "cross_agent_trust_test": (
        "cross_agent_trust_weakness"
    ),
    "tool_parameter_validation_test": (
        "tool_parameter_validation_weakness"
    ),
}


# Legacy dependency rules.
# These remain available for unregistered/custom chains.
CHAIN_DEPENDENCIES = {
    "permission_test": [],
    "tool_access_test": [
        "permission_test",
    ],
    "memory_access_test": [
        "tool_access_test",
    ],
    "prompt_injection_test": [],
    "indirect_prompt_injection_test": [],
    "sensitive_data_test": [],
    "file_operation_test": [],
    "context_manipulation_test": [],
    "privilege_propagation_test": [],
    "unsafe_delegation_test": [],
    "cross_agent_trust_test": [],
    "tool_parameter_validation_test": [],
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
        Check dependency ordering using legacy dependency rules.

        Registered chains use their own dependency definitions
        inside validate_chain().
        """

        completed_tests = set()

        for test_name in tests:

            dependencies = CHAIN_DEPENDENCIES.get(
                test_name
            )

            if dependencies is None:
                return (
                    False,
                    f"Unknown test: {test_name}",
                )

            missing_dependencies = [
                dependency
                for dependency in dependencies
                if dependency not in completed_tests
            ]

            if missing_dependencies:
                return (
                    False,
                    (
                        f"{test_name} requires: "
                        + ", ".join(
                            missing_dependencies
                        )
                    ),
                )

            completed_tests.add(
                test_name
            )

        return True, None

    def validate_chain(
        self,
        chain_id,
        tests,
    ):
        """
        Replay all tests and verify:

        1. Chain input is valid.
        2. Tests can be executed.
        3. Expected findings are reproduced.
        4. Evidence is produced.
        5. Chain-specific dependencies are respected.
        """

        # =====================================================
        # 1. CHECK CHAIN ID
        # =====================================================

        if not chain_id:
            return {
                "chain_id": chain_id,
                "status": "invalid",
                "validated_steps": 0,
                "total_steps": 0,
                "steps": [],
                "error": "chain_id is required.",
            }

        # =====================================================
        # 2. CHECK TEST LIST
        # =====================================================

        if not isinstance(tests, list):
            return {
                "chain_id": chain_id,
                "status": "invalid",
                "validated_steps": 0,
                "total_steps": 0,
                "steps": [],
                "error": "tests must be a list.",
            }

        # =====================================================
        # 3. CHECK NON-EMPTY CHAIN
        # =====================================================

        if not tests:
            return {
                "chain_id": chain_id,
                "status": "invalid",
                "validated_steps": 0,
                "total_steps": 0,
                "steps": [],
                "error": (
                    "Attack chain must contain "
                    "at least one test."
                ),
            }

        # =====================================================
        # 4. CHECK TEST NAME FORMAT
        # =====================================================

        if any(
            not isinstance(test, str)
            or not test.strip()
            for test in tests
        ):
            return {
                "chain_id": chain_id,
                "status": "invalid",
                "validated_steps": 0,
                "total_steps": len(tests),
                "steps": [],
                "error": (
                    "Every chain step must contain "
                    "a valid test name."
                ),
            }

        # =====================================================
        # 5. GET REGISTERED CHAIN DEPENDENCIES
        # =====================================================

        chain_definition = get_chain(
            chain_id
        )

        if chain_definition is not None:

            chain_specific_dependencies = (
                chain_definition.get(
                    "dependencies"
                )
            )

        else:

            chain_specific_dependencies = None

        # =====================================================
        # 6. REPLAY EACH TEST
        # =====================================================

        step_results = []
        completed_tests = set()

        for test_name in tests:

            # Registered chain:
            # use its explicit dependencies.
            #
            # Unknown/custom chain:
            # preserve legacy dependency behavior.

            if chain_specific_dependencies is not None:

                dependencies = (
                    chain_specific_dependencies.get(
                        test_name
                    )
                )

            else:

                dependencies = (
                    CHAIN_DEPENDENCIES.get(
                        test_name
                    )
                )

            dependency_error = None

            # Unknown test
            if dependencies is None:
                dependency_error = (
                    f"Unknown test: {test_name}"
                )

            # Dependency check
            elif len(tests) > 1:

                missing_dependencies = [
                    dependency
                    for dependency
                    in dependencies
                    if dependency
                    not in completed_tests
                ]

                if missing_dependencies:
                    dependency_error = (
                        f"{test_name} requires: "
                        + ", ".join(
                            missing_dependencies
                        )
                    )

            # =================================================
            # DEPENDENCY FAILURE
            # =================================================

            if dependency_error:

                step_results.append(
                    {
                        "test": test_name,
                        "status": "invalid",
                        "finding": None,
                        "expected_finding": (
                            EXPECTED_FINDINGS.get(
                                test_name
                            )
                        ),
                        "finding_matches": False,
                        "severity": None,
                        "evidence": dependency_error,
                        "evidence_exists": False,
                        "dependency_valid": False,
                        "dependency_error": (
                            dependency_error
                        ),
                        "valid": False,
                        "execution_cost": None,
                    }
                )

                continue

            # =================================================
            # EXECUTE SANDBOX TEST
            # =================================================

            result = execute_sandbox_test(
                self.experiment_id,
                test_name,
            )

            expected_finding = (
                EXPECTED_FINDINGS.get(
                    test_name
                )
            )

            # =================================================
            # VALIDATE FINDING
            # =================================================

            finding_matches = (
                result.get("finding")
                == expected_finding
            )

            # =================================================
            # VALIDATE EVIDENCE
            # =================================================

            evidence_exists = bool(
                result.get("evidence")
            )

            # =================================================
            # DEPENDENCY PASSED
            # =================================================

            dependency_valid = True

            # =================================================
            # FINAL STEP VALIDATION
            # =================================================

            step_valid = (
                result.get("status")
                == "completed"
                and finding_matches
                and evidence_exists
                and dependency_valid
            )

            # =================================================
            # STORE STEP RESULT
            # =================================================

            step_results.append(
                {
                    "test": test_name,
                    "status": result.get(
                        "status"
                    ),
                    "finding": result.get(
                        "finding"
                    ),
                    "expected_finding": (
                        expected_finding
                    ),
                    "finding_matches": (
                        finding_matches
                    ),
                    "severity": result.get(
                        "severity"
                    ),
                    "evidence": result.get(
                        "evidence"
                    ),
                    "evidence_exists": (
                        evidence_exists
                    ),
                    "dependency_valid": (
                        dependency_valid
                    ),
                    "dependency_error": None,
                    "valid": step_valid,
                    "execution_cost": (
                        result.get(
                            "execution_cost"
                        )
                    ),
                }
            )

            # =================================================
            # ADD SUCCESSFUL STEP
            # =================================================

            if step_valid:
                completed_tests.add(
                    test_name
                )

        # =====================================================
        # 7. OVERALL VALIDATION
        # =====================================================

        all_steps_valid = (
            len(step_results) > 0
            and all(
                step["valid"]
                for step in step_results
            )
        )

        validated_steps = sum(
            step["valid"]
            for step in step_results
        )

        total_steps = len(
            step_results
        )

        validation_rate = (
            validated_steps / total_steps
            if total_steps > 0
            else 0.0
        )

        all_findings_reproduced = (
            total_steps > 0
            and validated_steps == total_steps
        )

        return {
            "chain_id": chain_id,
            "status": (
                "validated"
                if all_steps_valid
                else "invalid"
            ),
            "validated_steps": validated_steps,
            "total_steps": total_steps,
            "chain_length": total_steps,
            "validation_rate": validation_rate,
            "all_findings_reproduced": (
                all_findings_reproduced
            ),
            "steps": step_results,
        }