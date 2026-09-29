from .research_result import create_research_result
from .research_dataset import create_research_dataset, add_experiment


def build_day12_dataset():
    """
    Build the Day 12 research dataset using the
    recorded static and adaptive experiment results.
    """

    # --------------------------------------------------
    # Adaptive Experiment: EXP007
    # --------------------------------------------------

    exp007 = create_research_result(
        experiment_id="EXP007",
        mode="adaptive",
        executed_tests=[
            "permission_test",
            "tool_access_test",
            "memory_access_test"
        ],
        findings=[
            "weak_permission_control",
            "unsafe_tool_access",
            "memory_validation_weakness"
        ],
        candidate_chains=[
            "EXP007_CHAIN"
        ],
        validated_chains=[
            "EXP007_CHAIN"
        ],
        average_chain_length=3.0,
        validation_rate=1.0,
        execution_count=3
    )

    # --------------------------------------------------
    # Adaptive Experiment: EXP008
    # --------------------------------------------------

    exp008 = create_research_result(
        experiment_id="EXP008",
        mode="adaptive",
        executed_tests=[
            "tool_access_test",
            "memory_access_test",
            "permission_test"
        ],
        findings=[
            "unsafe_tool_access",
            "memory_validation_weakness",
            "weak_permission_control"
        ],
        candidate_chains=[
            "CHAIN-d2a39833"
        ],
        validated_chains=[],
        average_chain_length=3.0,
        validation_rate=0.3333,
        execution_count=3
    )
        # --------------------------------------------------
    # Adaptive Experiment: EXP010
    # --------------------------------------------------

    exp010 = create_research_result(
        experiment_id="EXP010",
        mode="adaptive",
        executed_tests=[
            "permission_test",
            "tool_access_test",
            "memory_access_test"
        ],
        findings=[
            "weak_permission_control",
            "unsafe_tool_access",
            "memory_validation_weakness"
        ],
        candidate_chains=[
            "CHAIN-d4f70fa4"
        ],
        validated_chains=[
            "CHAIN-d4f70fa4"
        ],
        average_chain_length=3.0,
        validation_rate=1.0,
        execution_count=3
    )
    # --------------------------------------------------
    # Static Experiment: STATIC_DAY12
    # --------------------------------------------------

    static_day12 = create_research_result(
        experiment_id="STATIC_DAY12",
        mode="static",
        executed_tests=[
            "permission_test",
            "tool_access_test",
            "memory_access_test"
        ],
        findings=[
            "weak_permission_control",
            "unsafe_tool_access",
            "memory_validation_weakness"
        ],
        candidate_chains=[
            "STATIC_CHAIN_DAY12"
        ],
        validated_chains=[
            "STATIC_CHAIN_DAY12"
        ],
        average_chain_length=3.0,
        validation_rate=1.0,
        execution_count=3
    )

    # --------------------------------------------------
    # Create Dataset
    # --------------------------------------------------

    dataset = create_research_dataset()

    add_experiment(
        dataset,
        exp007
    )

    add_experiment(
        dataset,
        exp008
    )
    add_experiment(
        dataset,
        exp010
    )

    add_experiment(
        dataset,
        static_day12
    )

    return dataset