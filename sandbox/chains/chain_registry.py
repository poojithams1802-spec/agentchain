"""
Registry for controlled Phase 3 attack chains.
"""

from copy import deepcopy

from ..execution.sandbox_executor import ALLOWED_TESTS
from .chain_definitions import CHAIN_DEFINITIONS


def validate_chain_definition(chain_definition):
    """
    Validate the structure of one chain definition.

    Existing chain fields remain mandatory for backward compatibility.
    P3 metadata fields are optional but validated when supplied.
    """

    if not isinstance(chain_definition, dict):
        return False, "Chain definition must be a dictionary."

    # =========================================================
    # EXISTING REQUIRED INTERFACE
    # =========================================================

    required_fields = {
        "chain_id",
        "name",
        "description",
        "steps",
        "dependencies",
    }

    missing_fields = (
        required_fields - set(chain_definition.keys())
    )

    if missing_fields:
        return (
            False,
            (
                "Missing required fields: "
                + ", ".join(sorted(missing_fields))
            ),
        )

    chain_id = chain_definition["chain_id"]
    name = chain_definition["name"]
    steps = chain_definition["steps"]
    dependencies = chain_definition["dependencies"]

    if not isinstance(chain_id, str) or not chain_id.strip():
        return False, "chain_id must be a non-empty string."

    if not isinstance(name, str) or not name.strip():
        return False, "name must be a non-empty string."

    if not isinstance(steps, list) or not steps:
        return False, "steps must be a non-empty list."

    if any(
        not isinstance(step, str) or not step.strip()
        for step in steps
    ):
        return (
            False,
            "Every chain step must be a non-empty string.",
        )

    if len(steps) != len(set(steps)):
        return (
            False,
            "Chain steps must not contain duplicates.",
        )

    if not isinstance(dependencies, dict):
        return False, "dependencies must be a dictionary."

    # =========================================================
    # VALIDATE SANDBOX TESTS
    # =========================================================

    for step in steps:

        if step not in ALLOWED_TESTS:
            return (
                False,
                f"Unsupported sandbox test: {step}",
            )

        if step not in dependencies:
            return (
                False,
                (
                    "Missing dependency definition for step: "
                    f"{step}"
                ),
            )

    # =========================================================
    # VALIDATE DEPENDENCY REFERENCES
    # =========================================================

    for step, required_dependencies in dependencies.items():

        if step not in steps:
            return (
                False,
                (
                    "Dependency definition references unknown "
                    f"chain step: {step}"
                ),
            )

        if not isinstance(required_dependencies, list):
            return (
                False,
                (
                    f"Dependencies for {step} must be a list."
                ),
            )

        for dependency in required_dependencies:

            if dependency not in steps:
                return (
                    False,
                    (
                        f"{step} depends on step not present "
                        f"in chain: {dependency}"
                    ),
                )

    # =========================================================
    # VALIDATE DEPENDENCY ORDER
    # =========================================================

    completed_steps = set()

    for step in steps:

        required_dependencies = dependencies.get(
            step,
            [],
        )

        missing_prior_dependencies = [
            dependency
            for dependency in required_dependencies
            if dependency not in completed_steps
        ]

        if missing_prior_dependencies:
            return (
                False,
                (
                    f"{step} requires earlier step(s): "
                    + ", ".join(missing_prior_dependencies)
                ),
            )

        completed_steps.add(step)

    # =========================================================
    # OPTIONAL P3 METADATA
    # =========================================================

    ordered_steps = chain_definition.get(
        "ordered_steps"
    )

    if ordered_steps is not None:

        if not isinstance(ordered_steps, list):
            return (
                False,
                "ordered_steps must be a list.",
            )

        if ordered_steps != steps:
            return (
                False,
                "ordered_steps must match steps exactly.",
            )

    vulnerability_ids = chain_definition.get(
        "vulnerability_ids"
    )

    if vulnerability_ids is not None:

        if not isinstance(vulnerability_ids, list):
            return (
                False,
                "vulnerability_ids must be a list.",
            )

        if len(vulnerability_ids) != len(steps):
            return (
                False,
                (
                    "vulnerability_ids must match the "
                    "number of steps."
                ),
            )

        if any(
            not isinstance(vulnerability_id, str)
            or not vulnerability_id.strip()
            for vulnerability_id in vulnerability_ids
        ):
            return (
                False,
                (
                    "Every vulnerability_id must be "
                    "a non-empty string."
                ),
            )

    for metadata_field in (
        "chain_name",
        "entry_condition",
        "expected_goal",
    ):

        value = chain_definition.get(
            metadata_field
        )

        if value is not None:

            if not isinstance(value, str):
                return (
                    False,
                    f"{metadata_field} must be a string.",
                )

            if not value.strip():
                return (
                    False,
                    (
                        f"{metadata_field} must be "
                        "a non-empty string."
                    ),
                )

    return True, None


def register_chain(chain_definition):
    """
    Validate and register a new controlled chain.

    Returns:
        Defensive copy of the registered chain.

    Raises:
        ValueError: if the chain definition is invalid.
    """

    valid, error = validate_chain_definition(
        chain_definition
    )

    if not valid:
        raise ValueError(error)

    chain_id = chain_definition["chain_id"]

    CHAIN_DEFINITIONS[chain_id] = deepcopy(
        chain_definition
    )

    return deepcopy(
        CHAIN_DEFINITIONS[chain_id]
    )


def get_chain(chain_id):
    """
    Return one chain definition.

    Returns:
        Defensive copy of the chain definition,
        or None when it does not exist.
    """

    chain = CHAIN_DEFINITIONS.get(
        chain_id
    )

    if chain is None:
        return None

    return deepcopy(chain)


def get_all_chains():
    """
    Return a defensive copy of all registered chains.
    """

    return deepcopy(
        CHAIN_DEFINITIONS
    )