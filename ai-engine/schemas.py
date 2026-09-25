from typing import Any

from pydantic import BaseModel, Field


class Finding(BaseModel):
    finding: str
    severity: str
    confidence: float = Field(
        ge=0.0,
        le=1.0
    )
    evidence: str = ""


class PlannerInput(BaseModel):
    findings: list[Finding] = Field(
        default_factory=list
    )

    previous_tests: list[str] = Field(
        default_factory=list
    )

    available_tests: list[str] = Field(
        min_length=1
    )

    retrieved_knowledge: list[str] = Field(
        default_factory=list
    )

    chain_state: dict[str, Any] = Field(
        default_factory=dict
    )


class PlannerDecision(BaseModel):
    selected_test: str
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


