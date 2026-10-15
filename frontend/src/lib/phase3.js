// Phase 3 shared constants + pure helpers (no React, no DOM) so they can be
// unit-tested with `npm test` (node --test) without a browser.
//
// Nothing here talks to the backend or re-implements planner/sandbox logic: it
// only reshapes responses the backend already returns.

export const prettify = (s) => (typeof s === 'string' ? s.replaceAll('_', ' ') : s ?? '—')
export const fmtSec = (v) => (typeof v === 'number' ? `${v.toFixed(v < 1 ? 3 : 1)}s` : '—')
export const fmtPct = (v) => (typeof v === 'number' ? `${Math.round(v * 100)}%` : 'N/A')
export const toPct = (v) => (typeof v === 'number' ? Math.round(v * 1000) / 10 : null)

// ---------------------------------------------------------------------------
// Vulnerability catalog.
// MIRROR of sandbox/test_runner.py VULNERABILITY_TEST_MAP (ids accepted by
// POST /experiments -> vulnerability_ids) and sandbox/validator EXPECTED_FINDINGS.
// There is no catalog endpoint yet (see README_PHASE3_FRONTEND.md, blocker #7).
// src/lib/phase3.test.js fails if this drifts from the Python source.
// ---------------------------------------------------------------------------
export const VULNERABILITIES = [
  { id: 'V1', test: 'permission_test', finding: 'weak_permission_control' },
  { id: 'V2', test: 'tool_access_test', finding: 'unsafe_tool_access' },
  { id: 'V3', test: 'memory_access_test', finding: 'memory_validation_weakness' },
  { id: 'V4', test: 'prompt_injection_test', finding: 'prompt_injection' },
  { id: 'V5', test: 'indirect_prompt_injection_test', finding: 'indirect_prompt_injection' },
  { id: 'V6', test: 'sensitive_data_test', finding: 'sensitive_data_exposure' },
  { id: 'V7', test: 'file_operation_test', finding: 'unsafe_file_operation' },
  { id: 'V8', test: 'context_manipulation_test', finding: 'context_manipulation' },
  { id: 'V9', test: 'privilege_propagation_test', finding: 'privilege_propagation' },
  { id: 'V10', test: 'unsafe_delegation_test', finding: 'unsafe_delegation' },
  { id: 'V11', test: 'cross_agent_trust_test', finding: 'cross_agent_trust_weakness' },
  { id: 'V12', test: 'tool_parameter_validation_test', finding: 'tool_parameter_validation_weakness' },
].map((v) => ({ ...v, title: prettify(v.finding).replace(/^./, (c) => c.toUpperCase()) }))

export const vulnByTest = Object.fromEntries(VULNERABILITIES.map((v) => [v.test, v]))

// Only three defensive controls exist (CONTROL_TARGETS in the sandbox).
export const CONTROL_FOR_TEST = {
  permission_test: 'authorization_gate',
  tool_access_test: 'tool_allowlist',
  memory_access_test: 'memory_validation',
}

// ---------------------------------------------------------------------------
// Findings helpers
// ---------------------------------------------------------------------------
// Latest finding per test (later records win), like the Phase 2 mitigation page.
export function latestFindingByTest(findings = []) {
  const byTest = {}
  findings.forEach((f) => {
    if (f?.test) byTest[f.test] = f
  })
  return byTest
}

export function evidenceText(evidence) {
  if (evidence == null) return ''
  return typeof evidence === 'string' ? evidence : JSON.stringify(evidence)
}

// ---------------------------------------------------------------------------
// Attack-chain graph
// ---------------------------------------------------------------------------
// Edges come from the chain's stored `dependencies` map when present (it is
// written by POST .../p4-association). Otherwise only execution order is known,
// and the edges are labelled "order" so the UI never claims dependency data it
// does not have.
export function chainEdges(chain) {
  const steps = chain?.steps ?? []
  const deps = chain?.dependencies
  if (deps && typeof deps === 'object' && !Array.isArray(deps)) {
    const edges = []
    steps.forEach((step) => {
      ;(deps[step] ?? []).forEach((dep) => {
        if (steps.includes(dep)) edges.push({ source: dep, target: step, kind: 'dependency' })
      })
    })
    return edges
  }
  return steps.slice(1).map((step, i) => ({ source: steps[i], target: step, kind: 'order' }))
}

