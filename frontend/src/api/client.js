import axios from 'axios'

// --------------------------------------------------------------------------
// AgentChain frontend API client
// Connected to Person 2's FastAPI backend.
// --------------------------------------------------------------------------

export const http = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
})

export async function listExperiments() {
  const { data } = await http.get('/experiments')
  return data
}

export async function getExperiment(id) {
  const { data } = await http.get(`/experiments/${id}`)
  return data
}

// Phase 3 fields (testing_budget, scenario_id, scenario_name, vulnerability_ids)
// are optional in ExperimentCreate; they are only sent when provided so Phase 1/2
// callers behave exactly as before.
export async function createExperiment({
  name,
  mode,
  max_tests,
  testing_budget,
  scenario_id,
  scenario_name,
  vulnerability_ids,
}) {
  const body = { name, mode, max_tests }
  if (testing_budget != null) body.testing_budget = testing_budget
  if (scenario_id) body.scenario_id = scenario_id
  if (scenario_name) body.scenario_name = scenario_name
  if (vulnerability_ids?.length) body.vulnerability_ids = vulnerability_ids
  const { data } = await http.post('/experiments', body)
  return data
}

// Adaptive runs call the LLM planner several times, so allow a long timeout.
export async function startExperiment(id) {
  const { data } = await http.post(`/experiments/${id}/start`, null, { timeout: 300000 })
  return data
}

export async function getExperimentStatus(id) {
  const { data } = await http.get(`/experiments/${id}/status`)
  return data
}

export async function getExperimentLogs(id) {
  const { data } = await http.get(`/experiments/${id}/logs`)
  return data
}

export async function getExperimentFindings(id) {
  const { data } = await http.get(`/experiments/${id}/findings`)
  return data
}

export async function getExperimentChains(id) {
  const { data } = await http.get(`/experiments/${id}/chains`)
  return data
}

export async function validateChain(chainId) {
  const { data } = await http.post(`/chains/${chainId}/validate`)
  return data
}

export async function getAnalytics() {
  const { data } = await http.get('/analytics')
  return data
}

// ---------------- Phase 2: mitigation ----------------
export function apiError(e) {
  const d = e?.response?.data?.detail
  if (typeof d === 'string') return d
  if (Array.isArray(d)) return d.map((x) => x.msg).join('; ')
  return e?.message || 'Request failed'
}

// Selection calls the LLM + RAG and can take ~1 minute, so use a long timeout.
const SLOW = { timeout: 180000 }

export async function selectMitigation(experimentId, body) {
  const { data } = await http.post(`/experiments/${experimentId}/mitigation/select`, body, SLOW)
  return data
}

export async function applyMitigation(experimentId, body) {
  const { data } = await http.post(`/experiments/${experimentId}/mitigation/apply`, body, SLOW)
  return data
}

export async function replayMitigation(experimentId, body) {
  const { data } = await http.post(`/experiments/${experimentId}/mitigation/replay`, body, SLOW)
  return data
}

export async function getMitigationResult(experimentId, mitigationRunId) {
  const { data } = await http.get(`/experiments/${experimentId}/mitigation/result`, {
    params: { mitigation_run_id: mitigationRunId },
  })
  return data
}

// Expected: GET /phase2/analytics -> { metrics, records } (see README_PHASE2_FRONTEND.md).
// Falls back to a bundled snapshot if the endpoint does not exist yet.
export async function getPhase2Analytics() {
  const { data } = await http.get('/phase2/analytics')
  return { ...data, source: 'live' }
}

// ---------------- Phase 3 ----------------
// All endpoints below already exist in backend/app/main.py.

// GET /scenarios -> { scenarios: [{ scenario_id, scenario_name, description, chain_ids, steps }] }
export async function listScenarios() {
  const { data } = await http.get('/scenarios')
  return data.scenarios ?? []
}

// POST /experiments/{id}/chains/execute (only registered P4 chain ids work)
export async function executeChain(experimentId, chainId) {
  const { data } = await http.post(`/experiments/${experimentId}/chains/execute`, { chain_id: chainId }, SLOW)
  return data
}

// POST /experiments/{id}/chains/{chain_id}/p4-association
export async function associateChainWithP4(experimentId, chainId, p4ChainId) {
  const { data } = await http.post(`/experiments/${experimentId}/chains/${chainId}/p4-association`, {
    p4_chain_id: p4ChainId,
  })
  return data
}

// POST /experiments/{id}/chains/mitigation/replay (full-chain replay)
export async function replayChainMitigation(experimentId, chainId, controlName) {
  const { data } = await http.post(
    `/experiments/${experimentId}/chains/mitigation/replay`,
    { chain_id: chainId, control_name: controlName },
    SLOW,
  )
  return data
}

// GET /phase3/analytics -> { metrics: { static, adaptive }, records }
export async function getPhase3Analytics() {
  const { data } = await http.get('/phase3/analytics')
  return data
}

// GET /phase3/ablation/aggregation -> { study, configuration_order, configuration_count, comparisons }
export async function getAblationAggregation() {
  const { data } = await http.get('/phase3/ablation/aggregation')
  return data
}

// ---------------- Phase 3: multi-agent ----------------
// 404 means nothing has been persisted for the experiment yet; callers treat it as "empty".
export async function getAgentSecurityResult(experimentId) {
  const { data } = await http.get(`/experiments/${experimentId}/agents/security-result`)
  return data
}

export async function getAgentState(experimentId) {
  const { data } = await http.get(`/experiments/${experimentId}/agents/state`)
  return data
}

// Runs P4's controlled V11 -> V10 scenario and persists it.
export async function runAgentSecurityScenario(experimentId) {
  const { data } = await http.post(`/experiments/${experimentId}/agents/security-result/run`, null, SLOW)
  return data
}

export const isNotFound = (e) => e?.response?.status === 404
