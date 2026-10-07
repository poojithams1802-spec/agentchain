# AgentChain Phase 3 --- P3 Planner/RAG Methodology

## 1. Purpose

This document records the Person 3 (P3) methodology for the AgentChain
Phase 3 work.

The Phase 3 research objective is to evaluate whether a knowledge-guided
adaptive agent security system can discover, evaluate, and disrupt
multi-step compositional attack chains efficiently under testing
constraints, compared with static and simpler planning strategies.

All experiments are restricted to the intentionally vulnerable
AgentChain sandbox using controlled synthetic vulnerabilities, synthetic
data, controlled agents, mock APIs, simulated security failures,
defensive validation, and local experiments.

The planner is restricted to approved sandbox tests and controls.

## 2. P3 Scope

P3 owns the AI/RAG/adaptive-reasoning layer:

-   Security RAG
-   Candidate generation
-   Adaptive test selection
-   Testing-budget reasoning
-   Information-gain scoring
-   Chain-context reasoning
-   Ablation configurations
-   LLM fallback
-   Multi-agent reasoning

P3 does not own sandbox execution, mitigation application, replay,
validation, persistence, or frontend visualization.

## 3. Planner Architecture

The Phase 3 planner operates within the project architecture:

React Dashboard → FastAPI Backend → AI/RAG/Adaptive Planner → Controlled
Sandbox / Validator → MongoDB → React Dashboard

For the P3 layer, the main reasoning flow is:

Finding and current state → Security knowledge / RAG → Candidate tests →
Candidate scoring → Budget-aware selection → Controlled sandbox test →
Updated finding/state → Chain-context reasoning → Next-test selection

Phase 3 extends the planner with chain state, testing budgets, adaptive
candidate scoring, ablation configuration, and multi-agent context.

## 4. Security RAG Methodology

The planner uses a local security knowledge base and a retriever to
provide security-relevant context.

Phase 3 expanded the knowledge base with additional areas including:

-   Indirect prompt injection
-   Sensitive data exposure
-   Prompt-injection validation
-   Multi-step attack chains
-   Chain dependencies and validation
-   Residual chain steps and disruption
-   Adaptive testing budgets
-   Information gain and testing cost
-   Authorization and least privilege
-   Tool authorization and allowlisting
-   Memory validation and untrusted information

The RAG output is treated as contextual evidence for planner reasoning.
Retrieved knowledge is not itself treated as a security finding or
validated evidence.

The verified knowledge-base state reached 27 entries after the Phase 3
RAG expansion, including KB025, KB026, and KB027.

## 5. Candidate Generation and Adaptive Selection

The planner considers available approved sandbox tests together with:

-   current findings
-   finding severity
-   finding confidence
-   finding evidence
-   previously executed tests
-   available tests
-   chain state
-   candidate relevance
-   expected information gain
-   testing cost
-   remaining budget

Candidate scoring uses the implemented weighted components:

-   relevance
-   severity
-   confidence
-   expected information gain
-   testing-cost efficiency

The resulting score is used to rank candidates before budget-aware
selection.

The planner must select only approved sandbox actions.

## 6. Adaptive Testing Budget

The Phase 3 budget model tracks:

-   maximum tests
-   maximum LLM calls
-   maximum execution time
-   tests used
-   LLM calls used
-   time used

The example Phase 3 budget defined by the project documentation is:

-   maximum tests = 5
-   maximum LLM calls = 3
-   time budget = 30 seconds

When the available budget is exhausted, the planner/experiment flow
supports the `budget_exhausted` state.

## 7. Attack-Chain Reasoning

P3 represents attack-chain context for planner reasoning rather than
executing chains.

The implemented planner supports chain context including:

-   chain identifier
-   ordered steps
-   dependencies
-   completed steps
-   residual steps
-   next residual step
-   residual risk
-   validation result

The planner also contains five initial chain combinations:

### CHAIN_A

Authorization → Tool Access

### CHAIN_B

Authorization → Tool Access → Memory

### CHAIN_C

Tool Access → Prompt Injection → Data Exposure

### CHAIN_D

Authorization → Tool Access → Memory → Delegation

### CHAIN_E

Prompt Injection → Data Exposure → Unsafe Delegation

P4 owns actual chain execution and validation.

## 8. Residual-Chain Reasoning

After controlled execution and validation, the planner can reason about
residual chain state.

