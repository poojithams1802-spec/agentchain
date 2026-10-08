# P3 Day 16 — Experimental Results

## 1. Purpose

This document records the Phase 3 Day 16 experimental evidence produced by P3 for the AgentChain planner/RAG work.

The objective is to document:

- A/B/C/D planner ablation configurations.
- Controlled execution of the ablation experiment.
- LLM fallback behavior.
- Adaptive planner implementation verification.
- Multi-agent and end-to-end verification.
- Full AI-engine regression status.
- Reproducibility information.
- Limitations and conservative research interpretation.

The experiments are intended for the controlled AgentChain sandbox and are not evidence of real-world security effectiveness.

---

## 2. P3 Research Scope

P3 owns the planner and reasoning components used in Phase 3, including:

- Security knowledge retrieval (RAG).
- Candidate generation and adaptive test selection.
- Testing-budget reasoning.
- Information-gain-aware candidate scoring.
- Attack-chain context reasoning.
- Residual-chain reasoning.
- Ablation configurations.
- LLM fallback handling.
- Multi-agent reasoning and trust/delegation context.

The Phase 3 research question is:

> Can a knowledge-guided adaptive agent security system discover, evaluate, and disrupt multi-step compositional attack chains efficiently under testing constraints, compared with static and simpler planning strategies?

The results in this document should be interpreted within the controlled sandbox scope defined for AgentChain.

---

## 3. Ablation Configurations

The Phase 3 ablation study contains four planner configurations.

| Configuration | Name | LLM | RAG | Attack-chain context |
|---|---|---:|---:|---:|
| A | `llm_only` | Yes | No | No |
| B | `llm_rag` | Yes | Yes | No |
| C | `llm_chain` | Yes | No | Yes |
| D | `llm_rag_chain` | Yes | Yes | Yes |

The intended comparison is to isolate the contribution of:

1. Security knowledge retrieval.
2. Attack-chain context.
3. The combination of RAG and attack-chain context.

The configuration definitions were independently verified as:

```text
A llm_only       False False
B llm_rag        True  False
C llm_chain      False True
D llm_rag_chain  True  True
```

The two boolean values represent:

```text
use_rag
use_chain_context
```

---

## 4. Experimental Setup

The latest recorded ablation experiment used:

- Study: `phase3_ablation`
- Same initial state across configurations: `True`
- Maximum tests: `3`
- Maximum LLM calls: `3`
- Maximum planner time budget: `30.0` seconds
- Three candidate tests were selected/executed per configuration.
- The same initial scenario was used for A, B, C, and D.

Selected tests:

```text
permission_test
tool_access_test
memory_access_test
```

The experiment result was saved to:

```text
results/phase3_ablation_day12.json
```

---

## 5. Latest A/B/C/D Results

The latest reproducible run produced the following record.

| Config | Mode | Fallback | LLM Calls | Selected Tests | Total Time |
|---|---|---:|---:|---|---:|
| A | `llm_only` | Yes | 3 | permission, tool access, memory access | 33.259872 s |
| B | `llm_rag` | Yes | 3 | permission, tool access, memory access | 9.740067 s |
| C | `llm_chain` | Yes | 3 | permission, tool access, memory access | 1.031228 s |
| D | `llm_rag_chain` | Yes | 3 | permission, tool access, memory access | 1.358138 s |

All four configurations used the same initial state and selected the same three tests.

Execution completed successfully for the selected sandbox tests.

---

## 6. LLM Availability and Fallback Behavior

During the ablation execution, Gemini requests encountered service/quota failures, including:

- HTTP 503 `UNAVAILABLE`.
- HTTP 429 quota/rate-limit behavior.

As a result, the planner's deterministic fallback path was used for all four configurations.

This is an important experimental condition.

The run therefore demonstrates that:

- The planner handles LLM unavailability without crashing.
- The configured A/B/C/D modes remain executable.
- The fallback path produces valid planner outputs.
- The controlled tests can still be executed and recorded.

However, this run does **not** provide a valid comparison of successful LLM-only, RAG-enhanced, chain-context-enhanced, and combined reasoning.

### Important limitation

The observed timing differences must not be interpreted as evidence that one ablation configuration is inherently faster or better.

All four configurations used fallback behavior, and therefore the run does not isolate the intended successful LLM reasoning differences.

In particular:

```text
A: 33.259872 s
B:  9.740067 s
C:  1.031228 s
D:  1.358138 s
```

These values are recorded for reproducibility only.

---

## 7. Selection Accuracy

Selection accuracy was not available as a valid comparative metric in this run.

Reason:

- Gemini reasoning was unavailable.
- The deterministic fallback selected the same predefined tests across configurations.
- The experiment therefore did not produce an independent successful-LLM selection comparison between A, B, C, and D.

Consequently, no claim is made that RAG or attack-chain context improved selection accuracy in this experiment.

---

## 8. Adaptive Testing Budget

The experiment used the Phase 3 testing-budget model:

```text
Maximum tests:       3
Maximum LLM calls:   3
Maximum time:       30 seconds
```

The planner tracks:

- Tests used.
- LLM calls used.
- Time used.
- Remaining budget.
- Candidate tests.
- Selected tests.
- Selection reasoning.
- Budget exhaustion status.

The experiment runner checks the budget before and after planning/execution steps.

The 30-second value is treated as a tracked planning/testing budget rather than a hard operating-system timeout on an external LLM request. A blocking API request can therefore cause an individual measured run to exceed the nominal budget before the runner can update the accounting.

This distinction is important when interpreting the 33.259872-second result for configuration A.

---

## 9. Implementation Verification

The following P3 verification evidence was completed before this results record.

### Ablation planner tests