// Longest-path depth so a dependency graph lays out left-to-right.
function depths(chain, edges) {
  const steps = chain?.steps ?? []
  const memo = {}
  const visiting = new Set()
  const depth = (s) => {
    if (memo[s] != null) return memo[s]
    if (visiting.has(s)) return 0 // defensive: ignore cycles
    visiting.add(s)
    const incoming = edges.filter((e) => e.target === s)
    memo[s] = incoming.length ? 1 + Math.max(...incoming.map((e) => depth(e.source))) : 0
    visiting.delete(s)
    return memo[s]
  }
  steps.forEach(depth)
  return memo
}

export const NODE_W = 210
export const NODE_GAP_X = 90
export const NODE_GAP_Y = 36
export const NODE_H = 96

/**
 * Pure graph description for one chain. Styling is applied by the component.
 * validationSteps: `steps` from POST /chains/{id}/validate or /chains/execute.
 */
export function buildChainGraph(chain, { findings = [], validationSteps = [], offsetY = 0 } = {}) {
  const byTest = latestFindingByTest(findings)
  const valByTest = Object.fromEntries((validationSteps ?? []).map((s) => [s.test, s]))
  const edgesRaw = chainEdges(chain)
  const depth = depths(chain, edgesRaw)
  const laneCount = {}

  const nodes = (chain?.steps ?? []).map((step, index) => {
    const d = depth[step] ?? 0
    const lane = laneCount[d] ?? 0
    laneCount[d] = lane + 1
    const finding = byTest[step] ?? null
    const validation = valByTest[step] ?? null
    let status = 'unknown'
    if (validation) status = validation.valid === true ? 'reproduced' : 'failed'
    else if (finding) status = 'finding'
    return {
      id: `${chain.chain_id}::${step}`,
      step,
      index,
      chainId: chain.chain_id,
      x: d * (NODE_W + NODE_GAP_X),
      y: offsetY + lane * (NODE_H + NODE_GAP_Y),
      finding,
      validation,
      status,
      vulnerability: vulnByTest[step] ?? null,
    }
  })

  const edges = edgesRaw.map((e) => {
    const target = valByTest[e.target]
    return {
      id: `${chain.chain_id}::${e.source}->${e.target}`,
      source: `${chain.chain_id}::${e.source}`,
      target: `${chain.chain_id}::${e.target}`,
      kind: e.kind,
      // Only judged when validation ran; undefined means "not checked".
      satisfied: target ? target.dependency_valid !== false : undefined,
      error: target?.dependency_error ?? null,
    }
  })

  return { nodes, edges, height: Math.max(...Object.values(laneCount), 1) * (NODE_H + NODE_GAP_Y) }
}

// Registered P4 definitions (from GET /scenarios) that may be associated with a
// stored chain: the contract requires identical ordered steps.
export function matchingScenarios(chain, scenarios = []) {
  const steps = chain?.steps ?? []
  return scenarios.filter(
    (s) => Array.isArray(s.steps) && s.steps.length === steps.length && s.steps.every((x, i) => x === steps[i]),
  )
}

// POST /chains/execute only works for ids in the P4 registry (blocker #6).
export const isRegisteredChainId = (chainId, scenarios = []) => scenarios.some((s) => s.scenario_id === chainId)

