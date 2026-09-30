from typing import Any, Literal

from pydantic import BaseModel, Field


ControlName = Literal[
    "authorization_gate",
    "tool_allowlist",
    "memory_validation",
]


APPROVED_CONTROLS = (
    "authorization_gate",
    "tool_allowlist",
    "memory_validation",
)


class MitigationFinding(BaseModel):
    finding: str = Field(min_length=1)

    severity: str = Field(min_length=1)

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )

    evidence: str = ""


class MitigationSelectorInput(BaseModel):
    findings: list[MitigationFinding] = Field(
        min_length=1
    )

    attack_chain: list[str] = Field(
        default_factory=list
    )

    available_controls: list[ControlName] = Field(
        default_factory=lambda: list(APPROVED_CONTROLS)
    )

    chain_state: dict[str, Any] = Field(
        default_factory=dict
    )

    retrieved_knowledge: list[str] = Field(
        default_factory=list
    )


class MitigationDecision(BaseModel):
    selected_control: ControlName

    reason: str = Field(
        min_length=1
    )

    priority: float = Field(
        ge=0.0,
        le=1.0
    )

    confidence: float = Field(
        ge=0.0,
        le=1.0
    )


class MitigationExperimentRecord(BaseModel):
    experiment_id: str = Field(
        min_length=1
    )

    finding: str = Field(
        min_length=1
    )

    selected_control: ControlName

    reason: str = Field(
        min_length=1
    )

    confidence: float = Field(
        ge=0.0,
        le=1.0
    )

    priority: float = Field(
        ge=0.0,
        le=1.0
    )

    retrieved_knowledge: list[str] = Field(
        default_factory=list
    )

    llm_used: bool = True

    fallback_used: bool = False

    validation_status: str = "not_run"