import json
from typing import Any
from time import perf_counter
from mitigation_retriever import (
    MitigationKnowledgeRetriever,
)

from mitigation_schemas import (
    APPROVED_CONTROLS,
    MitigationDecision,
    MitigationSelectorInput,
)


# ---------------------------------------------------------
# Deterministic safety mapping
# ---------------------------------------------------------

EXPECTED_CONTROL_BY_FINDING = {

    "weak_permission_control":
        "authorization_gate",

    "unsafe_tool_access":
        "tool_allowlist",

    "memory_validation_weakness":
        "memory_validation",
}


class MitigationSelector:

    """
    AgentChain Phase 2 — Person 3

    Pipeline:

    Finding
       ↓
    Attack-chain context
       ↓
    Mitigation RAG
       ↓
    Gemini
       ↓
    Structured decision
       ↓
    Safety validation
       ↓
    Predefined control
    """

    def __init__(
        self,
        llm_client=None,
        retriever=None,
    ) -> None:

        self.retriever = (
            retriever
            or MitigationKnowledgeRetriever()
        )

        if llm_client is None:

            from llm_client import GeminiClient

            self.llm_client = GeminiClient()

        else:

            self.llm_client = llm_client

        self.last_metrics = {}

    # -----------------------------------------------------
    # Build RAG query
    # -----------------------------------------------------

    def build_query(
        self,
        selector_input: MitigationSelectorInput,
    ) -> str:

        parts = []

        for finding in selector_input.findings:

            parts.extend(
                [
                    finding.finding,
                    finding.severity,
                    finding.evidence,
                ]
            )

        parts.extend(
            selector_input.attack_chain
        )

        parts.extend(
            selector_input.available_controls
        )

        for key, value in (
            selector_input.chain_state.items()
        ):

            parts.extend(
                [
                    str(key),
                    str(value),
                ]
            )

        return " ".join(
            part
            for part in parts
            if part
        ).strip()

    # -----------------------------------------------------
    # RAG
    # -----------------------------------------------------

    def retrieve_knowledge(
        self,
        selector_input: MitigationSelectorInput,
        top_k: int = 5,
    ) -> list[str]:

        query = self.build_query(
            selector_input
        )

        if not query:
            return []

        try:

            return self.retriever.retrieve(
                query,
                top_k=top_k,
            )

        except Exception as error:

            print(
                "[Mitigation RAG Warning]",
                type(error).__name__,
                str(error),
            )

            return []

    # -----------------------------------------------------
    # Expected control
    # -----------------------------------------------------

    def expected_controls(
        self,
        selector_input: MitigationSelectorInput,
    ) -> set[str]:

        expected = set()

        for finding in (
            selector_input.findings
        ):

            finding_name = (
                finding.finding
                .strip()
                .lower()
            )

            control = (
                EXPECTED_CONTROL_BY_FINDING
                .get(finding_name)
            )

            if control:

                expected.add(control)

        return expected

    # -----------------------------------------------------
    # Prompt
    # -----------------------------------------------------

    def build_prompt(
        self,
        selector_input: MitigationSelectorInput,
    ) -> str:

        payload = {

            "findings": [
                finding.model_dump()
                for finding
                in selector_input.findings
            ],

            "attack_chain":
                selector_input.attack_chain,

            "available_controls":
                selector_input.available_controls,

            "retrieved_knowledge":
                selector_input.retrieved_knowledge,

            "chain_state":
                selector_input.chain_state,
        }

        return f"""
You are the mitigation-selection component
of AgentChain Phase 2.

Your job is to recommend ONE predefined
defensive control for a finding observed
in the controlled security sandbox.

Approved controls:

authorization_gate
- Enforce authorization before restricted operations.

tool_allowlist
- Restrict callable tools to an explicit allowlist.

memory_validation
- Validate memory data before it becomes
  trusted agent state.

RULES:

1. Select exactly ONE value from available_controls.

2. Never invent a new control.

3. Use:
   - finding
   - evidence
   - attack-chain context
   - retrieved mitigation knowledge

4. Do not generate source-code patches.

5. Do not propose deployment.

6. Do not invent security controls.

7. The selected control must directly address
   the observed finding.

8. Return ONLY JSON.

Required JSON:

{{
    "selected_control": "authorization_gate",
    "reason": "Evidence-based explanation",
    "priority": 0.0,
    "confidence": 0.0
}}

Context:

{json.dumps(
    payload,
    indent=2
)}
"""

    # -----------------------------------------------------
    # Validate LLM decision
    # -----------------------------------------------------

    def validate_decision(
        self,
        decision_data: dict[str, Any],
        selector_input: MitigationSelectorInput,
    ) -> MitigationDecision:

        decision = (
            MitigationDecision.model_validate(
                decision_data
            )
        )

        # Check approved control
        if (
            decision.selected_control
            not in APPROVED_CONTROLS
        ):

            raise ValueError(
                "Control is not approved: "
                + decision.selected_control
            )

        # Check available controls
        if (
            decision.selected_control
            not in selector_input.available_controls
        ):

            raise ValueError(
                "Control is not available: "
                + decision.selected_control
            )

        # Check finding-control relationship
        expected = (
            self.expected_controls(
                selector_input
            )
        )

        if (
            expected
            and decision.selected_control
            not in expected
        ):

            raise ValueError(
                "Selected control does not "
                "match the observed finding."
            )

        return decision

    # -----------------------------------------------------
    # Fallback
    # -----------------------------------------------------

    def fallback_decision(
        self,
        selector_input: MitigationSelectorInput,
        reason: str,
    ) -> MitigationDecision:

        expected = (
            self.expected_controls(
                selector_input
            )
        )

        available = list(
            selector_input.available_controls
        )

        # First preference:
        # exact deterministic mapping
        for control in available:

            if control in expected:

                return MitigationDecision(

                    selected_control=control,

                    reason=(
                        "Deterministic safety "
                        "fallback selected the "
                        "approved control mapped "
                        "to the observed finding. "
                        + reason
                    ),

                    priority=0.9,

                    confidence=0.1,
                )

        # No exact mapping
        if not available:

            raise ValueError(
                "No mitigation controls available."
            )

        return MitigationDecision(

            selected_control=available[0],

            reason=(
                "Deterministic fallback selected "
                "the first approved available "
                "control because no exact mapping "
                "was found. "
                + reason
            ),

            priority=0.1,

            confidence=0.1,
        )

    # -----------------------------------------------------
    # Main selector
    # -----------------------------------------------------

    def select(
        self,
        selector_input: MitigationSelectorInput,
    ) -> MitigationDecision:

        total_start = perf_counter()

        # -------------------------------------------------
        # RAG
        # -------------------------------------------------

        rag_start = perf_counter()

        selector_input.retrieved_knowledge = (
            self.retrieve_knowledge(
                selector_input
            )
        )

        rag_time = (
            perf_counter()
            - rag_start
        )

        # -------------------------------------------------
        # Build prompt
        # -------------------------------------------------

        prompt_start = perf_counter()

        prompt = self.build_prompt(
            selector_input
        )

        prompt_time = (
            perf_counter()
            - prompt_start
        )

        # -------------------------------------------------
        # LLM
        # -------------------------------------------------

        llm_start = perf_counter()

        llm_success = False
        fallback_used = False
        llm_error = None

        try:

            response = (
                self.llm_client.generate_json(
                    prompt
                )
            )

            llm_success = True

            decision = (
                self.validate_decision(
                    response,
                    selector_input,
                )
            )

            llm_time = (
                perf_counter()
                - llm_start
            )

            total_time = (
                perf_counter()
                - total_start
            )

            self.last_metrics = {

                "rag_time_seconds":
                    round(
                        rag_time,
                        6
                    ),

                "prompt_build_time_seconds":
                    round(
                        prompt_time,
                        6
                    ),

                "llm_time_seconds":
                    round(
                        llm_time,
                        6
                    ),

                "total_time_seconds":
                    round(
                        total_time,
                        6
                    ),

                "llm_called":
                    True,

                "llm_success":
                    True,

                "fallback_used":
                    False,

                "llm_error":
                    None,

                "retrieved_documents":
                    len(
                        selector_input
                        .retrieved_knowledge
                    ),
            }

            return decision

        except Exception as error:

            llm_time = (
                perf_counter()
                - llm_start
            )

            fallback_used = True

            llm_error = (
                f"{type(error).__name__}: "
                f"{error}"
            )

            print(
                "[Mitigation Selector Warning]",
                llm_error,
            )

            # ---------------------------------------------
            # Deterministic fallback
            # ---------------------------------------------

            decision = (
                self.fallback_decision(

                    selector_input,

                    reason=(
                        "The LLM decision was "
                        "invalid or unavailable."
                    ),
                )
            )

            total_time = (
                perf_counter()
                - total_start
            )

            self.last_metrics = {

                "rag_time_seconds":
                    round(
                        rag_time,
                        6
                    ),

                "prompt_build_time_seconds":
                    round(
                        prompt_time,
                        6
                    ),

                "llm_time_seconds":
                    round(
                        llm_time,
                        6
                    ),

                "total_time_seconds":
                    round(
                        total_time,
                        6
                    ),

                "llm_called":
                    True,

                "llm_success":
                    False,

                "fallback_used":
                    True,

                "llm_error":
                    llm_error,

                "retrieved_documents":
                    len(
                        selector_input
                        .retrieved_knowledge
                    ),
            }

            return decision