// ---------------------------------------------------------------------------
// Adaptive run (response of POST /experiments/{id}/start)
// ---------------------------------------------------------------------------
export function normalizeAdaptiveRun(start) {
  if (!start || typeof start !== 'object') return null
  const decisions = Array.isArray(start.decisions) ? start.decisions : []
  const metadata = Array.isArray(start.decision_metadata) ? start.decision_metadata : []
  const executions = Array.isArray(start.execution_results) ? start.execution_results : start.sandbox_results ?? []
  const used = start.budget_used ?? {}

  const events = decisions.map((d, i) => {
    const meta = metadata[i] ?? {}
    // A decision can exist without an execution (time budget hit right after
    // planning). Prefer positional match, verify by test name.
    let exec = executions[i]
    if (!exec || exec.test !== d.selected_test) exec = executions.find((e) => e.test === d.selected_test) ?? null
    return {
      index: i + 1,
      test: d.selected_test,
      reason: d.reason ?? '',
      // Present on the planner contract (§4.3) but dropped by the adaptive loop today.
      priority: typeof d.priority === 'number' ? d.priority : null,
      confidence: typeof d.confidence === 'number' ? d.confidence : null,
      source: meta.decision_source ?? 'unknown',
      fallbackReason: meta.fallback_reason ?? null,
      recovery: meta.decision_recovery ?? null,
      rag: {
        status: meta.rag_retrieval_status ?? 'unknown',
        retrieved: meta.rag_context_retrieved ?? null,
        used: meta.rag_context_used ?? null,
      },
      executed: !!exec,
      result: exec
        ? {
            status: exec.status,
            finding: exec.finding ?? null,
            severity: exec.severity ?? null,
            confidence: typeof exec.confidence === 'number' ? exec.confidence : null,
            evidence: exec.evidence ?? null,
            executionCost: exec.execution_cost ?? null,
          }
        : null,
    }
  })

  const fallbackDecisions = events.filter((e) => e.source === 'deterministic_fallback').length
  return {
    experimentId: start.experiment_id ?? null,
    status: start.status ?? null,
    events,
    budget: {
      tests: used.tests ?? start.tests_used ?? 0,
      llmCalls: used.llm_calls ?? start.llm_calls ?? 0,
      timeSeconds: used.time_seconds ?? null,
    },
    fallbackUsed: !!start.fallback_used,
    fallbackDecisions,
    // Provable from the data: planner chose a test but it never ran.
    cutBeforeExecution: events.some((e) => !e.executed),
    candidateChain: start.candidate_chain ?? null,
    validation: start.validation_result ?? null,
  }
}

// Meters for the budget panel. A cap is only known for max_tests (it is the
// experiment's own setting); LLM-call and time caps are server-side (blocker #4).
export function budgetMeters(run, experiment) {
  if (!run) return []
  const maxTests = experiment?.max_tests ?? null
  return [
    { key: 'tests', label: 'Tests executed', used: run.budget.tests, cap: maxTests, unit: '' },
    { key: 'llm', label: 'LLM planner calls', used: run.budget.llmCalls, cap: null, unit: '' },
    { key: 'time', label: 'Planner + sandbox time', used: run.budget.timeSeconds, cap: null, unit: 's' },
  ]
}

// ---------------------------------------------------------------------------
// Static vs adaptive (GET /phase3/analytics -> { metrics: {static, adaptive}, records })
// ---------------------------------------------------------------------------
export const SA_METRICS = [
  ['total_tests', 'Tests executed'],
  ['total_findings', 'Findings'],
  ['candidate_chains', 'Candidate chains'],
  ['validated_chains', 'Validated chains'],
  ['execution_count', 'Execution count'],
  ['llm_calls', 'LLM calls'],
]

export const hasStaticAdaptiveData = (metrics) =>
  !!metrics && (metrics.static?.experiments ?? 0) + (metrics.adaptive?.experiments ?? 0) > 0

export function staticAdaptiveCounts(metrics) {
  return SA_METRICS.map(([key, label]) => ({
    key,
    label,
    Static: metrics?.static?.[key] ?? null,
    Adaptive: metrics?.adaptive?.[key] ?? null,
  }))
}

export function staticAdaptiveRates(metrics) {
  return [
    ['validation_rate', 'Chain validation rate'],
  ].map(([key, label]) => ({
    label,
    Static: toPct(metrics?.static?.[key]),
    Adaptive: toPct(metrics?.adaptive?.[key]),
  }))
}

// ---------------------------------------------------------------------------
// A/B/C/D ablation (GET /phase3/ablation/aggregation -> { comparisons: [...] })
// ---------------------------------------------------------------------------
export const ABLATION_CONFIGS = [
  { key: 'llm_only', code: 'A', label: 'LLM only' },
  { key: 'llm_rag', code: 'B', label: 'LLM + RAG' },
  { key: 'llm_chain_context', code: 'C', label: 'LLM + chain context' },
  { key: 'llm_rag_chain_context', code: 'D', label: 'LLM + RAG + chain context' },
]

