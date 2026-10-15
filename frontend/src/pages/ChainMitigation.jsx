import { useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { Loader2, Link2, ShieldCheck, Download } from 'lucide-react'
import TopBar from '../components/TopBar'
import StatCard from '../components/StatCard'
import { LoadingState, ErrorState, EmptyState } from '../components/States'
import { Panel, Notice, Chip, JsonBlock } from '../components/Phase3Parts'
import { ReplayVerdict, ChainBeforeAfter, StepValidationTable } from '../components/ChainReplayParts'
import {
  listExperiments,
  getExperimentChains,
  listScenarios,
  associateChainWithP4,
  replayChainMitigation,
  apiError,
} from '../api/client'
import { CONTROLS, controlLabel } from '../lib/mitigation'
import { matchingScenarios, fmtPct } from '../lib/phase3'

export default function ChainMitigation() {
  const [params, setParams] = useSearchParams()
  const [exps, setExps] = useState({ loading: true, error: null, items: [] })
  const [chains, setChains] = useState([])
  const [scenarios, setScenarios] = useState([])
  const [p4Choice, setP4Choice] = useState('')
  const [control, setControl] = useState('')
  const [busy, setBusy] = useState(null)
  const [elapsed, setElapsed] = useState(0)
  const [error, setError] = useState(null)
  const [result, setResult] = useState(null)

  const expId = params.get('exp') ?? ''
  const chainId = params.get('chain') ?? ''
  const setParam = (k, v) => {
    const next = new URLSearchParams(params)
    v ? next.set(k, v) : next.delete(k)
    if (k === 'exp') next.delete('chain')
    setParams(next, { replace: true })
    setResult(null)
    setError(null)
  }

  useEffect(() => {
    Promise.all([listExperiments(), listScenarios().catch(() => [])])
      .then(([items, sc]) => {
        setExps({ loading: false, error: null, items })
        setScenarios(sc)
      })
      .catch((e) => setExps({ loading: false, error: apiError(e), items: [] }))
  }, [])

  useEffect(() => {
    setChains([])
    if (!expId) return
    getExperimentChains(expId).then(setChains).catch((e) => setError(apiError(e)))
  }, [expId])

  useEffect(() => {
    if (!busy) return
    setElapsed(0)
    const t = setInterval(() => setElapsed((s) => s + 1), 1000)
    return () => clearInterval(t)
  }, [busy])

  const chain = chains.find((c) => c.chain_id === chainId)
  const candidates = useMemo(() => matchingScenarios(chain, scenarios), [chain, scenarios])
  const associated = chain?.p4_chain_id ?? null
  const targetTest = control ? CONTROLS[control].test : null
  const controlHitsChain = !!(chain && targetTest && chain.steps.includes(targetTest))
  const done = exps.items.filter((e) => e.status === 'completed')

  async function doAssociate() {
    setBusy('associate'); setError(null)
    try {
      const r = await associateChainWithP4(expId, chainId, p4Choice)
      // Re-read so the stored dependency map is reflected.
      setChains(await getExperimentChains(expId))
      setP4Choice(r.p4_chain_id)
    } catch (e) {
      setError(`Association failed: ${apiError(e)}`)
    } finally { setBusy(null) }
  }

  async function doReplay() {
    setBusy('replay'); setError(null); setResult(null)
    try {
      setResult(await replayChainMitigation(expId, chainId, control))
    } catch (e) {
      setError(`Replay failed: ${apiError(e)}`)
    } finally { setBusy(null) }
  }

  function exportJson() {
    const url = URL.createObjectURL(new Blob([JSON.stringify(result, null, 2)], { type: 'application/json' }))
    const a = Object.assign(document.createElement('a'), { href: url, download: `chain_replay_${chainId}_${control}.json` })
    a.click()
    URL.revokeObjectURL(url)
  }

  const selectCls = 'w-full bg-base-800 border border-base-600 rounded px-2 py-1.5 text-sm'

  return (
    <>
      <TopBar
        title="Chain Mitigation"
        subtitle="Apply one predefined control, replay the whole chain, compare before and after"
        actions={
          <Link to="/mitigation" className="text-xs text-signal hover:underline">
            Single-step workflow with LLM control selection →
          </Link>
        }
      />
      <main className="flex-1 overflow-y-auto scrollbar-thin p-6 space-y-6">
        {exps.loading && <LoadingState label="Loading experiments…" />}
        {exps.error && <ErrorState message={exps.error} onRetry={() => location.reload()} />}
        {!exps.loading && !exps.error && done.length === 0 && (
          <EmptyState title="No completed experiments" description="Run an experiment first so a chain exists to replay."
            action={<Link to="/new-experiment" className="text-signal text-xs underline">Create experiment</Link>} />
        )}

        {done.length > 0 && (
          <Panel title="1 · Target chain">
            <div className="grid md:grid-cols-2 gap-3">
              <label className="space-y-1 text-sm"><span className="text-xs text-base-400">Experiment</span>
                <select className={selectCls} value={expId} onChange={(e) => setParam('exp', e.target.value)}>
                  <option value="">Select…</option>
                  {done.map((e) => <option key={e.experiment_id} value={e.experiment_id}>{e.experiment_id} · {e.name}</option>)}
                </select></label>
              <label className="space-y-1 text-sm"><span className="text-xs text-base-400">Attack chain</span>
                <select className={selectCls} value={chainId} onChange={(e) => setParam('chain', e.target.value)} disabled={!expId}>
                  <option value="">Select…</option>
                  {chains.map((c) => <option key={c.chain_id} value={c.chain_id}>{c.chain_id}</option>)}
                </select></label>
            </div>
            {expId && chains.length === 0 && !error && <p className="text-xs text-base-400 mt-3">This experiment has no chains.</p>}
            {chain && (
              <div className="flex flex-wrap items-center gap-2 mt-3 text-xs font-mono text-base-300">
                {chain.steps.map((s, i) => (
                  <span key={s} className="flex items-center gap-2">{i > 0 && '→'}
                    <span className="px-2 py-0.5 rounded bg-base-800 border border-base-600">{s}</span></span>
                ))}
              </div>
            )}
          </Panel>
        )}

        {chain && (
          <Panel
            title="2 · P4 chain definition"
            subtitle="The replay runs a registered P4 chain. The stored chain must be explicitly associated with one that has identical ordered steps."
          >
            {associated ? (
              <div className="flex flex-wrap items-center gap-2 text-sm">
                <Chip tone="good"><Link2 size={11} /> associated</Chip>
                <span className="font-mono text-base-100">{associated}</span>
                <span className="text-xs text-base-400">dependencies stored: {chain.dependencies ? 'yes' : 'no'}</span>
              </div>
            ) : candidates.length === 0 ? (
              <Notice tone="warn" title="No compatible registered definition">
                No P4 chain has exactly these steps in this order, so a full-chain replay is not possible for this chain.
              </Notice>
            ) : (
              <div className="space-y-2">
                <div className="grid sm:grid-cols-2 gap-2">
                  {candidates.map((s) => (
                    <button key={s.scenario_id} type="button" onClick={() => setP4Choice(s.scenario_id)} aria-pressed={p4Choice === s.scenario_id}
                      className={`text-left rounded-md border px-3 py-2 text-xs ${p4Choice === s.scenario_id ? 'border-signal bg-signal/10' : 'border-base-700 hover:border-base-500'}`}>
                      <div className="font-mono text-base-100">{s.scenario_id}</div>
                      <div className="text-base-400 mt-0.5">{s.scenario_name}</div>
                    </button>
                  ))}
                </div>
                <button onClick={doAssociate} disabled={!p4Choice || !!busy}
                  className="inline-flex items-center gap-2 btn-primary text-sm rounded px-3 py-1.5 disabled:opacity-50">
                  {busy === 'associate' && <Loader2 size={14} className="animate-spin" />} Associate with {p4Choice || 'selected definition'}
                </button>
              </div>
            )}
          </Panel>
        )}

        {chain && associated && (
          <Panel title="3 · Defensive control" subtitle="Only these three predefined controls exist. Each one blocks a single test.">
            <div className="grid md:grid-cols-3 gap-2">
              {Object.entries(CONTROLS).map(([key, c]) => {
                const inChain = chain.steps.includes(c.test)
                return (
                  <button key={key} type="button" onClick={() => { setControl(key); setResult(null) }} aria-pressed={control === key}
                    className={`text-left rounded-md border px-3 py-2.5 text-sm ${control === key ? 'border-signal bg-signal/10' : 'border-base-700 hover:border-base-500'}`}>
                    <div className={control === key ? 'text-signal font-medium' : 'text-base-100 font-medium'}>{c.label}</div>
                    <div className="text-[11px] text-base-400 mt-1">{c.desc}</div>
                    <div className="mt-2 flex items-center gap-1.5">
                      <Chip>blocks {c.test}</Chip>
                      {!inChain && <Chip tone="warn">not in this chain</Chip>}
                    </div>
                  </button>
                )
              })}
            </div>
            {control && !controlHitsChain && (
              <div className="mt-3"><Notice tone="warn">
                {controlLabel(control)} targets {targetTest}, which is not a step in this chain. Replaying it is allowed and is
                expected to disrupt nothing; this is a useful wrong-control check.
              </Notice></div>
            )}
            <div className="mt-4 flex items-center gap-3">
              <button onClick={doReplay} disabled={!control || !!busy}
                className="inline-flex items-center gap-2 btn-primary text-sm rounded px-3 py-1.5 disabled:opacity-50">
                {busy === 'replay' ? <Loader2 size={14} className="animate-spin" /> : <ShieldCheck size={14} />} Apply control and replay chain
              </button>
              {busy === 'replay' && <span className="text-xs text-base-400">Replaying in the sandbox… {elapsed}s</span>}
            </div>
          </Panel>
        )}

        {error && <Notice tone="bad">{error}</Notice>}

        {result && (
          <>
            <ReplayVerdict result={result} />
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
              <StatCard label="Control" value={<span className="text-base">{controlLabel(result.control)}</span>} sub={result.p4_chain_id} />
              <StatCard label="Chain disrupted" value={result.chain_disrupted ? 'YES' : 'NO'} accent={result.chain_disrupted ? '#5B9E6F' : '#E5484D'} />
              <StatCard label="Blocked steps" value={result.blocked_steps?.length ?? 0} sub={result.blocked_steps?.join(', ') || 'none'} />
              <StatCard label="Residual vulnerable steps" value={result.residual_vulnerable_steps?.length ?? 0} sub={result.residual_vulnerable_steps?.join(', ') || 'none'}
                accent={result.residual_vulnerable_steps?.length ? '#E8734D' : undefined} />
            </div>
            {result.chain_disrupted && result.residual_vulnerable_steps?.length > 0 && (
              <Notice tone="info">
                The chain is disrupted, but the residual steps above are still individually exploitable. A control blocks one
                step; it does not remove the other weaknesses.
              </Notice>
            )}

            <Panel title="Before vs after (whole chain)"><ChainBeforeAfter result={result} /></Panel>
            <Panel title="Step-level validation">
              <StepValidationTable before={result.before_validation} after={result.after_validation} blocked={result.blocked_steps} />
              <div className="flex flex-wrap gap-2 mt-3 text-xs">
                <Chip>validation: {result.validation_result?.status}</Chip>
                <Chip>rate {fmtPct(result.validation_result?.validation_rate)}</Chip>
                <Chip>attack_blocked {String(result.validation_result?.attack_blocked)}</Chip>
                <Chip>reset: {result.reset?.status ?? '—'}</Chip>
              </div>
            </Panel>
            <Panel
              title="Evidence"
              actions={<button onClick={exportJson} className="inline-flex items-center gap-1.5 text-xs border border-base-600 rounded px-2.5 py-1.5 hover:bg-base-800"><Download size={12} />JSON</button>}
            >
              <div className="grid md:grid-cols-2 gap-3 text-xs">
                <div><div className="text-base-400 mb-1">Control activation</div><JsonBlock value={result.activation} /></div>
                <div><div className="text-base-400 mb-1">Reset</div><JsonBlock value={result.reset} /></div>
              </div>
            </Panel>
          </>
        )}
      </main>
    </>
  )
}
