import sys
from pathlib import Path


AI_ENGINE_DIR = Path(__file__).resolve().parents[1]

if str(AI_ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(AI_ENGINE_DIR))


from mitigation_schemas import (
    MitigationSelectorInput,
)

from mitigation_selector import (
    MitigationSelector,
)


class FakeRetriever:

    def retrieve(
        self,
        query,
        top_k=5,
    ):

        return [
            (
                "Control: authorization_gate; "
                "Target findings: "
                "weak_permission_control; "
                "Authorization must be enforced "
                "before protected operations."
            )
        ]


class FakeLLM:

    def generate_json(
        self,
        prompt,
    ):

        return {
            "selected_control":
                "authorization_gate",

            "reason":
                (
                    "The finding shows that "
                    "authorization was not enforced "
                    "before the protected operation."
                ),

            "priority":
                0.95,

            "confidence":
                0.93,
        }


def test_successful_llm_selection():

    selector_input = (
        MitigationSelectorInput(

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
                            "Permission denied "
                            "but operation allowed."
                        ),
                }
            ],

            attack_chain=[
                "permission_test",
                "tool_access_test",
            ],
        )
    )

    selector = MitigationSelector(

        llm_client=FakeLLM(),

        retriever=FakeRetriever(),
    )

    decision = selector.select(
        selector_input
    )

    assert (
        decision.selected_control
        == "authorization_gate"
    )

    assert (
        decision.confidence
        == 0.93
    )

    assert (
        selector.last_metrics[
            "llm_called"
        ]
        is True
    )

    assert (
        selector.last_metrics[
            "llm_success"
        ]
        is True
    )

    assert (
        selector.last_metrics[
            "fallback_used"
        ]
        is False
    )