export function groupAblation(comparisons = []) {
  const out = Object.fromEntries(ABLATION_CONFIGS.map((c) => [c.key, []]))
  comparisons.forEach((r) => {
    if (out[r.configuration]) out[r.configuration].push(r)
  })
  return out
}

// One row per configuration: the latest persisted run (ids increase over time).
export function latestAblationRuns(comparisons = []) {
  const grouped = groupAblation(comparisons)
  return ABLATION_CONFIGS.map((c) => {
    const runs = grouped[c.key]
    return { ...c, runs: runs.length, record: runs.length ? runs[runs.length - 1] : null }
  })
}

export const ABLATION_RATE_METRICS = [
  ['selection_accuracy', 'Selection accuracy'],
  ['chain_discovery_rate', 'Chain discovery'],
  ['mitigation_success', 'Mitigation success'],
  ['chain_disruption', 'Chain disruption'],
  ['validation_rate', 'Validation rate'],
]

export const ABLATION_COST_METRICS = [
  ['tests_required', 'Tests required', ''],
  ['llm_calls', 'LLM calls', ''],
  ['latency', 'Latency', 's'],
  ['planner_time_seconds', 'Planner time', 's'],
  ['execution_time_seconds', 'Execution time', 's'],
  ['residual_vulnerable_steps', 'Residual vulnerable steps', ''],
]

// Chart rows: one row per metric, one key per configuration code (A-D).
// Missing metrics stay null so the chart leaves a gap instead of drawing zero.
export function ablationRateRows(runs) {
  return ABLATION_RATE_METRICS.map(([key, label]) => ({
    metric: label,
    ...Object.fromEntries(runs.map((r) => [r.code, toPct(r.record?.[key])])),
  }))
}

export function ablationCostRows(runs, key) {
  return runs.map((r) => ({
    name: `${r.code} · ${r.label}`,
    code: r.code,
    value: typeof r.record?.[key] === 'number' ? r.record[key] : null,
  }))
}

// A comparison is only like-for-like when all four ran to completion without
// fallback. Mirrors the caveat recorded in ai-engine/results/PHASE3_COMPLETION.md.
export function ablationCaveats(runs) {
  const notes = []
  runs.forEach((r) => {
    if (!r.record) {
      notes.push(`${r.code} (${r.label}): no persisted run`)
      return
    }
    if (r.record.fallback_used) notes.push(`${r.code}: planner fell back to the deterministic ranker`)
    if (r.record.status && r.record.status !== 'completed') notes.push(`${r.code}: run status "${r.record.status}"`)
  })
  return notes
}

export const isCleanAblation = (runs) => runs.length === 4 && ablationCaveats(runs).length === 0

