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
    max_tests: int = Field(default=5, ge=0)
    max_llm_calls: int = Field(default=3, ge=0)
    max_time_seconds: float = Field(default=30.0, ge=0.0)

class BudgetUsed(BaseModel):
    tests: int = Field(default=0, ge=0)
    llm_calls: int = Field(default=0, ge=0)
    time_seconds: float = Field(default=0.0, ge=0.0)

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
    experiment_id: str = Field(min_length=1)
    test: str = Field(min_length=1)


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