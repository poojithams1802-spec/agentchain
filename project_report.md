# AgentChain: Controlled Adaptive Attack-Chain Discovery and Evaluation

## 1. Title and Abstract

**AgentChain: A Knowledge-Guided Framework for Controlled Red-Teaming of Agentic AI Systems**

AgentChain is a research prototype for adaptive security-test selection, controlled vulnerability discovery, compositional attack-chain validation, mitigation replay, and evaluation in an intentionally vulnerable agentic-AI sandbox. Its implementation combines a React dashboard, a FastAPI orchestration and persistence layer, an AI planner with local security-knowledge retrieval and deterministic fallback, and deterministic sandbox tests, validators, and mitigation controls.

The reported experiments demonstrate selected controlled behaviors, not real-world security effectiveness. In Day 7, static and adaptive methods achieved the same reported discovery and validation outcomes under equal test budgets, while the adaptive run used more LLM calls and had higher measured execution time. Day 12 contains two separate planner-ablation records, including a fallback-affected run with Gemini HTTP 503 and 429 failures; neither record establishes comparative superiority. The controlled two-agent scenario validated the V11 cross-agent trust → V10 unsafe delegation chain. Four correct-control replay chains were disrupted, but eight vulnerable steps remained. The experiments therefore support system functionality in the stated sandbox and leave comparative and external effectiveness claims unestablished.

## 2. Introduction

Agentic systems can combine tool access, permissions, memory, delegated operations, and interactions among agents. A weakness in one component can be composed with later weaknesses. AgentChain provides an integrated environment in which a planner can select approved tests, sandbox components can reproduce controlled findings, and validation and replay components can evaluate ordered chains.

The project is described as a research dashboard and controlled sandbox. The implementation and experiments focus on bounded local scenarios using synthetic or deterministic behavior. This report distinguishes implementation facts from measured results and from future proposals; the existence of a framework component is not evidence that it improves security outcomes.

## 3. Problem Statement and Motivation

A fixed test sequence is straightforward to reproduce but does not adapt its next test to the findings and state already observed. Conversely, adaptive planning introduces additional components—retrieval, candidate scoring, chain context, budget tracking, and LLM availability—that require separate measurement. A planner's choice of tests also does not itself establish that a vulnerability was discovered, that a chain was validated, or that a mitigation removed vulnerabilities.

AgentChain addresses this evaluation problem by separating:

- planner decisions and fallback observations;
- deterministic sandbox execution and finding validation;
- chain-level mitigation, same-chain replay, and residual-step reporting; and
- software regression evidence.

This separation is necessary to avoid treating planner selection accuracy, chain validation, chain disruption, and complete vulnerability mitigation as interchangeable outcomes.

## 4. Research Objectives and Questions

The controlled evaluation considers:

1. Under an equal three-test budget, do the Day 7 static and adaptive runs produce the same discovery and validation results, and what LLM-call and execution-time differences were recorded?
2. What sequence and fallback observations were recorded for the four Day 12 planner configurations under a common initial scenario?
3. Can the controlled two-agent sandbox scenario represent and validate V11 cross-agent trust followed by V10 unsafe delegation?
4. In same-attack chain replay, which steps are blocked, which chains are disrupted, and which vulnerable steps remain?

These questions are descriptive. The available records do not provide repeated-sample statistical comparisons or establish that adaptive planning, RAG, or chain context is superior.

## 5. Proposed AgentChain Framework

The research concept is an iterative loop:

**Current findings and state → security knowledge and chain context → candidate tests → adaptive selection under budgets → controlled sandbox execution → updated state and findings → chain validation → mitigation and same-attack replay → recorded metrics.**

The implementation realizes parts of this loop across distinct components. The P3 planner retrieves knowledge (when enabled), builds and ranks candidates, requests and validates an LLM decision, and can fall back to a deterministic candidate choice. The P4 sandbox and validator execute and check controlled tests and chains. Mitigation utilities apply registered controls and replay the same chain. Backend orchestration and persistence connect these components to experiment records and the frontend.

This is a framework description, not a claim of validated superiority. The later Day 12 P3 experiment is explicitly fallback-affected, and the earlier P4 positional sequence agreement does not establish comparative successful-LLM accuracy.

## 6. System Architecture and Component Responsibilities

