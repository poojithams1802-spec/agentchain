from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class ExperimentCreate(BaseModel):
    name: str = Field(..., min_length=1)
    mode: str = Field(..., min_length=1)
    max_tests: int = Field(..., gt=0)
    testing_budget: int | None = Field(None, gt=0)
    scenario_id: str | None = Field(None, min_length=1)
    scenario_name: str | None = Field(None, min_length=1)
    vulnerability_ids: list[str] = Field(default_factory=list)


class ChainExecutionRequest(BaseModel):
    chain_id: str = Field(..., min_length=1)


class ChainExecutionResponse(BaseModel):
    status: str
    experiment_id: str
    chain_id: str
    name: str | None = None
    description: str | None = None
    steps: list[dict[str, Any]]
    chain_length: int
    validated_steps: int
    total_steps: int
    validation_rate: float
    all_findings_reproduced: bool
    error: str | None = None


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

class AblationResultCreate(BaseModel):
    experiment_id: str = Field(..., min_length=1)

    configuration: Literal[
        "llm_only",
        "llm_rag",
        "llm_chain_context",
        "llm_rag_chain_context",
    ]

    status: str = Field(..., min_length=1)

    selected_tests: list[str] = Field(default_factory=list)
    tests_used: int = Field(..., ge=0)

    findings: list[str] = Field(default_factory=list)
    finding_count: int = Field(..., ge=0)

    llm_calls: int = Field(..., ge=0)
    llm_calls_used: int = Field(..., ge=0)
    fallback_used: bool

    budget_used: int = Field(..., ge=0)
    budget_remaining: int = Field(..., ge=0)

    execution_success: bool
    execution_time_seconds: float = Field(..., ge=0)

    planner_decisions: list[dict] = Field(default_factory=list)

    selection_accuracy: float | None = Field(None, ge=0, le=1)
    chain_discovery_rate: float | None = Field(None, ge=0, le=1)
    mitigation_success: float | None = Field(None, ge=0, le=1)
    chain_disruption: float | None = Field(None, ge=0, le=1)
    tests_required: int | None = Field(None, ge=0)
    latency: float | None = Field(None, ge=0)
    validation_rate: float | None = Field(None, ge=0, le=1)
    residual_vulnerable_steps: int | None = Field(None, ge=0)