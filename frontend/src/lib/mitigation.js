// Shared constants + tiny local store for Phase 2 mitigation runs.
export const CONTROLS = {
  authorization_gate: { label: 'Authorization Gate', test: 'permission_test', desc: 'Requires authorization before a sensitive action runs.' },
  tool_allowlist: { label: 'Tool Allowlist', test: 'tool_access_test', desc: 'Restricts the agent to an explicit list of permitted tools.' },
  memory_validation: { label: 'Memory Validation', test: 'memory_access_test', desc: 'Stops untrusted memory content being treated as trusted instructions.' },
}

export const CONDITIONS = {
  rule_based_fixed_mitigation: 'Rule-based fixed',
  llm_recommendation_only: 'LLM recommendation only',
  level3_proposed: 'Level-3 (proposed)',
  wrong_control: 'Wrong control',
}

export const pct = (v) => (v == null ? 'N/A' : `${Math.round(v * 100)}%`)
export const controlLabel = (c) => CONTROLS[c]?.label ?? c ?? '—'

const KEY = 'agentchain.mitigationRuns'

export function loadRuns() {
  try {
    return JSON.parse(localStorage.getItem(KEY)) ?? []
  } catch {
    return []
  }
}

// Upsert by mitigation_run_id; merges timings so each step can add its own.
export function saveRun(run) {
  try {
    const runs = loadRuns()
    const i = runs.findIndex((r) => r.mitigation_run_id === run.mitigation_run_id)
    if (i >= 0) runs[i] = { ...runs[i], ...run, timings: { ...runs[i].timings, ...run.timings } }
    else runs.unshift(run)
    localStorage.setItem(KEY, JSON.stringify(runs.slice(0, 50)))
  } catch {
    /* storage unavailable: ignore */
  }
}

export const getRun = (id) => loadRuns().find((r) => r.mitigation_run_id === id)