| Component | Observed implementation responsibility |
|---|---|
| React/Vite frontend | Dashboard and experiment views for experiment creation, history/details, logs, findings, chains, analytics, and mitigation-related pages; API calls are made through an Axios client |
| FastAPI backend | Experiment and scenario routes, orchestration of planner and sandbox interfaces, mitigation/replay routes, analytics, and persistence coordination |
| MongoDB access layer | Provides the backend database client and collections used for experiment, finding, chain, evaluation, mitigation, and agent-state records |
| AI engine / P3 | Planner input/decision schemas, adaptive planning, retrieval, candidate scoring, ablation configuration, budget accounting, LLM integration, and planner fallback |
| Sandbox / P4 | Deterministic vulnerability test functions, allowed-test execution, registered chain definitions, chain validation, local multi-agent scenario execution, defensive controls, and replay |
| Evaluation utilities | Normalize and summarize experiment records, calculate supported metrics, and mark planner-only execution-dependent metrics as N/A where applicable |

The code-level flow for integrated adaptive experiments is frontend → FastAPI → Python planner and sandbox interfaces → persistence, with API responses returned to the frontend. The API contract documents planner and sandbox calls as internal Python integration contracts rather than separate `/ai/plan` or `/sandbox/test` FastAPI endpoints.

**Documentation discrepancy:** `API_CONTRACT.md` describes a baseline set of implemented endpoints and labels its Phase 2 mitigation endpoints as planned/not implemented. The current `backend/app/main.py` contains mitigation selection, application, replay, Phase 2 analytics, Phase 3 chain/ablation routes, and agent-state routes. This report records the implementation observed in code and flags the API-contract status as stale or incomplete; it does not infer that every route has been tested or reconcile the documentation change.

## 7. Controlled Sandbox and Vulnerability Scenarios

The sandbox executor dispatches approved test names to deterministic scenario functions and attaches execution-cost metadata. The supported test map covers these controlled weaknesses:

| Identifier | Test area |
|---|---|
| V1 | Weak permission control |
| V2 | Unsafe tool access |
| V3 | Memory validation |
| V4 | Prompt injection |
| V5 | Indirect prompt injection |
| V6 | Sensitive-data exposure |
| V7 | Unsafe file operation |
| V8 | Context manipulation |
| V9 | Privilege propagation |
| V10 | Unsafe delegation |
| V11 | Cross-agent trust |
| V12 | Tool-parameter validation |

Registered attack-chain definitions specify ordered sandbox tests and dependencies. Representative chains include authorization → tool access, authorization → tool → memory, tool access → prompt injection → data exposure, authorization → tool → memory → delegation, and prompt injection → data exposure → delegation. These are controlled test compositions; their names and successful sandbox execution do not establish real-world exploitability.

The project README and P3 methodology describe the sandbox as isolated/local and not interacting with real external systems. The sandbox outcomes in this report are controlled results, not tests against production agents or external targets.

## 8. Adaptive Planning, Security RAG, and Testing Budget

The P3 planner receives findings, previously run and available tests, retrieved knowledge, chain state, multi-agent context, and testing-budget state through typed planner structures. Its RAG-enabled configurations retrieve from a local security knowledge file using a hybrid retriever. The retriever combines embedding-based semantic results with lexical keyword results using reciprocal-rank fusion; if embedding retrieval fails, it falls back to keyword retrieval. Retrieved text is context for planning and is not itself treated as a finding or validation evidence.

Candidate scoring in the implementation combines relevance, severity, confidence, expected information gain, and testing-cost efficiency. Budget-aware ranking can apply a cost penalty as tracked budget pressure increases. The planner checks test, LLM-call, and time budgets and validates that an LLM-selected test is available and has not already been executed. If planning fails, its deterministic fallback selects a highest-ranked unexecuted candidate where scoring data is available, otherwise the first unexecuted candidate.

The saved Day 12 runner artifacts use a three-test/three-LLM-call limit and a configured 30-second time budget where recorded. In `phase3_ablation_gemini_20261011.json`, configurations A and D report 30.952956 and 31.074635 seconds and end `budget_exhausted`. The tracked budget stops subsequent work but does not demonstrate a hard wall-clock cancellation deadline. The separate 33.259872-second narrative figure is not present in the saved JSON and remains unverified.

## 9. Attack-Chain Validation and Mitigation Replay

The chain validator executes the candidate sequence and checks execution status, expected finding, evidence, and dependency order. Its per-step validation rate is valid steps divided by returned steps; a chain is validated only when it has at least one step and every step is valid.

The chain-replay implementation clears mitigation state, executes the registered chain before mitigation, applies one registered control, then replays the same chain. A step is counted as blocked when the replay result marks mitigation as applied and evidence identifies `attack_blocked`. Steps not meeting that condition are residual vulnerable steps. A chain is considered disrupted if at least one step is blocked.

