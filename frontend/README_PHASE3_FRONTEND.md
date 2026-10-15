# AgentChain Phase 3 frontend (P1)

Run: `npm install && npm run dev` (backend proxied at `/api`, see `vite.config.js`). Unit tests: `npm test`.

Scope: frontend only. No backend, sandbox or planner logic is duplicated; every call below is an endpoint that already exists in `backend/app/main.py`. Phase 1 and Phase 2 screens and routes are unchanged except for the small additions listed under "Existing screens touched".

## New screens

| Task | Route | File | Backend used |
|---|---|---|---|
| 1 Attack-chain visualization | `/chains` (upgraded) | `pages/ChainExplorer.jsx`, `components/ChainGraph.jsx` | `GET /experiments`, `/findings`, `/chains`, `GET /scenarios`, `POST /chains/{id}/validate`, `POST /experiments/{id}/chains/execute` |
| 2 Before/after mitigation + chain validation | `/chain-mitigation` | `pages/ChainMitigation.jsx`, `components/ChainReplayParts.jsx` | `POST .../chains/{id}/p4-association`, `POST .../chains/mitigation/replay` |
| 3 Budget controls + decision timeline | `/new-experiment` (extended), `/adaptive/:id` | `pages/NewExperiment.jsx`, `pages/AdaptiveRun.jsx` | `POST /experiments` (`testing_budget`, `max_tests`), `POST .../start` |
| 4 Static vs adaptive + A/B/C/D charts | `/comparison` | `pages/Comparison.jsx` | `GET /phase3/analytics`, `GET /phase3/ablation/aggregation` |
| 5 Vulnerability details, filter, search, scenario selection | `/vulnerabilities`, scenario picker on `/new-experiment` | `pages/Vulnerabilities.jsx`, `components/Pickers.jsx` | `GET /scenarios`, findings endpoints |
| 6 Multi-agent visualization | `/agents/:id` | `pages/MultiAgent.jsx`, `AgentGraph` in `components/Phase3Parts.jsx` | `GET/POST .../agents/security-result(/run)`, `GET .../agents/state` |
| 7 Integration | `src/api/client.js` | | all of the above |

Pure logic (graph layout, run normalisation, ablation/agent/vulnerability shaping) lives in `src/lib/phase3.js` and is covered by `src/lib/phase3.test.js`.

### Existing screens touched (additive only)
- `Header.jsx`: five new nav items, badge reads "Phase 3".
- `App.jsx`: new routes.
- `NewExperiment.jsx`: scenario picker, vulnerability picker, budget wiring, `?scenario=` deep link. The existing "Testing budget" field was previously never sent; it now goes to `testing_budget`.
- `ChainExplorer.jsx`: Phase 1 behaviour kept (all-chain graph, node details, Validate Chain). Changed: findings are now matched per experiment (Phase 1 matched across all experiments, so a later experiment's finding could overwrite another's).
- `Findings.jsx`: free-text search. `ExperimentDetails.jsx`: three links.
- `api/client.js`: `createExperiment` sends Phase 3 fields only when set; `startExperiment` timeout raised to 300 s (planner calls the LLM).

## Behaviour to know
- **Snapshots.** `/comparison` falls back to `src/mock/phase3_*.json` when an endpoint is empty or fails, with a visible banner. They were generated from `ai-engine/results/phase3_ablation_gemini_20261011.json` and `DAY14_FINAL_evaluation.json`.
- **Ablation honesty.** The page lists why a comparison is not like-for-like (fallback used, budget exhausted, missing configuration). The saved run today triggers all of these, and `PHASE3_COMPLETION.md` records the same limitation. Missing metrics render as N/A, never as zero.
- **Decision timeline** only has data for experiments started from this app (see blocker 1). Otherwise the page shows the recorded sequence from the experiment record and findings, and says so.
- **Chain replay.** HTTP 200 is not treated as success: the verdict comes from `validation_result.status`, `chain_disrupted`, `blocked_steps` and `residual_vulnerable_steps`. A control whose target test is not in the chain is allowed and expected to disrupt nothing.
- **Vulnerability catalog** (`VULNERABILITIES` in `phase3.js`) mirrors `VULNERABILITY_TEST_MAP` and `EXPECTED_FINDINGS`. `npm test` parses the Python files and fails if they drift.

