# AgentChain Frontend — Person 1 (Frontend & Visualization)

Built per `AGENTCHAIN_TEAM_IMPLEMENTATION.md`. Covers everything in the
"Person 1" section of the doc and nothing outside it (no LLM/planner logic,
no direct MongoDB access, no sandbox code, no backend contract changes).

## Run it

```bash
npm install
npm run dev
```

Opens at `http://localhost:5173`. All 8 pages work standalone right now,
reading from mock JSON in `src/mock/`.

## Pages (matches the doc exactly)

- **Dashboard** — experiment/finding/chain counts, validation rate, avg chain length, recent runs
- **New Experiment** — name, Static/Adaptive mode, max tests, testing budget, Start button
- **Experiment Details** — per-experiment stats, findings, candidate chains, recent activity
- **Live Logs** — chronological event stream, filterable by experiment
- **Findings** — ID, type, severity, confidence, evidence, validation status, filterable by severity
- **Attack Chain Explorer** — React Flow graph, click a node to see finding details
- **Analytics** — Recharts comparison of Static vs Adaptive (bar + pie charts)
- **Experiment History** — full table of all runs

## Connecting to Person 2's backend

Everything routes through `src/api/client.js`, which mirrors every endpoint
in Section 6 of the doc (`POST /experiments`, `GET /experiments/:id/findings`,
`POST /chains/:id/validate`, `GET /analytics`, etc.).

To switch from mock data to the real FastAPI backend:

1. Open `src/api/client.js`
2. Set `const USE_MOCK = false`
3. That's it — no page component needs to change, since they all call the
   same functions either way.

The Vite dev server also proxies `/api/*` to `http://localhost:8000`
(Person 2's FastAPI default), configured in `vite.config.js`.

## What's intentionally NOT here

Per the doc's "Must NOT do" list for Person 1:
- No LLM/planner logic (Person 3's scope)
- No direct MongoDB access (Person 2 owns the DB)
- No sandbox vulnerabilities (Person 4's scope)
- No changes to the API contract — this UI consumes it as specified

## Design notes

Dark "security console" theme (graphite background, amber accent for
active/priority states, semantic severity colors for critical/high/medium/low).
IBM Plex Sans for UI, IBM Plex Mono reserved for technical values (test IDs,
finding IDs, JSON-shaped data) to keep it legible as a real research tool
rather than a generic dashboard template.