// ---------------------------------------------------------------------------
// Multi-agent (GET /experiments/{id}/agents/security-result)
// Two persisted shapes exist: the P4 scenario runner (communication,
// chain_steps, validation, vulnerabilities) and the manual POST
// (interactions, trust_context, assessment). Handle both, invent nothing.
// ---------------------------------------------------------------------------
export function normalizeAgentResult(doc) {
  if (!doc || typeof doc !== 'object') return null
  const agents = Array.isArray(doc.agents) ? doc.agents : []
  const byId = Object.fromEntries(agents.map((a) => [a.agent_id, a]))
  const edgeMap = new Map()
  const put = (from, to, patch) => {
    if (!from || !to) return
    const key = `${from}->${to}`
    const prev = edgeMap.get(key) ?? { from, to, kind: 'allowed', message: null }
    // delivered / denied outrank "allowed by configuration".
    const rank = { allowed: 0, denied: 1, delivered: 2 }
    const next = { ...prev, ...patch }
    if (patch.kind && rank[patch.kind] < rank[prev.kind]) next.kind = prev.kind
    edgeMap.set(key, next)
  }

  agents.forEach((a) => (a.allowed_interactions ?? []).forEach((to) => put(a.agent_id, to, { kind: 'allowed' })))

  const comms = []
  if (doc.communication && typeof doc.communication === 'object') comms.push(doc.communication)
  if (Array.isArray(doc.interactions)) comms.push(...doc.interactions)
  comms.forEach((c) => {
    const from = c.sender ?? c.from ?? c.source ?? c.source_agent
    const to = c.receiver ?? c.to ?? c.target ?? c.target_agent
    const status = c.status === 'delivered' || c.status === 'denied' ? c.status : 'allowed'
    put(from, to, { kind: status, message: c.message ?? c.reason ?? null })
  })

  const edges = [...edgeMap.values()].map((e) => {
    const gap = (byId[e.to]?.trust_level ?? 0) - (byId[e.from]?.trust_level ?? 0)
    return { ...e, crossesTrustBoundary: gap > 0.3, trustGap: Number.isFinite(gap) ? gap : 0 }
  })

  return {
    experimentId: doc.experiment_id ?? null,
    chainId: doc.chain_id ?? null,
    status: doc.status ?? null,
    agents,
    edges,
    chainSteps: Array.isArray(doc.chain_steps) ? doc.chain_steps : [],
    expectedChain: Array.isArray(doc.expected_chain) ? doc.expected_chain : [],
    chainTriggered: typeof doc.chain_triggered === 'boolean' ? doc.chain_triggered : null,
    validation: doc.validation ?? null,
    validationRule: doc.validation_rule ?? null,
    vulnerabilities: doc.vulnerabilities ?? null,
    assessment: doc.assessment && Object.keys(doc.assessment).length ? doc.assessment : null,
    trustContext: doc.trust_context && Object.keys(doc.trust_context).length ? doc.trust_context : null,
    sharedMemory:
      doc.shared_memory_context && Object.keys(doc.shared_memory_context).length ? doc.shared_memory_context : null,
    timestamp: doc.timestamp ?? null,
  }
}

// ---------------------------------------------------------------------------
// Vulnerability explorer: catalog x findings x registered scenarios
// ---------------------------------------------------------------------------
export const SEVERITY_ORDER = ['critical', 'high', 'medium', 'low']
const sevRank = (s) => {
  const i = SEVERITY_ORDER.indexOf(s)
  return i < 0 ? SEVERITY_ORDER.length : i
}

// One row per catalog vulnerability (plus any observed test missing from the
// catalog, so nothing the backend reports is silently dropped).
export function aggregateVulnerabilities(findings = [], scenarios = []) {
  const catalog = [...VULNERABILITIES]
  const known = new Set(catalog.map((v) => v.test))
  findings.forEach((f) => {
    if (f?.test && !known.has(f.test)) {
      known.add(f.test)
      catalog.push({ id: '—', test: f.test, finding: f.finding ?? f.test, title: prettify(f.finding ?? f.test), uncatalogued: true })
    }
  })

  return catalog.map((v) => {
    const observations = findings.filter((f) => f.test === v.test)
    const confs = observations.map((o) => o.confidence).filter((c) => typeof c === 'number')
    const worst = observations.map((o) => o.severity).sort((a, b) => sevRank(a) - sevRank(b))[0] ?? null
    return {
      ...v,
      observations,
      count: observations.length,
      experiments: [...new Set(observations.map((o) => o.experiment_id))],
      severity: worst,
      avgConfidence: confs.length ? confs.reduce((a, b) => a + b, 0) / confs.length : null,
      control: CONTROL_FOR_TEST[v.test] ?? null,
      scenarios: scenarios.filter((s) => (s.steps ?? []).includes(v.test)),
    }
  })
}

export function filterVulnerabilities(rows, { query = '', severity = 'all', status = 'all', scenarioId = 'all' } = {}) {
  const needle = query.trim().toLowerCase()
  return rows.filter((r) => {
    if (severity !== 'all' && r.severity !== severity) return false
    if (status === 'observed' && r.count === 0) return false
    if (status === 'not_observed' && r.count > 0) return false
    if (scenarioId !== 'all' && !r.scenarios.some((s) => s.scenario_id === scenarioId)) return false
    if (!needle) return true
    const hay = [r.id, r.test, r.finding, r.control ?? '', ...r.observations.map((o) => evidenceText(o.evidence))]
    return hay.some((x) => String(x).toLowerCase().includes(needle))
  })
}
