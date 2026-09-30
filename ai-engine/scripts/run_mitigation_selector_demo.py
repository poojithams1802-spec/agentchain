import sys
from pathlib import Path

# Add ai-engine directory to Python import path
AI_ENGINE_DIR = Path(__file__).resolve().parents[1]

if str(AI_ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(AI_ENGINE_DIR))


import json

from mitigation_schemas import (
    MitigationSelectorInput,
)

from mitigation_selector import (
    MitigationSelector,
)


def main():

    print("=" * 60)
    print("AGENTCHAIN PHASE 2")
    print("PERSON 3 - MITIGATION SELECTOR")
    print("=" * 60)

    selector_input = MitigationSelectorInput(

        findings=[

            {
                "finding":
                    "weak_permission_control",

                "severity":
                    "high",

                "confidence":
                    1.0,

                "evidence":
                    (
                        "Permission was DENIED, "
                        "but the protected operation "
                        "was still allowed."
                    ),
            }
        ],

        attack_chain=[
            "permission_test",
            "tool_access_test",
        ],

        available_controls=[
            "authorization_gate",
            "tool_allowlist",
            "memory_validation",
        ],

        chain_state={
            "experiment_id":
                "PHASE2-DEMO-001",

            "chain_step":
                1,
        },
    )

    selector = MitigationSelector()

    decision = selector.select(
        selector_input
    )

    print("\nMITIGATION DECISION")
    print("-" * 60)

    print(
        json.dumps(
            {
                "selected_control":
                    decision.selected_control,

                "reason":
                    decision.reason,

                "priority":
                    decision.priority,

                "confidence":
                    decision.confidence,

                "retrieved_knowledge":
                    selector_input.retrieved_knowledge,

                "metrics":
                    selector.last_metrics,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()