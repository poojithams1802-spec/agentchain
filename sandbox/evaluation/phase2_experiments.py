from .phase2_conditions import get_phase2_condition


EXPERIMENTS = [
    # --------------------------------------------------
    # Rule-based fixed mitigation baseline
    # --------------------------------------------------

    {
        "experiment_id": "P2-RULE-001",
        "condition": "rule_based_fixed_mitigation",
        "mode": "static",
        "test": "permission_test",
        "expected_control": "authorization_gate",
        "control": "authorization_gate",
        "llm_calls": 0,
    },
    {
        "experiment_id": "P2-RULE-002",
        "condition": "rule_based_fixed_mitigation",
        "mode": "static",
        "test": "tool_access_test",
        "expected_control": "tool_allowlist",
        "control": "tool_allowlist",
        "llm_calls": 0,
    },
    {
        "experiment_id": "P2-RULE-003",
        "condition": "rule_based_fixed_mitigation",
        "mode": "static",
        "test": "memory_access_test",
        "expected_control": "memory_validation",
        "control": "memory_validation",
        "llm_calls": 0,
    },

    # --------------------------------------------------
    # LLM recommendation only
    # --------------------------------------------------

    {
        "experiment_id": "P2-LLM-001",
        "condition": "llm_recommendation_only",
        "mode": "adaptive",
        "test": "permission_test",
        "expected_control": "authorization_gate",
        "control": "authorization_gate",
        "llm_calls": 1,
    },
    {
        "experiment_id": "P2-LLM-002",
        "condition": "llm_recommendation_only",
        "mode": "adaptive",
        "test": "tool_access_test",
        "expected_control": "tool_allowlist",
        "control": "tool_allowlist",
        "llm_calls": 1,
    },
    {
        "experiment_id": "P2-LLM-003",
        "condition": "llm_recommendation_only",
        "mode": "adaptive",
        "test": "memory_access_test",
        "expected_control": "memory_validation",
        "control": "memory_validation",
        "llm_calls": 1,
    },

    # --------------------------------------------------
    # Level-3 proposed approach
    # --------------------------------------------------

    {
        "experiment_id": "P2-L3-001",
        "condition": "level3_proposed",
        "mode": "adaptive",
        "test": "permission_test",
        "expected_control": "authorization_gate",
        "control": "authorization_gate",
        "llm_calls": 1,
    },
    {
        "experiment_id": "P2-L3-002",
        "condition": "level3_proposed",
        "mode": "adaptive",
        "test": "tool_access_test",
        "expected_control": "tool_allowlist",
        "control": "tool_allowlist",
        "llm_calls": 1,
    },
    {
        "experiment_id": "P2-L3-003",
        "condition": "level3_proposed",
        "mode": "adaptive",
        "test": "memory_access_test",
        "expected_control": "memory_validation",
        "control": "memory_validation",
        "llm_calls": 1,
    },

    # --------------------------------------------------
    # Wrong-control evaluation
    # --------------------------------------------------

    {
        "experiment_id": "P2-WRONG-001",
        "condition": "wrong_control",
        "mode": "adaptive",
        "test": "permission_test",
        "expected_control": "authorization_gate",
        "control": "tool_allowlist",
        "llm_calls": 1,
    },
    {
        "experiment_id": "P2-WRONG-002",
        "condition": "wrong_control",
        "mode": "adaptive",
        "test": "tool_access_test",
        "expected_control": "tool_allowlist",
        "control": "memory_validation",
        "llm_calls": 1,
    },
    {
        "experiment_id": "P2-WRONG-003",
        "condition": "wrong_control",
        "mode": "adaptive",
        "test": "memory_access_test",
        "expected_control": "memory_validation",
        "control": "authorization_gate",
        "llm_calls": 1,
    },
]


def get_phase2_experiment(experiment_id):
    for experiment in EXPERIMENTS:
        if experiment["experiment_id"] == experiment_id:
            return experiment.copy()

    return None


def get_all_phase2_experiments():
    return [
        experiment.copy()
        for experiment in EXPERIMENTS
    ]


def get_experiment_condition(experiment_id):
    experiment = get_phase2_experiment(experiment_id)

    if experiment is None:
        return None

    return get_phase2_condition(
        experiment["condition"]
    )