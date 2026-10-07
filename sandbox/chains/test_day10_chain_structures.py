from sandbox.chains.chain_registry import (
    get_all_chains,
    get_chain,
    validate_chain_definition,
)
from sandbox.chains.chain_executor import (
    execute_chain,
)


EXPECTED_CHAINS = {
    "CHAIN_A": [
        "permission_test",
        "tool_access_test",
    ],
    "CHAIN_B": [
        "permission_test",
        "tool_access_test",
        "memory_access_test",
    ],
    "CHAIN_C": [
        "tool_access_test",
        "prompt_injection_test",
        "sensitive_data_test",
    ],
    "CHAIN_D": [
        "permission_test",
        "tool_access_test",
        "memory_access_test",
        "unsafe_delegation_test",
    ],
    "CHAIN_E": [
        "prompt_injection_test",
        "sensitive_data_test",
        "unsafe_delegation_test",
    ],
}


EXPECTED_VULNERABILITIES = {
    "CHAIN_A": ["V01", "V02"],
    "CHAIN_B": ["V01", "V02", "V03"],
    "CHAIN_C": ["V02", "V04", "V06"],
    "CHAIN_D": ["V01", "V02", "V03", "V10"],
    "CHAIN_E": ["V04", "V06", "V10"],
}


def test_all_day10_chains_are_registered():
    chains = get_all_chains()

    for chain_id in EXPECTED_CHAINS:
        assert chain_id in chains


def test_all_day10_chain_definitions_are_valid():
    for chain_id in EXPECTED_CHAINS:

        chain = get_chain(
            chain_id
        )

        valid, error = (
            validate_chain_definition(
                chain
            )
        )

        assert valid, (
            f"{chain_id} should be valid: {error}"
        )


def test_ordered_steps_match_steps():
    for chain_id, expected_steps in (
        EXPECTED_CHAINS.items()
    ):

        chain = get_chain(
            chain_id
        )

        assert (
            chain["steps"]
            == expected_steps
        )

        assert (
            chain["ordered_steps"]
            == expected_steps
        )


def test_vulnerability_ids_match_chain_steps():
    for chain_id, expected_ids in (
        EXPECTED_VULNERABILITIES.items()
    ):

        chain = get_chain(
            chain_id
        )

        assert (
            chain["vulnerability_ids"]
            == expected_ids
        )

        assert len(
            chain["vulnerability_ids"]
        ) == len(
            chain["steps"]
        )


def test_required_p3_metadata_exists():
    for chain_id in EXPECTED_CHAINS:

        chain = get_chain(
            chain_id
        )

        assert chain["chain_id"]
        assert chain["chain_name"]
        assert chain["description"]
        assert chain["ordered_steps"]
        assert chain["vulnerability_ids"]
        assert chain["entry_condition"]
        assert chain["expected_goal"]


def test_existing_chain_auth_tool_unchanged():
    chain = get_chain(
        "CHAIN-AUTH-TOOL"
    )

    assert chain["steps"] == [
        "permission_test",
        "tool_access_test",
    ]


def test_existing_chain_auth_tool_memory_unchanged():
    chain = get_chain(
        "CHAIN-AUTH-TOOL-MEM"
    )

    assert chain["steps"] == [
        "permission_test",
        "tool_access_test",
        "memory_access_test",
    ]


def test_chain_c_has_chain_specific_dependencies():
    chain = get_chain(
        "CHAIN_C"
    )

    assert chain["dependencies"] == {
        "tool_access_test": [],
        "prompt_injection_test": [
            "tool_access_test",
        ],
        "sensitive_data_test": [
            "prompt_injection_test",
        ],
    }


def test_chain_d_has_correct_dependencies():
    chain = get_chain(
        "CHAIN_D"
    )

    assert chain["dependencies"] == {
        "permission_test": [],
        "tool_access_test": [
            "permission_test",
        ],
        "memory_access_test": [
            "tool_access_test",
        ],
        "unsafe_delegation_test": [
            "memory_access_test",
        ],
    }


def test_chain_e_has_correct_dependencies():
    chain = get_chain(
        "CHAIN_E"
    )

    assert chain["dependencies"] == {
        "prompt_injection_test": [],
        "sensitive_data_test": [
            "prompt_injection_test",
        ],
        "unsafe_delegation_test": [
            "sensitive_data_test",
        ],
    }


def test_chain_a_executes_and_validates():
    result = execute_chain(
        "DAY10-CHAIN-A-001",
        "CHAIN_A",
    )

    assert result["status"] == "validated"
    assert result["chain_id"] == "CHAIN_A"
    assert result["chain_length"] == 2
    assert result["validated_steps"] == 2
    assert result["validation_rate"] == 1.0
    assert result["ordered_steps"] == [
        "permission_test",
        "tool_access_test",
    ]
    assert result["vulnerability_ids"] == [
        "V01",
        "V02",
    ]


def test_chain_b_executes_and_validates():
    result = execute_chain(
        "DAY10-CHAIN-B-001",
        "CHAIN_B",
    )

    assert result["status"] == "validated"
    assert result["chain_length"] == 3
    assert result["validated_steps"] == 3


def test_chain_c_executes_and_validates():
    result = execute_chain(
        "DAY10-CHAIN-C-001",
        "CHAIN_C",
    )

    assert result["status"] == "validated"
    assert result["chain_id"] == "CHAIN_C"
    assert result["chain_length"] == 3
    assert result["validated_steps"] == 3
    assert result["validation_rate"] == 1.0
    assert result["vulnerability_ids"] == [
        "V02",
        "V04",
        "V06",
    ]


def test_chain_d_executes_and_validates():
    result = execute_chain(
        "DAY10-CHAIN-D-001",
        "CHAIN_D",
    )

    assert result["status"] == "validated"
    assert result["chain_length"] == 4
    assert result["validated_steps"] == 4


def test_chain_e_executes_and_validates():
    result = execute_chain(
        "DAY10-CHAIN-E-001",
        "CHAIN_E",
    )

    assert result["status"] == "validated"
    assert result["chain_length"] == 3
    assert result["validated_steps"] == 3


def test_chain_c_does_not_require_permission_test():
    result = execute_chain(
        "DAY10-CHAIN-C-002",
        "CHAIN_C",
    )

    selected_tests = [
        step["test"]
        for step in result["steps"]
    ]

    assert selected_tests == [
        "tool_access_test",
        "prompt_injection_test",
        "sensitive_data_test",
    ]


def test_day10_registry_contains_multiple_chain_structures():
    chains = get_all_chains()

    assert len(chains) >= 7

    for chain_id in (
        "CHAIN-AUTH-TOOL",
        "CHAIN-AUTH-TOOL-MEM",
        "CHAIN_A",
        "CHAIN_B",
        "CHAIN_C",
        "CHAIN_D",
        "CHAIN_E",
    ):
        assert chain_id in chains