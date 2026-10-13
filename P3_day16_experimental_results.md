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

The P3 narrative originally described an ablation experiment with:

- Study: `phase3_ablation`
- Same initial state across configurations: `True`
- Maximum tests: `3`
- Maximum LLM calls: `3`
- Maximum planner time budget: `30.0` seconds
- Three candidate tests described as selected/executed per configuration.
- The same initial scenario was used for A, B, C, and D.

Selected tests:

```text
permission_test
tool_access_test
memory_access_test
```

The narrative attributes the result to:

```text
results/phase3_ablation_day12.json
```

---

## 5. Latest A/B/C/D Results

The following figures are retained as a historical narrative record. They do not match the saved `phase3_ablation_day12.json` artifact currently in the repository and are not treated as verified raw metrics.

| Config | Mode | Fallback | LLM Calls | Selected Tests | Total Time |
|---|---|---:|---:|---|---:|
| A | `llm_only` | Yes | 3 | permission, tool access, memory access | 33.259872 s |
| B | `llm_rag` | Yes | 3 | permission, tool access, memory access | 9.740067 s |
| C | `llm_chain` | Yes | 3 | permission, tool access, memory access | 1.031228 s |
| D | `llm_rag_chain` | Yes | 3 | permission, tool access, memory access | 1.358138 s |

The saved JSON instead reports two selected tests and two completed sandbox executions per configuration, three LLM calls, fallback after HTTP 429, and `budget_exhausted` for all four modes. The raw artifact takes precedence for current reported results.

### Saved artifact evidence

| Artifact | Configuration outcomes |
|---|---|
| `results/phase3_ablation_day12.json` | A-D: 2/3 tests selected, 2 completed sandbox executions, 3 LLM calls, fallback after HTTP 429, `budget_exhausted`. |
| `results/phase3_ablation_gemini_20261011.json` | A/D: one non-fallback test and `budget_exhausted` at 30.952956 s / 31.074635 s; B/C: 3 fallback tests, completed after HTTP 503 / 503+504, at 12.634323 s / 23.548119 s. |

Neither saved artifact is a valid successful non-fallback A/B/C/D comparison. The earlier `*_before_*` JSON files are retained historical snapshots.

The derived `results/phase3_ablation_evaluation_20261011.json` names the Gemini runner artifact as its source, reports A=0.3333 and B/C/D=1.0 selection accuracy, and records fallback-decision counts A=0, B=2, C=3, D=3. It marks the performance comparison invalid and says the accuracy was copied rather than independently validated. These values are not evidence of comparative accuracy. The other narrative fallback counts (A=2, B=0, C=1, D=1) remain unresolved against the saved evaluation record.

---

## 6. LLM Availability and Fallback Behavior

The saved artifacts record Gemini service/quota failures, including:

- HTTP 503 `UNAVAILABLE`.
- HTTP 429 quota/rate-limit behavior.

In `phase3_ablation_day12.json`, fallback was used for A-D. In `phase3_ablation_gemini_20261011.json`, only B and C used fallback; A and D each made one non-fallback decision before exhausting their time budget. The narrative claim that all four used fallback applies to the unreconciled report figures above and is not confirmed by that artifact.

This is an important experimental condition.

The run therefore demonstrates that:

- The planner handles LLM unavailability without crashing.
- The configured A/B/C/D modes remain executable.
- The fallback path produces valid planner outputs.
- The controlled tests can still be executed and recorded.

However, this run does **not** provide a valid comparison of successful LLM-only, RAG-enhanced, chain-context-enhanced, and combined reasoning.

### Important limitation

The observed timing differences must not be interpreted as evidence that one ablation configuration is inherently faster or better.

The saved runs do not isolate the intended successful LLM reasoning differences: one is entirely fallback-affected, and the other mixes incomplete non-fallback A/D with fallback B/C.

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

Selection accuracy is not available as a valid comparative metric in the saved runs.

Reason:

- `phase3_ablation_day12.json` used fallback in every configuration.
- `phase3_ablation_gemini_20261011.json` did not complete comparable non-fallback decisions across all four modes.
- The saved artifacts therefore do not produce a successful-LLM selection comparison between A, B, C, and D.

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

This distinction is important when interpreting the 33.259872-second narrative value for configuration A. That value does not match the saved JSON artifact and remains unverified; the verified 20261011 artifact records 30.952956 seconds for A and 31.074635 seconds for D.

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

The core P3 planner/RAG mechanisms and regression coverage are implemented. The planner tracks execution time and stops subsequent operations, but saved A/D totals exceed the configured 30 seconds; Section 18's “planner respects the budget” criterion remains partial pending clarification. The specification does not separately mandate hard cancellation. A valid live A/B/C/D comparison remains unresolved. Section 18's multi-agent disruption criterion is also unverified: Day 14 tests chain triggering and validation, not mitigation or replay disruption.

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
| Adaptive test and LLM-call budget cutoffs | Complete; 10 focused tests passed after the latest change |
| Tracked adaptive execution-time budget | Complete; tests prevent subsequent work after the tracked budget expires |
| Planner respects configured time budget | Partial; saved A/D totals exceed 30 seconds and in-flight overrun semantics are undefined |
| V01-V12 AI/P4 adapter and backend selection | Complete; exact test mapping covered for all 12 IDs and all 12 local sandbox executions pass |
| Chain reasoning | Complete |
| Residual-chain reasoning | Complete |
| Multi-agent planner reasoning and V11->V10 chain triggering | Complete; focused planner and sandbox suites pass |
| Multi-agent validation and disruption | Partial; chain order is validated, but no V11->V10 mitigation/replay disruption result is recorded |
| Agent-specific tool permission enforcement | Complete; registry allow/deny/unassigned cases covered |
| Trust/delegation reasoning | Complete |
| Ablation tests | 11 passed |
| Multi-agent/E2E tests | 19 passed |
| Historical full AI-engine regression | 248 passed at the time of this report |
| Full AI-engine regression on latest worktree | 264 passed; one warning |
| Focused AI-engine budget/adapter/multi-agent/ablation slice | 62 passed |
| Full sandbox regression | 290 passed |
| Full backend regression | 149 passed |
| Integrated API/planner/sandbox/validator test | 1 passed with deterministic LLM responses |
| Fallback/failure experiment records | Complete as records; not valid comparative evidence |
| Canonical experiment-results reconciliation | Partial; narrative-only Day 12 values remain unverified |
| Comparative successful-LLM ablation | Pending Gemini availability |

---

## 16. Recommended Next Step

Do not treat the current fallback run as the final comparative A/B/C/D result.

Before rerunning the ablation, verify Gemini model/service availability and sufficient quota for at least 12 successful planner requests (three per configuration), plus retries. Do not remove or overwrite the existing failure and fallback artifacts.

If Gemini becomes available, rerun the same A/B/C/D experiment with:

- the same initial state,
- the same budget,
- the same candidate/test pool,
- the same evaluation procedure,
- and the same result-recording format.

The located Phase 3 specification defines a tracked 30-second budget and `budget_exhausted` outcome, not hard cancellation of an in-flight request. If the project requires a strict wall-clock deadline beyond that specification, define it as a separate acceptance requirement before implementing cancellation.

This preserves comparability between the fallback experiment and any later successful-LLM experiment.
