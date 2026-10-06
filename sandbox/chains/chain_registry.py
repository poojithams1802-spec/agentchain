"""
Registry for controlled Phase 3 attack chains.
"""

from copy import deepcopy

from ..execution.sandbox_executor import ALLOWED_TESTS
from .chain_definitions import CHAIN_DEFINITIONS


def validate_chain_definition(chain_definition):
    """
    Validate the structure of one chain definition.

    Returns:
        (True, None) when valid.
        (False, error_message) when invalid.
    """

    if not isinstance(chain_definition, dict):
        return False, "Chain definition must be a dictionary."

    required_fields = {
        "chain_id",
        "name",
        "description",
        "steps",
        "dependencies",
    }

    missing_fields = required_fields - set(chain_definition.keys())

    if missing_fields:
        return (
            False,
            f"Missing required fields: {', '.join(sorted(missing_fields))}",
        )

    chain_id = chain_definition["chain_id"]
    steps = chain_definition["steps"]
    dependencies = chain_definition["dependencies"]

    if not isinstance(chain_id, str) or not chain_id.strip():
        return False, "chain_id must be a non-empty string."

    if not isinstance(steps, list) or not steps:
        return False, "steps must be a non-empty list."

    if any(
        not isinstance(step, str) or not step.strip()
        for step in steps
    ):
        return False, "Every chain step must be a non-empty string."

    if len(steps) != len(set(steps)):
        return False, "Chain steps must not contain duplicates."

    if not isinstance(dependencies, dict):
        return False, "dependencies must be a dictionary."

    # Every step must be a supported sandbox test.
    for step in steps:
        if step not in ALLOWED_TESTS:
            return False, f"Unsupported sandbox test: {step}"

        if step not in dependencies:
            return (
                False,
                f"Missing dependency definition for step: {step}",
            )

    # Dependencies must refer only to steps inside this chain.
    for step, required_dependencies in dependencies.items():

        if step not in steps:
            return (
                False,
                f"Dependency definition references unknown chain step: {step}",
            )

        if not isinstance(required_dependencies, list):
            return (
                False,
                f"Dependencies for {step} must be a list.",
            )

        for dependency in required_dependencies:

            if dependency not in steps:
                return (
                    False,
                    f"{step} depends on step not present in chain: "
                    f"{dependency}",
                )

    # Dependencies must appear before the step that requires them.
    completed_steps = set()

    for step in steps:

        required_dependencies = dependencies.get(step, [])

        missing_prior_dependencies = [
            dependency
            for dependency in required_dependencies
            if dependency not in completed_steps
        ]

        if missing_prior_dependencies:
            return (
                False,
                f"{step} requires earlier step(s): "
                f"{', '.join(missing_prior_dependencies)}",
            )

        completed_steps.add(step)

    return True, None


def register_chain(chain_definition):
    """
    Validate and register a new controlled chain.

    Returns:
        A defensive copy of the registered chain.

    Raises:
        ValueError: if the chain definition is invalid.
    """

    valid, error = validate_chain_definition(chain_definition)

    if not valid:
        raise ValueError(error)

    chain_id = chain_definition["chain_id"]

    CHAIN_DEFINITIONS[chain_id] = deepcopy(chain_definition)

    return deepcopy(CHAIN_DEFINITIONS[chain_id])


def get_chain(chain_id):
    """
    Return one chain definition.

    Returns:
        A defensive copy of the chain definition,
        or None when the chain does not exist.
    """

    chain = CHAIN_DEFINITIONS.get(chain_id)

    if chain is None:
        return None

    return deepcopy(chain)


def get_all_chains():
    """
    Return all registered chain definitions.

    Returns:
        A defensive copy of the complete registry.
    """

    return deepcopy(CHAIN_DEFINITIONS)