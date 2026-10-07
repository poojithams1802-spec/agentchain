from typing import Any, Literal

from pydantic import BaseModel, Field


class Finding(BaseModel):
    finding: str
    severity: str
    confidence: float = Field(
        ge=0.0,
        le=1.0
    )
    evidence: str = ""


class TestingBudget(BaseModel):
    max_tests: int = Field(
        default=5,
        ge=0
    )
    max_llm_calls: int = Field(
        default=3,
        ge=0
    )
    max_time_seconds: float = Field(
        default=30.0,
        ge=0.0
    )


class BudgetUsed(BaseModel):
    tests: int = Field(
        default=0,
        ge=0
    )
    llm_calls: int = Field(
        default=0,
        ge=0
    )
    time_seconds: float = Field(
        default=0.0,
        ge=0.0
    )


class AblationConfiguration(BaseModel):
    """
    One of the four controlled Phase 3 ablation configurations.

    A: LLM only
    B: LLM + RAG
    C: LLM + attack-chain context
    D: LLM + RAG + attack-chain context
    """

    config_id: Literal[
        "A",
        "B",
        "C",
        "D",
    ]

    name: str = Field(
        min_length=1
    )

    use_rag: bool

    use_chain_context: bool

    description: str = Field(
        min_length=1
    )

class MultiAgentContext(BaseModel):
    """
    Planner-side description of the controlled Phase 3 multi-agent context.

    Agent execution, sandboxing, permission enforcement, and trust validation
    remain outside the planner.
    """

    enabled: bool = False

    agents: dict[str, dict[str, Any]] = Field(
        default_factory=dict
    )

    allowed_interactions: list[dict[str, Any]] = Field(
        default_factory=list
    )

    trust_context: dict[str, Any] = Field(
        default_factory=dict
    )

    shared_memory_context: dict[str, Any] = Field(
        default_factory=dict
    )


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

    multi_agent_context: MultiAgentContext = Field(
        default_factory=MultiAgentContext
    )

    testing_budget: TestingBudget = Field(
        default_factory=TestingBudget
    )

    budget_used: BudgetUsed = Field(
        default_factory=BudgetUsed
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


class ExperimentRequest(BaseModel):
    experiment_id: str = Field(
        min_length=1
    )
    test: str = Field(
        min_length=1
    )


class SandboxTestRequest(BaseModel):
    test: Literal[
        "permission_test",
        "tool_access_test",
        "memory_access_test",
    ]


class SandboxTestResponse(BaseModel):
    status: str
    test: str
    finding: str
    severity: str
    evidence: str
