from sandbox.evaluation.day12_ablation_experiment import (
    EXPECTED_TEST_SEQUENCE,
)


def test_expected_sequence_is_controlled():
    assert EXPECTED_TEST_SEQUENCE == [
        "permission_test",
        "tool_access_test",
        "memory_access_test",
    ]


def test_expected_sequence_length():
    assert len(EXPECTED_TEST_SEQUENCE) == 3