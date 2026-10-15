import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync, existsSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import path from 'node:path'

import {
  VULNERABILITIES,
  chainEdges,
  buildChainGraph,
  matchingScenarios,
  isRegisteredChainId,
  normalizeAdaptiveRun,
  budgetMeters,
  hasStaticAdaptiveData,
  staticAdaptiveCounts,
  latestAblationRuns,
  ablationRateRows,
  ablationCostRows,
  ablationCaveats,
  isCleanAblation,
  normalizeAgentResult,
  latestFindingByTest,
  toPct,
} from './phase3.js'

const here = path.dirname(fileURLToPath(import.meta.url))

// ---------------------------------------------------------------- catalog drift
test('VULNERABILITIES mirrors sandbox VULNERABILITY_TEST_MAP and EXPECTED_FINDINGS', (t) => {
  const runner = path.resolve(here, '../../../sandbox/test_runner.py')
  const validator = path.resolve(here, '../../../sandbox/validator/chain_validator.py')
  if (!existsSync(runner) || !existsSync(validator)) return t.skip('sandbox sources not next to frontend')

  const mapSrc = readFileSync(runner, 'utf8').match(/VULNERABILITY_TEST_MAP\s*=\s*\{([\s\S]*?)\}/)[1]
  const pyMap = Object.fromEntries([...mapSrc.matchAll(/"(V\d+)":\s*"(\w+)"/g)].map((m) => [m[1], m[2]]))
  assert.equal(Object.keys(pyMap).length, 12)
  VULNERABILITIES.forEach((v) => assert.equal(pyMap[v.id], v.test, `${v.id} test`))
  assert.equal(VULNERABILITIES.length, 12)

  const expSrc = readFileSync(validator, 'utf8').match(/EXPECTED_FINDINGS\s*=\s*\{([\s\S]*?)\n\}/)[1]
  const pyExpected = Object.fromEntries(
    [...expSrc.matchAll(/"(\w+_test)":\s*\(?\s*"(\w+)"/g)].map((m) => [m[1], m[2]]),
  )
  VULNERABILITIES.forEach((v) => assert.equal(pyExpected[v.test], v.finding, `${v.test} finding`))
})

// ---------------------------------------------------------------- chain graph
const CHAIN = {
  chain_id: 'CHAIN-x1',
  steps: ['permission_test', 'tool_access_test', 'memory_access_test'],
}

test('chainEdges falls back to ordered edges labelled "order" without dependency data', () => {
  const edges = chainEdges(CHAIN)
  assert.deepEqual(
    edges.map((e) => [e.source, e.target, e.kind]),
    [
      ['permission_test', 'tool_access_test', 'order'],
      ['tool_access_test', 'memory_access_test', 'order'],
    ],
  )
})

test('chainEdges uses the stored dependency map and ignores unknown steps', () => {
  const edges = chainEdges({
    ...CHAIN,
    dependencies: {
      permission_test: [],
      tool_access_test: ['permission_test'],
      memory_access_test: ['tool_access_test', 'not_in_chain'],
    },
  })
  assert.deepEqual(
    edges.map((e) => `${e.source}>${e.target}:${e.kind}`),
    ['permission_test>tool_access_test:dependency', 'tool_access_test>memory_access_test:dependency'],
  )
})

test('buildChainGraph lays out by dependency depth and derives node status', () => {
  const g = buildChainGraph(
    { ...CHAIN, dependencies: { permission_test: [], tool_access_test: ['permission_test'], memory_access_test: ['tool_access_test'] } },
    {
      findings: [{ test: 'permission_test', finding: 'weak_permission_control', severity: 'high' }],
      validationSteps: [
        { test: 'permission_test', valid: true, dependency_valid: true },
        { test: 'tool_access_test', valid: false, dependency_valid: false, dependency_error: 'needs permission_test' },
      ],
    },
  )
  assert.equal(g.nodes.length, 3)
  const xs = g.nodes.map((n) => n.x)
  assert.ok(xs[0] < xs[1] && xs[1] < xs[2], 'strictly increasing x by depth')
  assert.deepEqual(g.nodes.map((n) => n.status), ['reproduced', 'failed', 'unknown'])
  const toolEdge = g.edges.find((e) => e.target.endsWith('tool_access_test'))
  assert.equal(toolEdge.satisfied, false)
  assert.equal(toolEdge.error, 'needs permission_test')
  assert.equal(g.edges.find((e) => e.target.endsWith('memory_access_test')).satisfied, undefined)
})

test('buildChainGraph without validation marks nodes with a finding as "finding"', () => {
  const g = buildChainGraph(CHAIN, { findings: [{ test: 'tool_access_test', finding: 'unsafe_tool_access' }] })
  assert.deepEqual(g.nodes.map((n) => n.status), ['unknown', 'finding', 'unknown'])
})

test('buildChainGraph survives a dependency cycle without hanging', () => {
  const g = buildChainGraph({
    chain_id: 'C',
    steps: ['a', 'b'],
    dependencies: { a: ['b'], b: ['a'] },
  })
  assert.equal(g.nodes.length, 2)
})

test('matchingScenarios requires identical ordered steps', () => {
  const scenarios = [
    { scenario_id: 'CHAIN_B', steps: ['permission_test', 'tool_access_test', 'memory_access_test'] },
    { scenario_id: 'CHAIN-AUTH-TOOL-MEM', steps: ['permission_test', 'tool_access_test', 'memory_access_test'] },
    { scenario_id: 'CHAIN_A', steps: ['permission_test', 'tool_access_test'] },
    { scenario_id: 'REORDERED', steps: ['tool_access_test', 'permission_test', 'memory_access_test'] },
  ]
  assert.deepEqual(matchingScenarios(CHAIN, scenarios).map((s) => s.scenario_id), ['CHAIN_B', 'CHAIN-AUTH-TOOL-MEM'])
  assert.equal(isRegisteredChainId('CHAIN_A', scenarios), true)
  assert.equal(isRegisteredChainId('CHAIN-x1', scenarios), false)
})

test('latestFindingByTest keeps the last finding per test', () => {
  const m = latestFindingByTest([
    { test: 'a', finding: 'old' },
    { test: 'a', finding: 'new' },
    { finding: 'no test' },
  ])
  assert.equal(m.a.finding, 'new')
  assert.equal(Object.keys(m).length, 1)
})

// ---------------------------------------------------------------- adaptive run
const START = {
  experiment_id: 'EXP010',
  status: 'completed',
  decisions: [
    { selected_test: 'permission_test', reason: 'baseline' },
    { selected_test: 'tool_access_test', reason: 'Fallback selected the highest-ranked candidate' },
    { selected_test: 'memory_access_test', reason: 'planned but cut' },
  ],
  decision_metadata: [
    { decision_source: 'gemini', fallback_reason: null, rag_retrieval_status: 'ok', rag_context_retrieved: true, rag_context_used: true },
    { decision_source: 'deterministic_fallback', fallback_reason: '429', rag_retrieval_status: 'failed', rag_context_retrieved: false, rag_context_used: false, decision_recovery: 'ranked_candidate_fallback' },
    { decision_source: 'gemini' },
  ],
  execution_results: [
    { status: 'completed', test: 'permission_test', finding: 'weak_permission_control', severity: 'high', confidence: 1, evidence: { a: 1 } },
    { status: 'completed', test: 'tool_access_test', finding: 'unsafe_tool_access', severity: 'high', confidence: 1, evidence: 'x' },
  ],
  budget_used: { tests: 2, llm_calls: 3, time_seconds: 31.2 },
  llm_calls: 3,
  fallback_used: true,
  candidate_chain: { chain_id: 'CHAIN-1', steps: ['permission_test', 'tool_access_test'] },
}

test('normalizeAdaptiveRun joins decisions, metadata and executions', () => {
  const r = normalizeAdaptiveRun(START)
  assert.equal(r.events.length, 3)
  assert.equal(r.events[0].source, 'gemini')
  assert.equal(r.events[0].result.finding, 'weak_permission_control')
  assert.equal(r.events[1].source, 'deterministic_fallback')
  assert.equal(r.events[1].recovery, 'ranked_candidate_fallback')
  assert.equal(r.fallbackDecisions, 1)
  assert.equal(r.events[2].executed, false)
  assert.equal(r.events[2].result, null)
  assert.equal(r.cutBeforeExecution, true)
  assert.deepEqual(r.budget, { tests: 2, llmCalls: 3, timeSeconds: 31.2 })
})

test('normalizeAdaptiveRun does not invent priority/confidence the loop drops', () => {
  const r = normalizeAdaptiveRun(START)
  assert.equal(r.events[0].priority, null)
  assert.equal(r.events[0].confidence, null)
  const withScores = normalizeAdaptiveRun({ ...START, decisions: [{ selected_test: 'permission_test', reason: '', priority: 0.8, confidence: 0.9 }] })
  assert.equal(withScores.events[0].priority, 0.8)
  assert.equal(withScores.events[0].confidence, 0.9)
})

test('normalizeAdaptiveRun tolerates missing/partial payloads', () => {
  assert.equal(normalizeAdaptiveRun(null), null)
  const r = normalizeAdaptiveRun({ experiment_id: 'E' })
  assert.deepEqual(r.events, [])
  assert.equal(r.cutBeforeExecution, false)
  assert.equal(r.budget.tests, 0)
})

test('budgetMeters only reports a cap for max_tests', () => {
  const m = budgetMeters(normalizeAdaptiveRun(START), { max_tests: 5 })
  assert.equal(m.find((x) => x.key === 'tests').cap, 5)
  assert.equal(m.find((x) => x.key === 'llm').cap, null)
  assert.equal(m.find((x) => x.key === 'time').cap, null)
  assert.deepEqual(budgetMeters(null, null), [])
})

// ---------------------------------------------------------------- static vs adaptive
test('static/adaptive helpers keep missing values null (no fabricated zeros)', () => {
  const empty = { static: { experiments: 0 }, adaptive: { experiments: 0 } }
  assert.equal(hasStaticAdaptiveData(empty), false)
  assert.equal(hasStaticAdaptiveData(null), false)
  const m = { static: { experiments: 1, total_findings: 3 }, adaptive: { experiments: 2, total_findings: 6, llm_calls: 4 } }
  assert.equal(hasStaticAdaptiveData(m), true)
  const rows = staticAdaptiveCounts(m)
  const findings = rows.find((r) => r.key === 'total_findings')
  assert.deepEqual([findings.Static, findings.Adaptive], [3, 6])
  const llm = rows.find((r) => r.key === 'llm_calls')
  assert.deepEqual([llm.Static, llm.Adaptive], [null, 4])
})

// ---------------------------------------------------------------- ablation
const rec = (configuration, extra = {}) => ({
  ablation_run_id: `ABL-${configuration}`,
  configuration,
  status: 'completed',
  fallback_used: false,
  selection_accuracy: 1,
  chain_discovery_rate: null,
  llm_calls: 3,
  latency: 12.5,
  ...extra,
})

test('latestAblationRuns orders A-D, takes the latest run, keeps run counts', () => {
  const runs = latestAblationRuns([
    rec('llm_rag_chain_context', { ablation_run_id: 'D1' }),
    rec('llm_only', { ablation_run_id: 'A1' }),
    rec('llm_only', { ablation_run_id: 'A2' }),
    { configuration: 'unknown_cfg' },
  ])
  assert.deepEqual(runs.map((r) => r.code), ['A', 'B', 'C', 'D'])
  assert.equal(runs[0].runs, 2)
  assert.equal(runs[0].record.ablation_run_id, 'A2')
  assert.equal(runs[1].record, null)
  assert.equal(runs[3].record.ablation_run_id, 'D1')
})

test('ablation chart rows leave gaps for missing configurations and metrics', () => {
  const runs = latestAblationRuns([rec('llm_only'), rec('llm_rag', { selection_accuracy: 0.3333 })])
  const rows = ablationRateRows(runs)
  const sel = rows.find((r) => r.metric === 'Selection accuracy')
  assert.equal(sel.A, 100)
  assert.equal(sel.B, 33.3)
  assert.equal(sel.C, null)
  assert.equal(rows.find((r) => r.metric === 'Chain discovery').A, null)
  const cost = ablationCostRows(runs, 'latency')
  assert.equal(cost[0].value, 12.5)
  assert.equal(cost[3].value, null)
})

test('ablation caveats flag fallback, incomplete status and missing runs; clean only when all four are fine', () => {
  const dirty = latestAblationRuns([
    rec('llm_only', { status: 'budget_exhausted' }),
    rec('llm_rag', { fallback_used: true }),
  ])
  const notes = ablationCaveats(dirty)
  assert.ok(notes.some((n) => n.startsWith('A:') && n.includes('budget_exhausted')))
  assert.ok(notes.some((n) => n.startsWith('B:') && n.includes('fell back')))
  assert.ok(notes.some((n) => n.startsWith('C (')))
  assert.equal(isCleanAblation(dirty), false)

  const clean = latestAblationRuns(['llm_only', 'llm_rag', 'llm_chain_context', 'llm_rag_chain_context'].map((c) => rec(c)))
  assert.equal(isCleanAblation(clean), true)
})

test('toPct rounds to one decimal and passes null through', () => {
  assert.equal(toPct(0.12345), 12.3)
  assert.equal(toPct(null), null)
  assert.equal(toPct(undefined), null)
})

// ---------------------------------------------------------------- multi-agent
const RUN_DOC = {
  experiment_id: 'EXP010',
  chain_id: 'MULTI-AGENT-CHAIN-V11-V10',
  agents: [
    { agent_id: 'AGENT_UNTRUSTED', role: 'Research', trust_level: 0.2, allowed_interactions: ['AGENT_CONTROLLED'], tools: ['search'], permissions: ['read'] },
    { agent_id: 'AGENT_CONTROLLED', role: 'Planning', trust_level: 0.9, allowed_interactions: [], tools: ['planner'], permissions: ['plan', 'delegate'] },
  ],
  communication: { status: 'delivered', sender: 'AGENT_UNTRUSTED', receiver: 'AGENT_CONTROLLED', message: 'Controlled delegation request.' },
  chain_steps: [
    { step: 1, vulnerability_id: 'V11', test: 'cross_agent_trust_test', finding: 'cross_agent_trust_weakness', status: 'triggered' },
    { step: 2, vulnerability_id: 'V10', test: 'unsafe_delegation_test', finding: 'unsafe_delegation', status: 'triggered' },
  ],
  expected_chain: ['V11', 'V10'],
  chain_triggered: true,
  validation: { valid: true, errors: [], chain_length: 2, validated_chain: true },
}

test('normalizeAgentResult: P4 scenario shape yields one delivered edge that crosses the trust boundary', () => {
  const r = normalizeAgentResult(RUN_DOC)
  assert.equal(r.agents.length, 2)
  assert.equal(r.edges.length, 1)
  assert.equal(r.edges[0].kind, 'delivered')
  assert.equal(r.edges[0].crossesTrustBoundary, true)
  assert.equal(r.edges[0].message, 'Controlled delegation request.')
  assert.equal(r.chainSteps.length, 2)
  assert.equal(r.chainTriggered, true)
  assert.equal(r.validation.validated_chain, true)
})

test('normalizeAgentResult: manual shape with free-form interactions and a denied message', () => {
  const r = normalizeAgentResult({
    experiment_id: 'E',
    status: 'completed',
    agents: [
      { agent_id: 'A', trust_level: 0.5, allowed_interactions: ['B'] },
      { agent_id: 'B', trust_level: 0.5, allowed_interactions: [] },
    ],
    interactions: [{ from: 'B', to: 'A', status: 'denied', message: 'not allowed' }],
    assessment: { risk: 'medium' },
    trust_context: {},
  })
  const byKey = Object.fromEntries(r.edges.map((e) => [`${e.from}>${e.to}`, e]))
  assert.equal(byKey['A>B'].kind, 'allowed')
  assert.equal(byKey['B>A'].kind, 'denied')
  assert.equal(byKey['A>B'].crossesTrustBoundary, false)
  assert.deepEqual(r.assessment, { risk: 'medium' })
  assert.equal(r.trustContext, null)
  assert.equal(r.chainTriggered, null)
})

test('normalizeAgentResult never downgrades a delivered edge to "allowed"', () => {
  const r = normalizeAgentResult({
    agents: [{ agent_id: 'A', allowed_interactions: ['B'] }, { agent_id: 'B' }],
    interactions: [{ sender: 'A', receiver: 'B', status: 'delivered' }, { sender: 'A', receiver: 'B', status: 'weird' }],
  })
  assert.equal(r.edges.length, 1)
  assert.equal(r.edges[0].kind, 'delivered')
  assert.equal(normalizeAgentResult(null), null)
})

// ---------------------------------------------------------------- vulnerability explorer
import { aggregateVulnerabilities, filterVulnerabilities } from './phase3.js'

const FINDINGS = [
  { experiment_id: 'EXP1', test: 'permission_test', finding: 'weak_permission_control', severity: 'high', confidence: 1, evidence: { permission: 'DENIED' } },
  { experiment_id: 'EXP2', test: 'permission_test', finding: 'weak_permission_control', severity: 'critical', confidence: 0.5, evidence: 'x' },
  { experiment_id: 'EXP1', test: 'brand_new_test', finding: 'brand_new', severity: 'low', confidence: 1, evidence: {} },
]
const SCENARIOS = [
  { scenario_id: 'CHAIN_A', steps: ['permission_test', 'tool_access_test'] },
  { scenario_id: 'CHAIN_C', steps: ['tool_access_test', 'prompt_injection_test'] },
]

test('aggregateVulnerabilities covers all 12 catalog entries plus unknown observed tests', () => {
  const rows = aggregateVulnerabilities(FINDINGS, SCENARIOS)
  assert.equal(rows.length, 13)
  const perm = rows.find((r) => r.test === 'permission_test')
  assert.equal(perm.count, 2)
  assert.equal(perm.severity, 'critical') // worst severity wins
  assert.equal(perm.avgConfidence, 0.75)
  assert.deepEqual(perm.experiments, ['EXP1', 'EXP2'])
  assert.equal(perm.control, 'authorization_gate')
  assert.deepEqual(perm.scenarios.map((s) => s.scenario_id), ['CHAIN_A'])
  const unseen = rows.find((r) => r.test === 'memory_access_test')
  assert.equal(unseen.count, 0)
  assert.equal(unseen.severity, null)
  assert.equal(unseen.avgConfidence, null)
  const extra = rows.find((r) => r.test === 'brand_new_test')
  assert.equal(extra.uncatalogued, true)
  assert.equal(extra.count, 1)
})

test('filterVulnerabilities: search, severity, status and scenario combine', () => {
  const rows = aggregateVulnerabilities(FINDINGS, SCENARIOS)
  assert.deepEqual(filterVulnerabilities(rows, { query: 'v2' }).map((r) => r.id), ['V2'])
  assert.deepEqual(filterVulnerabilities(rows, { query: 'DENIED' }).map((r) => r.id), ['V1']) // evidence search
  assert.deepEqual(filterVulnerabilities(rows, { severity: 'critical' }).map((r) => r.id), ['V1'])
  assert.equal(filterVulnerabilities(rows, { status: 'observed' }).length, 2)
  assert.equal(filterVulnerabilities(rows, { status: 'not_observed' }).length, 11)
  assert.deepEqual(filterVulnerabilities(rows, { scenarioId: 'CHAIN_C' }).map((r) => r.id), ['V2', 'V4'])
  assert.deepEqual(filterVulnerabilities(rows, { scenarioId: 'CHAIN_C', query: 'prompt' }).map((r) => r.id), ['V4'])
  assert.equal(filterVulnerabilities(rows, {}).length, 13)
})