```text
tests/test_ablation_planner.py
tests/test_ablation_experiment_runner.py

Result:
11 passed
```

These tests verify the ablation configuration behavior and experiment-runner integration.

### Multi-agent and end-to-end tests

The combined verification covered:

```text
tests/test_day13_multi_agent_planner.py
tests/test_day14_trust_delegation.py
tests/test_end_to_end_adaptive_chain.py

Result:
19 passed
```

This verifies the P3 multi-agent reasoning, trust/delegation reasoning, and adaptive end-to-end chain behavior.

### Full AI-engine regression

```text
python -m pytest

Result:
248 passed
0 failed
```

Therefore, the P3 Day 11/Day 16 changes were regression-tested against the full AI-engine test suite available at the time of verification.

---

## 10. Multi-Agent Reasoning Verification

P3 implemented planner-side multi-agent reasoning context for:

- Agent identities and roles.
- Trust relationships.
- Allowed interactions.
- Shared memory/context.
- Delegation requests.
- Cross-agent trust boundaries.
- Unauthorized delegation.
- Low-trust delegation.
- Privilege propagation.
- Cross-agent memory/context leakage.

The planner produces reasoning context and recommended controlled checks.

Execution and enforcement remain outside P3's ownership and are handled by the sandbox/execution components.

The multi-agent and trust/delegation tests passed as part of the 19-test combined verification above.

---

## 11. Attack-Chain Reasoning Verification

P3 supports five representative chain combinations:

```text
CHAIN_A
authorization -> tool access

CHAIN_B
authorization -> tool -> memory

CHAIN_C
tool access -> prompt injection -> data exposure

CHAIN_D
authorization -> tool -> memory -> delegation

CHAIN_E
prompt injection -> data exposure -> delegation
```

The planner uses chain context when the selected configuration enables it.

Residual-chain reasoning tracks completed steps and identifies remaining chain steps when validation information is available.

The planner is designed not to invent residual steps when explicit or derivable chain information is unavailable.

---

## 12. Research Interpretation

The latest ablation run supports the following conclusions.

### Supported conclusions

1. The four intended Phase 3 planner configurations are implemented and distinguishable.
2. The A/B/C/D configurations can be executed through the common ablation runner.
3. The planner can operate when Gemini is unavailable by using deterministic fallback behavior.
4. The same initial state can be used across the four configurations.
5. Testing-budget information is tracked during adaptive planning.
6. The P3 implementation passes its targeted ablation, multi-agent, end-to-end, and full AI-engine regression tests.
7. The latest fallback run is reproducible and can be included as a documented failure-case experiment.

### Conclusions not supported by this run

This run does not establish that:

- RAG improves selection accuracy.
- Attack-chain context improves selection accuracy.
- RAG plus chain context is superior to the other configurations.
- One configuration is inherently faster than another.
- The planner provides real-world security effectiveness.
- The LLM achieves a particular general selection-accuracy percentage.

These claims require successful comparable LLM-backed runs and controlled evaluation metrics.

---

## 13. Reproducibility Record

The following information is sufficient to identify the latest recorded experiment:

```text
Study:
phase3_ablation

Initial state:
same across A/B/C/D

Configurations:
A = llm_only
B = llm_rag
C = llm_chain
D = llm_rag_chain

Budget:
max_tests = 3
max_llm_calls = 3
max_time_seconds = 30.0

Selected tests:
permission_test
tool_access_test
memory_access_test

Fallback:
True for A/B/C/D

LLM calls:
3 for A/B/C/D

Result file:
results/phase3_ablation_day12.json
```

---

## 14. Final P3 Position

P3's Phase 3 planner/RAG implementation is functionally complete and regression-tested.

The implementation provides:

- Knowledge-guided retrieval.
- Adaptive candidate selection.
- Testing-budget reasoning.
- Attack-chain reasoning.
- Residual-chain reasoning.
- Ablation configuration support.
- LLM fallback.
- Multi-agent reasoning.
- Trust/delegation reasoning.
- End-to-end planner integration.

The latest A/B/C/D experiment should be classified as a **fallback/failure-case experiment**, not as the primary comparative ablation result.

The appropriate research statement is therefore:

> AgentChain implements a controlled, knowledge-guided framework for adaptive discovery, validation, mitigation, and evaluation of compositional attack chains in agentic AI systems. The current P3 evidence verifies the planner architecture, adaptive mechanisms, ablation infrastructure, multi-agent reasoning, fallback behavior, and regression stability. A successful Gemini-backed A/B/C/D run is required before making comparative claims about the effect of RAG and attack-chain context on planner performance.

---

## 15. Day 16 Deliverable Status

| P3 Deliverable | Status |
|---|---|
| Planner/RAG methodology | Complete |
| A/B/C/D ablation configurations | Complete |
| Ablation runner | Complete |
| Adaptive budget tracking | Complete |
| Chain reasoning | Complete |
| Residual-chain reasoning | Complete |
| Multi-agent reasoning | Complete |
| Trust/delegation reasoning | Complete |
| Ablation tests | 11 passed |
| Multi-agent/E2E tests | 19 passed |
| Full AI-engine regression | 248 passed |
| Fallback experiment | Complete |
| Experimental-results record | Complete |
| Comparative successful-LLM ablation | Pending Gemini availability |

---

## 16. Recommended Next Step

Do not treat the current fallback run as the final comparative A/B/C/D result.

Before rerunning the ablation, verify that Gemini is available and that sufficient quota exists for the required LLM calls.

If Gemini becomes available, rerun the same A/B/C/D experiment with:

- the same initial state,
- the same budget,
- the same candidate/test pool,
- the same evaluation procedure,
- and the same result-recording format.

This preserves comparability between the fallback experiment and any later successful-LLM experiment.
