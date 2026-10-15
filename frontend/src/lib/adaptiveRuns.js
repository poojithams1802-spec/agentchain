// The adaptive-run detail (decisions, planner metadata, budget used) is returned
// ONLY by POST /experiments/{id}/start. The backend persists it in
// `adaptive_run_results` but exposes no GET for it (README_PHASE3_FRONTEND.md,
// blocker #1). Until P2 adds one, we keep the response in this browser, the same
// way Phase 2 keeps recent mitigation runs (lib/mitigation.js).
const KEY = 'agentchain.adaptiveRuns'
const MAX = 30

function read() {
  try {
    const v = JSON.parse(localStorage.getItem(KEY))
    return v && typeof v === 'object' ? v : {}
  } catch {
    return {}
  }
}

export function saveAdaptiveRun(experimentId, startResponse) {
  if (!experimentId || !startResponse) return
  try {
    const all = read()
    all[experimentId] = { saved_at: new Date().toISOString(), response: startResponse }
    const keep = Object.entries(all)
      .sort((a, b) => (b[1].saved_at ?? '').localeCompare(a[1].saved_at ?? ''))
      .slice(0, MAX)
    localStorage.setItem(KEY, JSON.stringify(Object.fromEntries(keep)))
  } catch {
    /* storage unavailable or full: the page falls back to an explanatory empty state */
  }
}

export const loadAdaptiveRun = (experimentId) => read()[experimentId] ?? null

export const listAdaptiveRunIds = () =>
  Object.entries(read())
    .sort((a, b) => (b[1].saved_at ?? '').localeCompare(a[1].saved_at ?? ''))
    .map(([id]) => id)
