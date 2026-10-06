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

export async function createExperiment({ name, mode, max_tests }) {
  const { data } = await http.post('/experiments', {
    name,
    mode,
    max_tests,
  })
  return data
}

export async function startExperiment(id) {
  const { data } = await http.post(`/experiments/${id}/start`)
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