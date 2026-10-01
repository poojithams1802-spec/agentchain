PHASE2_CONDITIONS = {
    "rule_based_fixed_mitigation": {
        "name": "Rule-based fixed mitigation",
        "purpose": "Baseline using predetermined vulnerability-to-control mapping.",
        "automatic_application": True,
        "replay": True,
        "validation": True,
    },

    "llm_recommendation_only": {
        "name": "LLM recommendation only",
        "purpose": "Measure recommendation quality without automatic application/replay.",
        "automatic_application": False,
        "replay": False,
        "validation": False,
    },

    "level3_proposed": {
        "name": "Level-3 proposed approach",
        "purpose": (
            "LLM + RAG + attack-chain context -> control -> "
            "application -> replay -> validation."
        ),
        "automatic_application": True,
        "replay": True,
        "validation": True,
    },

    "wrong_control": {
        "name": "Wrong-control test",
        "purpose": (
            "Demonstrate that applying a control does not automatically "
            "imply successful mitigation."
        ),
        "automatic_application": True,
        "replay": True,
        "validation": True,
    },
}


def get_phase2_condition(condition_name):
    return PHASE2_CONDITIONS.get(condition_name)


def get_all_phase2_conditions():
    return PHASE2_CONDITIONS.copy()