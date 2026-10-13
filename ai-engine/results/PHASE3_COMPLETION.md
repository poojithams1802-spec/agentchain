# AgentChain Phase 3 — Evidence and DoD Status

This report supersedes the earlier blanket completion statement. “Complete” below means the scoped implementation or verification item is supported; it does not claim security effectiveness.

## Definition of Done Matrix

Authoritative source: Section 18, “Phase 3 Definition of Done,” supplied by the user. Statuses below map each criterion; “Complete” is limited to the stated controlled implementation/evidence and is not a real-world security claim.

| Section 18 criterion | Status | Evidence and boundary | Owner |
|---|---|---|---|
| 1. Multiple chain structures execute | Complete | Seven registered chains; chain replay and execution tests pass in the 290-test sandbox suite. | P4 |
| 1. Chain dependencies are represented | Complete | Registry definitions and dependency-order tests; included in the 30-test focused chain/validator/replay run. | P4 |
| 1. Chain validation works | Complete | ChainValidator tests and integrated backend validation; sandbox suite 290 passed. | P4 |
| 1. Chain disruption works | Complete | Registered-chain replay tests verify blocked steps and disruption; not a claim about multi-agent disruption. | P4 |
| 1. Residual steps are reported | Complete | Replay tests assert residual vulnerable steps after effective and ineffective controls. | P4 |
| 2. Test budget is supported | Complete | `AdaptiveLoop` stops at the test cap; fake-clock/budget tests are included in the 264-test AI-engine suite. | P3 |
| 2. LLM-call budget is supported | Complete | Both `run()` and `run_detailed()` stop after the configured call cap; tested in the full AI-engine suite. | P3 |
| 2. Time budget is supported | Complete | Tracked elapsed time and between-operation cutoff are tested; this matches the located spec. | P3 |
| 2. Planner respects the budget | Partial | Tests assert no new planner/sandbox operation begins after the tracked cutoff, but saved A/D wall-clock totals are 30.952956s and 31.074635s against 30s. The spec does not define in-flight cancellation semantics. | P3/shared team |
| 2. Budget exhaustion is handled | Complete | Planner/runner exposes `budget_exhausted`; saved ablation records preserve this status. | P3 |
| 3. LLM-only configuration | Complete | A configuration is defined and exercised by ablation runner tests. | P3 |
| 3. LLM + RAG configuration | Complete | B configuration is defined and exercised by ablation runner tests. | P3 |
| 3. LLM + chain-context configuration | Complete | C configuration is defined and exercised by ablation runner tests. | P3 |
| 3. Full proposed approach | Complete | D (LLM + RAG + chain context) is defined and exercised by ablation runner tests. | P3 |
| 3. Same scenarios are compared across configurations | Partial | Runner tests use the same initial state. Saved live artifacts are fallback-affected, budget-exhausted, or unequally complete, so a valid comparison is pending. | P3 |
| 4. 10–12 controlled vulnerability types | Complete | V01–V12 map exactly to approved sandbox tests; backend mapping and AI adapter coverage are tested. | P2/P3/P4 |
| 4. Multiple chain configurations | Complete | Seven registered chain definitions pass registry tests. | P4 |
| 4. Deterministic reset | Complete | Replay resets mitigation state before/after runs, including exception cleanup; focused replay tests cover reset. | P4 |
| 4. Test evidence | Complete | Full sandbox suite: 290 passed; backend: 149 passed; AI engine: 264 passed. | Shared team |
| 4. Regression coverage | Complete | Exact full-suite results above; warnings are dependency deprecations. | Shared team |
| 5. At least two agents | Complete | Controlled registry contains two agents; scenario tests pass. | P4 |
| 5. Controlled communication | Complete | Allowed and denied local communication paths are tested. | P4 |
| 5. Agent-specific tools and permissions | Complete | Registry enforces tool assignment and per-agent allow/deny grants; 11 registry tests pass. | P4 |
| 5. At least one multi-agent chain | Complete | Controlled V11→V10 chain is represented and triggered in the local scenario. | P4 |
| 5. Multi-agent validation and disruption | Partial | V11→V10 order, findings, and communication are validated; no mitigation/disruption replay for the multi-agent chain was found. | P4 |
| 6. Static baseline | Complete | Day 7 static controlled baseline has saved result/evaluation evidence and deterministic tests. | P3/P4 |
| 6. Adaptive baseline | Complete | Day 7 adaptive controlled run and local sandbox integration are tested. | P3/P4 |
| 6. Ablation experiments | Partial | A-D runner and raw runs exist; no valid successful non-fallback four-way comparison. | P3 / external provider |
| 6. Wrong-control experiments | Complete | Wrong-control replay returns no blocked steps, retains residual steps, and fails validation; replay tests cover it. | P4 |
| 6. LLM fallback evaluation | Complete | Raw JSON preserves HTTP 429 and HTTP 503/504 fallback cases and outcomes; these are not successful live comparisons. | P3 |
| 6. Timing evaluation | Partial | Day 7 and ablation timing values are saved; ablation timings are fallback/mixed and A/D exceed the configured 30 seconds. | P3 |
| 6. Reproducible experiment records | Partial | Raw JSON and test commands are retained; some older narrative metrics remain unmatched or derived and unvalidated. | P3/shared team |
| 6. Research claims stay within controlled evidence | Complete | Canonical reports limit claims to the intentionally vulnerable sandbox and do not claim real-world effectiveness or comparative superiority. | P3/shared team |
| 7. P1↔P2 integration | Partial | Backend create/start API contract is tested, but no browser-driven frontend/live-backend run was performed. | P1/P2 |
| 7. P2↔P3 integration | Complete | Backend create/start invokes the planner; persisted adaptive-run data is asserted in the API test. | P2/P3 |
| 7. P3↔P4 integration | Complete | AI adapter and backend workflow execute approved tests in the local sandbox and validate the result. | P3/P4 |
| 7. Full end-to-end workflow | Complete | Deterministic API test covers create→planner→sandbox→validator→persistence with a stubbed LLM and in-memory test DB. | P2/P3/P4 |
| 7. Existing Phase 1 and Phase 2 tests pass | Partial | Backend and sandbox suites pass; browser/frontend validation was not run and remains P1/P2-owned. | P1/P2/shared team |

