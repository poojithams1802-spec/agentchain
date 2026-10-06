import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { Loader2, Play, ShieldCheck, Crosshair, RotateCcw, AlertTriangle } from 'lucide-react'
import TopBar from '../components/TopBar'
import { SeverityBadge, StatusBadge } from '../components/Badges'
import { LoadingState, ErrorState, EmptyState } from '../components/States'
import { ControlBadge, Stepper } from '../components/MitigationParts'
import {
  listExperiments, getExperimentChains, getExperimentFindings, selectMitigation,
  applyMitigation, replayMitigation, getMitigationResult, apiError,
} from '../api/client'
import { CONTROLS, loadRuns, saveRun } from '../lib/mitigation'

const STEPS = ['Choose target', 'Select control', 'Apply control', 'Replay same attack', 'Result']

export default function Mitigation() {
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const [experiments, setExperiments] = useState(null)
  const [loadError, setLoadError] = useState(null)
  const [expId, setExpId] = useState(params.get('exp') ?? '')
  const [chains, setChains] = useState([])
  const [findings, setFindings] = useState([])
  const [chainId, setChainId] = useState('')
  const [testName, setTestName] = useState('')
  const [run, setRun] = useState(null) // { id, selection, application }
  const [busy, setBusy] = useState(null)
  const [elapsed, setElapsed] = useState(0)
  const [error, setError] = useState(null)
  const [recent, setRecent] = useState(loadRuns())

  useEffect(() => {
    listExperiments().then(setExperiments).catch((e) => setLoadError(apiError(e)))
  }, [])

  // Load chains and findings for the chosen experiment.
  useEffect(() => {
    if (!expId) return
    setChains([]); setFindings([]); setChainId(''); setTestName('')
    Promise.all([getExperimentChains(expId), getExperimentFindings(expId)])
      .then(([c, f]) => {
        setChains(c); setFindings(f)
        if (c[0]) setChainId(c[0].chain_id)
      })
      .catch((e) => setError(apiError(e)))
  }, [expId])

  // Resume an unfinished run from ?exp=..&run=..
  useEffect(() => {
    const id = params.get('run')
    if (!id || !params.get('exp')) return
    getMitigationResult(params.get('exp'), id)
      .then((r) => {
        setChainId(r.chain_id)
        setRun({ id: r.mitigation_run_id, selection: r.selection, application: r.application })
      })
      .catch((e) => setError(apiError(e)))
  }, [params])

  useEffect(() => {
    if (!busy) return
    setElapsed(0)
    const t = setInterval(() => setElapsed((s) => s + 1), 1000)
    return () => clearInterval(t)
  }, [busy])

  const chain = chains.find((c) => c.chain_id === chainId)
  // Latest finding per test, in chain order.
  const chainFindings = useMemo(() => {
    if (!chain) return []
    const byTest = {}
    findings.forEach((f) => { byTest[f.test] = f })
    return chain.steps.map((s) => byTest[s]).filter(Boolean)
  }, [chain, findings])
  const target = chainFindings.find((f) => f.test === testName)

  useEffect(() => {
    if (chainFindings.length && !chainFindings.some((f) => f.test === testName)) setTestName(chainFindings[0].test)
  }, [chainFindings, testName])

  const stage = run?.application ? 3 : run ? 2 : target ? 1 : 0

  async function step(name, fn) {
    setBusy(name); setError(null)
    try {
      await fn()
    } catch (e) {
      setError(`${name} failed: ${apiError(e)}`)
    } finally {
      setBusy(null)
    }
  }

  const doSelect = () => step('Selection', async () => {
    const t0 = performance.now()
    const r = await selectMitigation(expId, {
      chain_id: chainId,
      finding: target.finding,
      severity: target.severity,
      evidence: target.evidence,
      attack_chain: chain.steps,
      chain_context: { chain_length: chain.steps.length, current_stage: 'mitigation_selection' },
    })
    setRun({ id: r.mitigation_run_id, selection: r, application: null })
    saveRun({
      mitigation_run_id: r.mitigation_run_id, experiment_id: expId, chain_id: chainId,
      control: r.selected_control, finding: target.finding, created_at: new Date().toISOString(),
      timings: { select: (performance.now() - t0) / 1000 },
    })
    setRecent(loadRuns())
  })

  const doApply = () => step('Apply', async () => {
    const t0 = performance.now()
    const r = await applyMitigation(expId, { mitigation_run_id: run.id, selected_control: run.selection.selected_control })
    setRun({ ...run, application: r })
    saveRun({ mitigation_run_id: run.id, timings: { apply: (performance.now() - t0) / 1000 } })
  })

  const doReplay = () => step('Replay', async () => {
    const t0 = performance.now()
    // The backend only accepts the test that belongs to the selected control.
    await replayMitigation(expId, { mitigation_run_id: run.id, test: CONTROLS[run.selection.selected_control].test })
    saveRun({ mitigation_run_id: run.id, timings: { replay: (performance.now() - t0) / 1000 } })
    navigate(`/mitigation/${expId}/${run.id}`)
  })

  function reset() { setRun(null); setError(null) }

  const done = experiments?.filter((e) => e.status === 'completed') ?? []

  return (
    <>
      <TopBar title="Mitigation Workflow" subtitle="Select a predefined control, apply it in the sandbox, replay the same attack" />
      <main className="flex-1 overflow-y-auto scrollbar-thin p-6 space-y-6">
        <Stepper steps={STEPS} current={stage} />

        {loadError && <ErrorState message={loadError} onRetry={() => location.reload()} />}
        {!experiments && !loadError && <LoadingState label="Loading experiments…" />}
        {experiments && done.length === 0 && (
          <EmptyState title="No completed experiments" description="Run an experiment first so an attack chain exists to mitigate."
            action={<Link to="/new-experiment" className="text-signal text-xs underline">Create experiment</Link>} />
        )}

        {done.length > 0 && (
          <section className="bg-base-900 border border-base-700 rounded-lg p-4 space-y-4">
            <h2 className="text-sm font-semibold flex items-center gap-2"><Crosshair size={14} className="text-signal" />1 · Target</h2>
            <div className="grid md:grid-cols-3 gap-3 text-sm">
              <label className="space-y-1"><span className="text-xs text-base-400">Experiment</span>
                <select disabled={!!run} value={expId} onChange={(e) => setExpId(e.target.value)}
                  className="w-full bg-base-800 border border-base-600 rounded px-2 py-1.5">
                  <option value="">Select…</option>
                  {done.map((e) => <option key={e.experiment_id} value={e.experiment_id}>{e.experiment_id} · {e.name}</option>)}
                </select></label>
              <label className="space-y-1"><span className="text-xs text-base-400">Attack chain</span>
                <select disabled={!!run} value={chainId} onChange={(e) => setChainId(e.target.value)}
                  className="w-full bg-base-800 border border-base-600 rounded px-2 py-1.5">
                  {chains.map((c) => <option key={c.chain_id} value={c.chain_id}>{c.chain_id}</option>)}
                </select></label>
              <label className="space-y-1"><span className="text-xs text-base-400">Finding to mitigate</span>
                <select disabled={!!run} value={testName} onChange={(e) => setTestName(e.target.value)}
                  className="w-full bg-base-800 border border-base-600 rounded px-2 py-1.5">
                  {chainFindings.map((f) => <option key={f.test} value={f.test}>{f.finding}</option>)}
                </select></label>
            </div>
            {chain && (
              <div className="flex flex-wrap items-center gap-2 text-xs font-mono text-base-300">
                {chain.steps.map((s, i) => <span key={s} className="flex items-center gap-2">{i > 0 && '→'}<span className="px-2 py-0.5 rounded bg-base-800 border border-base-600">{s}</span></span>)}
              </div>
            )}
            {target && (
              <div className="text-xs bg-base-800 rounded p-3 space-y-1">
                <div className="flex items-center gap-2"><span className="font-mono">{target.finding}</span><SeverityBadge severity={target.severity} /></div>
                <div className="font-mono text-base-300 break-words">{typeof target.evidence === 'object' ? JSON.stringify(target.evidence) : String(target.evidence)}</div>
              </div>
            )}
            {chain && chainFindings.length === 0 && <p className="text-xs text-sev-medium">No findings were stored for this chain's steps.</p>}
          </section>
        )}

        {target && (
          <section className="bg-base-900 border border-base-700 rounded-lg p-4 space-y-3">
            <h2 className="text-sm font-semibold flex items-center gap-2"><ShieldCheck size={14} className="text-signal" />2 · LLM + Security RAG selects a predefined control</h2>
            {!run && (
              <button onClick={doSelect} disabled={!!busy}
                className="inline-flex items-center gap-2 btn-primary font-medium text-sm rounded px-3 py-1.5 disabled:opacity-50">
                {busy === 'Selection' ? <Loader2 size={14} className="animate-spin" /> : <Play size={14} />} Select control
              </button>
            )}
            {busy === 'Selection' && <p className="text-xs text-base-400">The LLM is reasoning over the attack chain… {elapsed}s (this can take about a minute)</p>}
            {run && (
              <div className="space-y-2 text-sm">
                <div className="flex items-center gap-3"><ControlBadge control={run.selection.selected_control} />
                  <span className="text-xs font-mono text-base-300">confidence {Number(run.selection.confidence).toFixed(2)}</span>
                  <span className="text-xs font-mono text-base-400">{run.id}</span></div>
                <p className="text-base-200 text-sm">{run.selection.reason}</p>
                <p className="text-xs text-base-400">{CONTROLS[run.selection.selected_control]?.desc}</p>
              </div>
            )}
          </section>
        )}

        {run && (
          <section className="bg-base-900 border border-base-700 rounded-lg p-4 space-y-3">
            <h2 className="text-sm font-semibold">3 · Apply control · 4 · Replay the same attack</h2>
            <div className="flex flex-wrap items-center gap-3">
              <button onClick={doApply} disabled={!!busy || !!run.application}
                className="inline-flex items-center gap-2 border border-signal/50 text-signal text-sm rounded px-3 py-1.5 disabled:opacity-40">
                {busy === 'Apply' && <Loader2 size={14} className="animate-spin" />} Apply control
              </button>
              <button onClick={doReplay} disabled={!!busy || !run.application}
                className="inline-flex items-center gap-2 btn-primary font-medium text-sm rounded px-3 py-1.5 disabled:opacity-40">
                {busy === 'Replay' && <Loader2 size={14} className="animate-spin" />} Replay {CONTROLS[run.selection.selected_control]?.test}
              </button>
              {run.application && <StatusBadge status={run.application.status} />}
              <button onClick={reset} disabled={!!busy} className="ml-auto inline-flex items-center gap-1 text-xs text-base-300 hover:text-base-100">
                <RotateCcw size={12} /> Start over
              </button>
            </div>
            {busy && busy !== 'Selection' && <p className="text-xs text-base-400">{busy} in progress… {elapsed}s</p>}
          </section>
        )}

        {error && (
          <div className="flex items-start gap-2 text-sm text-sev-high border border-sev-high/30 bg-sev-high/10 rounded p-3">
            <AlertTriangle size={16} className="mt-0.5 shrink-0" /><span>{error}</span>
          </div>
        )}

        <section>
          <h2 className="text-sm font-semibold mb-2">Recent mitigation runs (this browser)</h2>
          {recent.length === 0 ? <p className="text-xs text-base-400">None yet.</p> : (
            <div className="border border-base-700 rounded-lg divide-y divide-base-700">
              {recent.slice(0, 8).map((r) => (
                <Link key={r.mitigation_run_id} to={`/mitigation/${r.experiment_id}/${r.mitigation_run_id}`}
                  className="flex items-center gap-3 px-3 py-2 text-xs hover:bg-base-800/60">
                  <span className="font-mono">{r.mitigation_run_id}</span>
                  <span className="text-base-400">{r.experiment_id}</span>
                  <ControlBadge control={r.control} />
                  <span className="ml-auto text-base-400">{new Date(r.created_at).toLocaleString()}</span>
                </Link>
              ))}
            </div>
          )}
        </section>
      </main>
    </>
  )
}
