from __future__ import annotations

from schemas import AblationConfiguration


ABLATION_CONFIGURATIONS: dict[str, AblationConfiguration] = {
    "A": AblationConfiguration(
        config_id="A",
        name="llm_only",
        use_rag=False,
        use_chain_context=False,
        description=(
            "LLM reasoning over the common planner state without "
            "security RAG or attack-chain context."
        ),
    ),
    "B": AblationConfiguration(
        config_id="B",
        name="llm_rag",
        use_rag=True,
        use_chain_context=False,
        description=(
            "LLM reasoning augmented with retrieved security "
            "knowledge, without attack-chain context."
        ),
    ),
    "C": AblationConfiguration(
        config_id="C",
        name="llm_chain",
        use_rag=False,
        use_chain_context=True,
        description=(
            "LLM reasoning augmented with controlled attack-chain "
            "context, without security RAG."
        ),
    ),
    "D": AblationConfiguration(
        config_id="D",
        name="llm_rag_chain",
        use_rag=True,
        use_chain_context=True,
        description=(
            "Full proposed planner using both retrieved security "
            "knowledge and controlled attack-chain context."
        ),
    ),
}


def get_ablation_configuration(
    configuration: str | AblationConfiguration = "D",
) -> AblationConfiguration:
    """
    Resolve an ablation configuration by ID or return a validated copy
    of an existing configuration object.
    """

    if isinstance(
        configuration,
        AblationConfiguration,
    ):
        return configuration.model_copy(
            deep=True
        )

    normalized = str(
        configuration
    ).strip().upper()

    try:
        config = ABLATION_CONFIGURATIONS[
            normalized
        ]
    except KeyError as error:
        raise ValueError(
            "Ablation configuration must be one of A, B, C, or D."
        ) from error

    return config.model_copy(
        deep=True
    )


def list_ablation_configurations() -> list[AblationConfiguration]:
    """
    Return the four configurations in fixed A-D order.
    """

    return [
        ABLATION_CONFIGURATIONS[key].model_copy(
            deep=True
        )
        for key in (
            "A",
            "B",
            "C",
            "D",
        )
    ]