For the Day 15 correct-control replay, four of four chains were disrupted, four of twelve total steps were blocked, and eight vulnerable steps remained. Thus, chain disruption is not equivalent to complete vulnerability mitigation. The initial ineffective-control replay cases are also retained: CHAIN-A, CHAIN-C, and CHAIN-E were not disrupted by `memory_validation`; CHAIN-B and CHAIN-D were disrupted at `memory_access_test` but retained vulnerable steps. A wrong control may be applied while the attack chain continues and validation fails.

## 10. Multi-Agent Trust and Delegation Evaluation

The Day 14 controlled scenario uses a local two-agent registry with controlled communication and composes V11 cross-agent trust followed by V10 unsafe delegation. The scenario is considered triggered when both vulnerability checks report vulnerable and the controlled message is delivered; validation checks the expected chain identifier, communication status, vulnerability states, and ordered V11 → V10 steps.

The recorded result is that the controlled V11 → V10 chain was validated. This is a bounded synthetic scenario, not a test of a deployed multi-agent system or a broad population of agent interactions.

## 11. Experimental Design and Evaluation Metrics

The experiments use controlled settings and report only the outcomes recorded for each run. Day 7 compares a fixed-sequence static method with an adaptive method under an equal three-test budget. Day 12 has two separate planner-ablation records; they must not be merged:

| Day 12 configuration | Components |
|---|---|
| A (`llm_only`) | LLM only |
| B (`llm_rag`) | LLM + RAG |
| C (`llm_chain`) | LLM + attack-chain context |
| D (`llm_rag_chain`) | LLM + RAG + attack-chain context |

Principal metrics are interpreted as follows:

| Metric | Definition / scope |
|---|---|
| Tests and findings | Counts recorded by the relevant run; planner selection is not sandbox execution |
| Candidate/validated chains | Candidate chain count and count satisfying that experiment's validation condition |
| Average chain length | Arithmetic mean of recorded chain lengths within the stated experiment |
| Validation rate | For chain steps, valid steps divided by total returned steps; the Day 15 replay's final validation rate is a separate chain-level validation result |
| Day 12 Record 1 positional agreement | Positional matches with the expected sequence divided by compared positions; it is not comparative successful-LLM selection accuracy |
| Fallback-decision count | Number of individual planner decisions marked as fallback or identified by fallback reason text in that calculation |
| Fallback-used status | Boolean observation that fallback was used for a configuration in a run; not interchangeable with fallback-decision count |
| Chain-disruption rate | Chains with at least one blocked step divided by evaluated chains in the correct-control replay |
| Blocked-step rate | Blocked steps divided by total chain steps |
| Residual vulnerable steps | Steps not identified as blocked after replay |
| Timing | A reported measurement for its named scope; total run times, test execution costs, replay latency, and test-suite duration must not be conflated |

Unmeasured outcomes are N/A, not zero. The available experiments do not establish inferential significance.

## 12. Results and Discussion

### Day 7 static versus adaptive

| Metric | Static | Adaptive |
|---|---:|---:|
| Test budget | 3 | 3 |
| Tests executed | 3 | 3 |
| Findings | 3 | 3 |
| Candidate chains | 1 | 1 |
| Validated chains | 1 | 1 |
| Average chain length | 3 | 3 |
| Validation rate | 1.0 | 1.0 |
| LLM calls | 0 | 3 |
| Fallback | No | No |
| Measured execution time | Approximately 0.0000128 seconds | Approximately 0.0000824 seconds |

Both methods produced the same reported controlled discovery and validation outcome. Adaptive planning used three additional LLM calls and had higher measured execution time in this deterministic controlled run. The results do not establish adaptive superiority.

### Day 12 A/B/C/D saved runner records

The raw evidence and limits are detailed in [experimental_results.md](experimental_results.md). `phase3_ablation_day12.json` records two completed sandbox executions per mode, fallback after HTTP 429, three LLM calls, and `budget_exhausted` for A-D. `phase3_ablation_gemini_20261011.json` records one non-fallback test and budget exhaustion for A/D, while B/C completed three tests using fallback after HTTP 503/504. These records contain sandbox executions but do not form a valid successful-LLM four-way comparison. The older narrative positional-agreement and fallback-count figures are not traceable to a current raw artifact and remain unverified. Neither saved run establishes that RAG or chain context improved planner performance.

### Multi-agent, chain replay, and software testing