## Integration blockers (for P2 / P3, not invented here)

| # | Owner | Gap | Effect on the UI |
|---|---|---|---|
| 1 | P2 | `adaptive_run_results` is stored but no GET exists. Decisions, planner metadata and budget are only in the `POST /start` response. | Timeline works only for runs started from this browser (kept in localStorage). Ask: `GET /experiments/{id}/adaptive-run`. |
| 2 | P2 | `/start` returns `"status": "completed"` even when the loop ended `budget_exhausted`. | UI can only infer a cut run when a decision has no execution. Ask: return the loop's `run_status`. |
| 3 | P2/P3 | Loop decisions contain only `selected_test` and `reason`; `priority`/`confidence` (contract §4.3) are dropped. Ablation `planner_decisions` do carry them. | Fields render only if present. |
| 4 | P2/P3 | LLM-call and time caps are not configurable via the API (`ExperimentCreate` has only `max_tests` and an unused `testing_budget` int). | Budget meter shows a cap for tests only; LLM calls and time are shown as used, with "limit set server-side". |
| 5 | P2 | `mode: "static"` is stored but `/start` always runs the planner loop. `/phase3/analytics` is fed only by `/chains/execute`. | Static-vs-adaptive is empty until such records exist (snapshot shown meanwhile). Ask what produces static records via the API. |
| 6 | P2/P4 | `/chains/execute` requires a registered P4 chain id, but `/start` stores generated `CHAIN-xxxxxxxx` ids, and no endpoint creates a registered-id chain record. | Execute button is disabled with an explanation for generated chains. Validate and mitigation replay (via p4-association) work. |
| 7 | P2/P4 | No vulnerability catalog endpoint. `/scenarios` omits `vulnerability_ids`, `dependencies`, `entry_condition`, `expected_goal`, which exist in the registry. | Catalog is mirrored (drift-tested). Dependencies appear only after p4-association stores them on the chain. |
| 8 | P2 | `GET .../agents/security-result` returns the first stored document; `POST .../run` appends a new one each time. | A re-run does not change the view; the UI says so. Ask for latest-first. |
| 9 | P4 | No mitigation/disruption replay for the multi-agent chain (also listed in `PHASE3_COMPLETION.md`). | Multi-agent page shows interaction and chain validation only. |
| 10 | P3 | Nothing persists ablation results through the API except `POST /phase3/ablation/results`. Aggregation is empty until P3 posts a valid A–D run. | Snapshot shown with banner. |
| 11 | P2 | `API_CONTRACT.md` still describes Phase 2 and lacks `/scenarios`, `/phase3/*`, agents endpoints, `chains/execute` and the extended `/start` response. | This README is the frontend's reference until it is updated. |

## Verification status
Run in this environment (no network, so `npm install` and a browser run were not possible):
- `npm test`: 22 unit tests pass.
- Whole app bundled with esbuild (third-party packages external): all JSX parses and every relative import resolves.
- Type-checker pass for undefined identifiers: clean.
- Server-side render smoke test of the timeline, budget meters, agent graph, replay views and pickers with realistic payloads: all pass.

Not run: `npm run build`/`dev`, anything using `reactflow`/`recharts` at runtime, and a live browser-to-backend run (also still open in `PHASE3_COMPLETION.md` as P1/P2). Run `npm install && npm run build` first, then walk: New Experiment → Adaptive Run → Chains → Chain Mitigation → Comparison → Vulnerabilities → Multi-Agent.