## Remaining Work by Owner

| Owner | Remaining work | Status |
|---|---|---|
| P3/shared team | Clarify the intended meaning of “planner respects the budget” against the recorded A/D overruns; retain operation-boundary behavior unless stricter semantics are specified. | Partial |
| P4 | Add or locate controlled mitigation/disruption replay evidence for the V11→V10 multi-agent chain. | Not Verified |
| P3 + external provider | Run a same-state, same-budget A/B/C/D experiment with successful non-fallback decisions for all modes and preserve raw outcomes. | Pending External Dependency |
| P3/P4 | Reconcile the remaining narrative-only Day 12 metrics against a source run or retain them explicitly as unverified history. | Partial |
| P1/P2 | If browser-level completion is mandatory, run unchanged frontend against a test backend/database and capture create/start/result. | Not Verified |

## Experiment Record Classification

- Deterministic software tests verify implementation contracts; they are not security outcome metrics.
- `phase3_ablation_day12.json` records fallback after HTTP 429 in A-D, two completed sandbox tests each, three LLM calls each, and `budget_exhausted` status.
- `phase3_ablation_gemini_20261011.json` records one non-fallback test for A/D before budget exhaustion, and three fallback tests for B/C after HTTP 503/504. The mixed run is not a valid A/B/C/D comparison.
- The narrative times in `P3_day16_experimental_results.md` do not match these saved artifacts; retain them as unverified historical figures until a matching raw run is found.
- No valid live non-fallback A/B/C/D experiment is currently recorded. No superiority or real-world security-effectiveness claim is made.

## Verification Evidence

Current full-suite results: 290 sandbox tests, 149 backend tests, and 264 AI-engine tests passed. The AI-engine run includes the latest adapter regression. Focused multi-agent registry coverage reports 11 passed.

| Command | Result |
|---|---|
| `.\venv\Scripts\python.exe -m pytest .\sandbox -q` | 290 passed, 1 warning, 57.63s |
| `.\venv\Scripts\python.exe -m pytest .\backend\tests -q` | 149 passed, 2 warnings, 20.70s |
| `Push-Location .\ai-engine; ..\venv\Scripts\python.exe -m pytest .\tests -q; Pop-Location` | 264 passed, 1 warning, 674.30s (11:14) |
| `.\venv\Scripts\python.exe -m pytest .\sandbox\tests\test_multi_agent_registry.py -q` | 11 passed |
| `.\venv\Scripts\python.exe -m pytest .\backend\tests\test_phase3_adaptive_selection.py::test_frontend_create_start_flow_uses_real_planner_and_sandbox -q` | 1 passed, 2 warnings, 17.42s |

## Requirements to Close Remaining Gaps

1. Run A/B/C/D with the same initial state, candidate set, model/configuration, and budgets; obtain successful non-fallback decisions in all four modes and retain the complete raw JSON, including failures and timing.
2. Provide Gemini service availability and sufficient quota for at least 12 successful planner requests (three per configuration), plus any retries; confirm the configured model and credentials in the experiment environment.
3. The located P3 specification requires a time budget and says the planner should respect it. Current code enforces a between-operation cutoff, but saved A/D totals exceed 30s. Clarify whether that measured overrun violates the intended budget semantics; hard cancellation itself is not separately specified.
4. If browser-level end-to-end completion is required, P1/P2 must run the unchanged frontend against the backend with a test database and capture the create/start/result path.

Until the pending external comparison, partial budget-respect criterion, and unverified multi-agent disruption criterion are resolved, Phase 3 is partially complete against supplied Section 18. No commit or push is implied by this report.
