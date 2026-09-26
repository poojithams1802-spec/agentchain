import axios from 'axios'
import experiments from '../mock/experiments.json'
import findings from '../mock/findings.json'
import chains from '../mock/chains.json'
import logs from '../mock/logs.json'
import analytics from '../mock/analytics.json'

// --------------------------------------------------------------------------
// AgentChain frontend API client (Person 1)
//
// Every function here mirrors an endpoint from Section 6, "Shared API &
// Data Contract", in AGENTCHAIN_TEAM_IMPLEMENTATION.md. Right now each one
// resolves against local mock JSON so the whole UI works standalone from
// Day 1, per the doc's instruction to "Use mock JSON until backend
// endpoints are available, then replace with Axios API calls."
//
// TO INTEGRATE WITH PERSON 2'S BACKEND:
// Set USE_MOCK = false once /experiments etc. are live. Nothing else in
// the app needs to change — every page calls these functions, not the
// mock files directly.
// --------------------------------------------------------------------------

const USE_MOCK = true

export const http = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
})

const delay = (ms = 300) => new Promise((res) => setTimeout(res, ms))

export async function listExperiments() {
  if (USE_MOCK) {
    await delay()
    return experiments
  }
  const { data } = await http.get('/experiments')
  return data
}

export async function getExperiment(id) {
  if (USE_MOCK) {
    await delay()
    const exp = experiments.find((e) => e.experiment_id === id)
    if (!exp) throw new Error('Experiment not found')
    return exp
  }
  const { data } = await http.get(`/experiments/${id}`)
  return data
}

export async function createExperiment({ name, mode, max_tests }) {
  if (USE_MOCK) {
    await delay()
    return { experiment_id: `EXP${Math.floor(Math.random() * 900 + 100)}`, status: 'created' }
  }
  const { data } = await http.post('/experiments', { name, mode, max_tests })
  return data
}

export async function startExperiment(id) {
  if (USE_MOCK) {
    await delay()
    return { experiment_id: id, status: 'running' }
  }
  const { data } = await http.post(`/experiments/${id}/start`)
  return data
}

export async function getExperimentStatus(id) {
  if (USE_MOCK) {
    await delay()
    const exp = experiments.find((e) => e.experiment_id === id)
    return { experiment_id: id, status: exp?.status ?? 'unknown' }
  }
  const { data } = await http.get(`/experiments/${id}/status`)
  return data
}

export async function getExperimentLogs(id) {
  if (USE_MOCK) {
    await delay()
    return logs.filter((l) => l.experiment_id === id)
  }
  const { data } = await http.get(`/experiments/${id}/logs`)
  return data
}

export async function getExperimentFindings(id) {
  if (USE_MOCK) {
    await delay()
    return findings.filter((f) => f.experiment_id === id)
  }
  const { data } = await http.get(`/experiments/${id}/findings`)
  return data
}

export async function getAllFindings() {
  if (USE_MOCK) {
    await delay()
    return findings
  }
  const { data } = await http.get('/findings')
  return data
}

export async function getExperimentChains(id) {
  if (USE_MOCK) {
    await delay()
    return chains.filter((c) => c.experiment_id === id)
  }
  const { data } = await http.get(`/experiments/${id}/chains`)
  return data
}

export async function getAllChains() {
  if (USE_MOCK) {
    await delay()
    return chains
  }
  const { data } = await http.get('/chains')
  return data
}

export async function validateChain(chainId) {
  if (USE_MOCK) {
    await delay(600)
    return { chain_id: chainId, status: 'validated', validated_steps: 3 }
  }
  const { data } = await http.post(`/chains/${chainId}/validate`)
  return data
}

export async function getAnalytics() {
  if (USE_MOCK) {
    await delay()
    return analytics
  }
  const { data } = await http.get('/analytics')
  return data
}