Explicit residual steps supplied by validation are preferred.

When explicit residual steps are unavailable, the planner can derive
remaining steps from the ordered chain steps and completed steps.

The planner uses this information to identify:

-   remaining attack-chain steps
-   next residual step
-   residual risk
-   chain-disruption context

The planner does not invent residual steps that are not supported by the
supplied chain state.

## 9. Ablation Methodology

Phase 3 defines four planner configurations:

  Configuration   Definition
  --------------- ----------------------------------
  A               LLM only
  B               LLM + RAG
  C               LLM + attack-chain context
  D               LLM + RAG + attack-chain context

The same controlled scenarios should be used across configurations
whenever possible.

The purpose is to isolate the contribution of RAG and attack-chain
context rather than to compare unrelated planner implementations.

The intended comparison dimensions include:

-   selection accuracy
-   chain discovery rate
-   mitigation success
-   chain disruption
-   tests required
-   LLM calls
-   latency
-   validation rate
-   residual vulnerable steps

A previous real Day 12 run experienced Gemini 503/429 availability/quota
failures and therefore should not be interpreted as evidence that one
configuration outperformed another. The fallback behavior itself is a
relevant failure-case observation.

## 10. LLM Fallback

The planner includes deterministic fallback behavior for situations
where the LLM is unavailable or fails.

Fallback behavior is important for maintaining controlled experiment
execution and reproducibility when external model availability changes.

Observed Phase 2 and Phase 3 testing included Gemini 503/429 failure
conditions with fallback activation.

Fallback results should be reported explicitly rather than presented as
successful LLM reasoning.

## 11. Multi-Agent Reasoning

Phase 3 adds multi-agent planner context containing:

-   enabled state
-   agents
-   allowed interactions
-   trust context
-   shared-memory context

The Day 14 reasoning layer evaluates planner-side security signals
related to:

-   untrusted agents
-   cross-agent trust boundaries
-   delegation
-   unauthorized delegation
-   privilege propagation
-   shared-memory access
-   cross-agent context leakage

P3 provides reasoning and security signals. P4 owns the controlled
multi-agent sandbox, communication execution, and validation.

## 12. Verification Evidence

Recent targeted P3 verification produced:

-   Adaptive-chain E2E: 10 tests passed
-   RAG/chain integration: 6 tests passed
-   Day 13 multi-agent planner + Day 14 trust/delegation: 9 tests passed
-   Ablation configuration verification: A/B/C/D matched the Phase 3
    definitions

Earlier Phase 3 verification also covered:

-   adaptive-loop behavior
-   budget-aware planner behavior
-   candidate scoring
-   RAG expansion
-   chain-context reasoning
-   chain combinations
-   ablation planner behavior
-   ablation experiment runner
-   multi-agent context
-   trust/delegation reasoning

## 13. Research Interpretation

The current evidence supports the claim that AgentChain has a controlled
planner framework implementing:

-   knowledge-guided reasoning
-   adaptive test selection
-   budget-aware selection
-   compositional chain context
-   ablation configurations
-   multi-agent security reasoning
-   LLM fallback

The evidence does not justify claiming general real-world security
effectiveness.

The Phase 2 baseline documentation explicitly cautions against
generalizing controlled three-scenario results, including the reported
100% selection accuracy figures.

Therefore, final results should distinguish:

1.  implementation verification,
2.  controlled sandbox experiment results,
3.  fallback/failure-case observations,
4.  research conclusions.

## 14. Reproducibility

Experiments should preserve:

-   configuration ID
-   experiment ID supplied by P2
-   scenario ID
-   selected tests
-   findings
-   budget configuration
-   budget usage
-   LLM usage
-   fallback state
-   execution results
-   chain context
-   validation results
-   timing information

P3 does not generate production experiment IDs in the integrated
workflow.

## 15. Final P3 Research Position

The intended research story is:

Traditional static testing → fixed test sequence → limited attack-chain
context

AgentChain → security knowledge → current state → chain context →
testing budget → adaptive planner → next-test selection → controlled
sandbox → multi-step attack chain → mitigation / replay → chain
validation → chain disruption → research metrics

The conservative project claim is that AgentChain is a controlled,
knowledge-guided framework for adaptive discovery, validation,
mitigation, and evaluation of compositional attack chains in agentic AI
systems.