The controlled two-agent scenario validated V11 → V10. In the Day 15 correct-control replay, four of four chains were disrupted; across twelve chain steps, four were blocked and eight residual vulnerable steps remained. The chain-disruption rate was 100%, the blocked-step rate was 33.3%, and the average residual vulnerable steps per chain was 2.0. This result indicates interruption of each evaluated chain under the replay definition, not complete vulnerability mitigation.

Reported software testing evidence is separate from security outcomes:

| Software test suite | Result |
|---|---|
| Day 16 sandbox/evaluation suite | 44 passed; one dependency deprecation warning |
| Full sandbox regression | 290 passed; one warning |
| Backend full regression including integrated test | 149 passed; two warnings |
| Full AI-engine regression on latest worktree | 264 passed; one warning |
| Current focused AI-engine budget/adapter/multi-agent/ablation slice | 62 passed; one warning |
| Focused adaptive-loop tests after budget fix | 10 passed; one warning |
| Real planner/sandbox API integration test | 1 passed; deterministic LLM stub, no live Gemini call |

These test results support implementation regression status only; they are not measures of vulnerability discovery or security effectiveness.

## 13. Failure Cases and API Fallback Analysis

The initial replay with `memory_validation` was ineffective for CHAIN-A, CHAIN-C, and CHAIN-E, which were not disrupted. CHAIN-B and CHAIN-D were disrupted at `memory_access_test`, but residual vulnerable steps remained. They are not failed disruptions. The wrong-control replay demonstrates another failure mode: a control can be applied while no chain step is blocked, the chain continues, and replay validation fails.

The saved Day 12 JSON records preserve distinct failure evidence: one is all-fallback after HTTP 429 and budget-exhausted across A-D; the other has non-fallback but incomplete A/D and fallback/completed B/C after HTTP 503/504. Narrative-only fallback-decision counts and a second set of timings remain unverified because no matching raw record is present.

**Day 12 evidence reconciliation:** The repository contains `ai-engine/results/phase3_ablation_day12.json` and `phase3_ablation_gemini_20261011.json`; both declare `runner_scope: planner_plus_sandbox` and contain execution records. The first has two completed sandbox executions per configuration, all fallback after HTTP 429, and `budget_exhausted` for A-D. The second has one non-fallback test for A/D (both `budget_exhausted`) and three fallback tests for B/C (both completed, after HTTP 503/504). The derived evaluation JSON reports copied, independently unvalidated accuracy and explicitly marks the comparison invalid. Thus the saved records include sandbox execution, but neither is a valid successful-LLM four-way comparison. The separate narrative figures in `P3_day16_experimental_results.md` do not match these artifacts and remain unverified historical claims. The API-contract route-status discrepancy also remains; code presence does not prove every route is tested.

## 14. Limitations and Threats to Validity

- **Controlled scope:** Experiments use intentionally vulnerable, synthetic/local sandbox behaviors and do not demonstrate real-world security effectiveness.
- **Small evaluation set:** Day 7 is a controlled comparison at a three-test budget; Day 12 uses one common scenario across four configurations per record; the multi-agent result covers one stated V11 → V10 scenario; and the correct-control replay covers four chains.
- **Fallback confounding:** Saved Day 12 artifacts are either all-fallback and budget-exhausted or mix non-fallback incomplete and fallback complete configurations; neither compares successful LLM reasoning across A/B/C/D.
- **Metric interpretation:** Positional sequence agreement, step validation, chain disruption, blocked-step rate, and vulnerability mitigation are different concepts. A 100% chain-disruption rate does not imply all vulnerabilities were removed.
- **Performance scope:** P3 Day 12 total times are fallback-affected observations; strict budget enforcement and relative performance conclusions are not supported. Other unrecorded performance measurements are N/A.
- **Documentation and evidence discrepancies:** The API contract's status for Phase 2 routes differs from current backend route code. The P3 Day 16 narrative metrics conflict with the present raw JSON; the raw artifacts have been inspected and the conflicting narrative figures remain unverified.
- **No statistical generalization:** No statistical significance, confidence interval, model-version comparison, or broad performance estimate is available.

## 15. Phase 3 Definition of Done Status

Statuses are based on repository implementation, focused tests, saved experiment artifacts, and the commands recorded for this handoff. “Complete” describes the scoped software deliverable, not security effectiveness.

