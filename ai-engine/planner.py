import json
from typing import Any

from llm_client import GeminiClient
from retriever import KnowledgeRetriever
from schemas import (
    PlannerDecision,
    PlannerInput
)


class AdaptivePlanner:
    def __init__(self) -> None:
        self.llm_client = GeminiClient()
        self.retriever = KnowledgeRetriever()

    def build_query(
        self,
        planner_input: PlannerInput
    ) -> str:
        finding_text = " ".join(
            finding.finding
            for finding in planner_input.findings
        )

        available_test_text = " ".join(
            planner_input.available_tests
        )

        return (
            finding_text
            + " "
            + available_test_text
        )

    def create_prompt(
        self,
        planner_input: PlannerInput
    ) -> str:
        payload = planner_input.model_dump_json(
            indent=2
        )

        return f"""
You are the adaptive security reasoning component
of a controlled research sandbox.

Your task is to select the next test from the
provided available_tests list.

Safety rules:
1. Select only a test in available_tests.
2. Do not invent a test.
3. Do not target external systems.
4. Do not provide real-world attack instructions.
5. Return only a JSON object.
6. Priority and confidence must be between 0 and 1.

Consider:
- Current findings
- Previous tests
- Retrieved security knowledge
- Chain state
- Severity
- Confidence
- Expected information gain
- Testing cost

Required JSON format:
{{
  "selected_test": "one_allowed_test",
  "reason": "short explanation",
  "priority": 0.0,
  "confidence": 0.0
}}

Planner input:
{payload}
"""

    def fallback_decision(
        self,
        planner_input: PlannerInput,
        reason: str
        ) -> PlannerDecision:
        previous_tests = set(
            planner_input.previous_tests
        )

        unexecuted_tests = [
            test
            for test in planner_input.available_tests
            if test not in previous_tests
        ]

        if not unexecuted_tests:
            raise ValueError(
                "No unexecuted sandbox tests are available."
            )

        print("[Planner] Using fallback decision")

        return PlannerDecision(
            selected_test=unexecuted_tests[0],
            reason=(
                "Fallback decision: "
                + reason
            ),
            priority=0.1,
            confidence=0.1
        )

    def validate_decision(
        self,
        decision_data: dict[str, Any],
        planner_input: PlannerInput
    ) -> PlannerDecision:
        decision = PlannerDecision.model_validate(
            decision_data
        )

        if (
            decision.selected_test
            not in planner_input.available_tests
        ):
            raise ValueError(
                "Planner selected a test that is "
                "not in available_tests."
            )

        if (
            decision.selected_test
            in planner_input.previous_tests
        ):
            raise ValueError(
                "Planner selected a test that was "
                "already executed."
            )

        return decision

    def plan(
        self,
        planner_input: PlannerInput
    ) -> PlannerDecision:
        query = self.build_query(
            planner_input
        )

        retrieved_knowledge = (
            self.retriever.retrieve(query)
        )

        planner_input.retrieved_knowledge = (
            retrieved_knowledge
        )

        prompt = self.create_prompt(
            planner_input
        )

        try:
            response_data = (
                self.llm_client.generate_json(
                    prompt
                )
            )

            return self.validate_decision(
                response_data,
                planner_input
            )

        except Exception as error:
            print(
                f"[Planner Warning] "
                f"{type(error).__name__}: {error}"
            )

            return self.fallback_decision(
                planner_input,
                reason="The LLM decision could not be used."
            )