# AgentChain Phase 2 frontend (P1)

Run: `npm install && npm run dev` (backend on 127.0.0.1:8000, proxied at `/api`).

## New screens
| Route | File | Purpose |
|---|---|---|
| `/mitigation` | pages/Mitigation.jsx | experiment -> chain -> finding -> select -> apply -> replay |
| `/mitigation/:experimentId/:runId` | pages/MitigationResult.jsx | verdict, before/after, chain disruption, details |
| `/phase2-analytics` | pages/Phase2Analytics.jsx | 4-condition metrics, charts, JSON / Markdown report export |

Uses the live endpoints `mitigation/select | apply | replay | result` as implemented in backend/app/main.py.

## One thing to ask Person 2
`GET /phase2/analytics` does not exist yet. Expected response (same as the bundled snapshot in src/mock/phase2.json):
```python
records = run_all_phase2_experiments()
return {"metrics": calculate_phase2_metrics(records), "records": records}
```
Until it exists, the page falls back to the snapshot and shows a banner saying so.

## Behaviour to know
- Selection calls the LLM (about 60 s in your logs); the UI shows a live timer and a 180 s timeout.
- The backend only accepts the replay test that matches the selected control, so the UI sends it automatically. Wrong-control runs cannot go through the API; they appear only in the experiments table.
- There is no "list mitigation runs" endpoint, so recent runs are kept in browser localStorage.

## Design refresh (visual only)
Re-skinned to match agentchain_platform_ui.tsx. No routes, API calls or logic changed.
- Top header navigation replaces the sidebar (components/Header.jsx); light/dark toggle (default light, saved in localStorage).
- Theme colors are CSS variables in src/index.css, used through the existing Tailwind names (base-*, signal, sev-*), so every page themes automatically.
- Dashboard has a new hero (components/LoopHero.jsx). It is a static illustration of the Level-3 workflow and the three predefined controls, with no live or invented data.
- Charts and the attack-chain graph follow the theme (lib/theme.js).
- Primary buttons use the .btn-primary gradient class.