| Phase 3 deliverable | Status | Evidence / remaining boundary |
|---|---|---|
| Local knowledge retrieval, candidate scoring, approved-test planner, chain and multi-agent context | Complete | Implemented in P3; latest full AI-engine suite passed 264, including latest adapter coverage. |
| Adaptive findings-to-next-test loop and controlled P3→P4 execution | Complete | Real planner + local sandbox/validator are exercised through the API create/start flow with deterministic LLM responses; no live model call. |
| Test-count and LLM-call budget cutoffs | Complete | Focused post-change adaptive-loop tests: 10 passed; both `run()` and `run_detailed()` stop further work at configured counts. |
| Tracked execution-time budget | Complete | Tests verify no subsequent planner/sandbox operation starts after tracked time is exhausted. The located P3 specification requires time accounting and `budget_exhausted`, not forced cancellation of an in-flight provider request. |
| Planner respects configured time budget | Partial | The loop stops subsequent work at tracked exhaustion, but saved A/D totals exceed 30 seconds; whether the intended criterion permits in-flight overruns needs P3/shared-team clarification. |
| V01–V12 backend/AI/sandbox support | Complete | Backend maps each ID to exactly the requested test; tests cover all 12 IDs and all 12 AI-to-sandbox executions. Sandbox vulnerability tests pass. |
| Chain execution, dependencies, replay, disruption, residual steps | Complete | Registered dependency, validator, and replay tests pass; full sandbox suite is 290 passed. |
| Multi-agent interactions | Complete | Local allowed/denied communication, per-agent grants, and planner reasoning tests pass. |
| Multi-agent validation and disruption | Partial | V11→V10 trigger/order is validated; no multi-agent mitigation/disruption replay evidence was found. |
| Agent-specific tool permissions | Complete | Registry-level tool assignment and independent per-agent grants are enforced and tested. |
| P2 API compatibility, persistence, and scenario resolution | Complete | Full backend suite: 149 passed; end-to-end API test uses real planner, local sandbox, and validator. |
| Browser-driven frontend-to-live-backend workflow | Not Verified | The API test matches the frontend create-then-start request contract, but no browser run against a live backend/database was performed. |
| A/B/C/D configuration and comparable runner | Complete | Four configurations and same-initial-state runner tests pass; current focused ablation suite passed. |
| Comparable successful non-fallback live A/B/C/D experiment | Pending External Dependency | No saved artifact has all four configurations complete with valid, successful non-fallback LLM decisions. Requires available Gemini service/quota and a saved same-state, same-budget run with decision-level provenance. |
| Canonical experiment-record reconciliation | Partial | Raw/derived runs are distinguished; some historical Day 12 narrative figures still lack a matching raw artifact. |
| Research claims limited to controlled evidence | Complete | Canonical reports restrict claims to the intentionally vulnerable sandbox and do not claim real-world effectiveness or comparative superiority. |
| Broad security effectiveness or comparative superiority | Not Verified | Current experiments are small controlled sandbox observations; neither effectiveness beyond that scope nor superiority is established. |

Remaining work owners: P3/shared team clarify the budget-respect semantics against recorded overruns; P4 owns multi-agent disruption evidence; P3 plus the external provider own the valid live A/B/C/D run; P3/P4 own final experiment provenance reconciliation; P1/P2 own any required live browser-to-backend acceptance run. Hard in-flight cancellation is not separately specified in Section 18.

## 16. Conclusion and Future Work

The evidence supports a conservative conclusion: AgentChain demonstrates controlled functionality for adaptive planning, local security-knowledge retrieval, deterministic sandbox testing, regular chain validation and replay, and multi-agent V11→V10 validation. It does not yet verify multi-agent chain disruption. Day 7 produced equal discovery and validation outcomes at equal test budgets, but does not establish adaptive superiority. The saved Day 12 runs are fallback-affected, budget-exhausted, or mixed in completion and do not establish that any ablation configuration is superior. Phase 3 is partially complete because a valid successful-LLM A/B/C/D run and multi-agent disruption evidence remain outstanding; planner budget respect is also partial due to saved over-30-second runs.

Future work, clearly outside the present results, should include reconciling the Day 12 execution-record discrepancy with raw artifacts; conducting successful, comparable LLM-backed A/B/C/D runs under documented, verified budget behavior; recording timing components and end-to-end metrics consistently; retaining failure and fallback runs; and expanding controlled scenarios and repetitions before making comparative claims. Any subsequent evaluation should continue to distinguish chain interruption from complete vulnerability mitigation and should not generalize sandbox results to real-world security effectiveness without separate evidence.

AgentChain's current results establish reproducible controlled behavior in an intentionally vulnerable sandbox, not superiority over alternative methods or real-world security effectiveness.
