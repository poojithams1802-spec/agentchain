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