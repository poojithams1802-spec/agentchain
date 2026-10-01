from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ExperimentCreate(BaseModel):
    name: str = Field(..., min_length=1)
    mode: str = Field(..., min_length=1)
    max_tests: int = Field(..., gt=0)


class DefensiveControl(str, Enum):
    authorization_gate = "authorization_gate"
    tool_allowlist = "tool_allowlist"
    memory_validation = "memory_validation"


class MitigationSelectionRequest(BaseModel):
    chain_id: str = Field(..., min_length=1)
    finding: str = Field(..., min_length=1)
    severity: str = Field(..., min_length=1)
    evidence: Any = None
    attack_chain: list[str] = Field(..., min_length=1)
    chain_context: dict[str, Any] = Field(default_factory=dict)


class MitigationSelectionResponse(BaseModel):
    mitigation_run_id: str = Field(..., min_length=1)
    selected_control: DefensiveControl
    reason: str = Field(..., min_length=1)
    confidence: float = Field(..., ge=0.0, le=1.0)


class MitigationApplyRequest(BaseModel):
    mitigation_run_id: str = Field(..., min_length=1)
    selected_control: DefensiveControl


class MitigationReplayRequest(BaseModel):
    mitigation_run_id: str = Field(..., min_length=1)
    test: str = Field(..., min_length=1)


class ControlApplicationResult(BaseModel):
    selected_control: DefensiveControl
    status: str = Field(..., min_length=1)
    execution_info: dict[str, Any] = Field(default_factory=dict)


class BeforeAfterReplayResult(BaseModel):
    test: str = Field(..., min_length=1)
    before_result: dict[str, Any]
    after_result: dict[str, Any]
    blocked_after_mitigation: bool


class ChainDisruptionResult(BaseModel):
    chain_id: str = Field(..., min_length=1)
    before_validation: dict[str, Any]
    after_validation: dict[str, Any]
    disrupted: bool
    residual_vulnerable_steps: list[str] = Field(
        default_factory=list
    )
    validation_result: dict[str, Any] = Field(default_factory=dict)


class MitigationResultResponse(BaseModel):
    mitigation_run_id: str = Field(..., min_length=1)
    experiment_id: str = Field(..., min_length=1)
    chain_id: str = Field(..., min_length=1)
    status: str = Field(..., min_length=1)
    selection: MitigationSelectionResponse
    application: ControlApplicationResult
    replay: BeforeAfterReplayResult
    disruption: ChainDisruptionResult
