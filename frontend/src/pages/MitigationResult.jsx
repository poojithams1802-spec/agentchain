import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import TopBar from '../components/TopBar'
import StatCard from '../components/StatCard'
import { LoadingState, ErrorState } from '../components/States'
import { StatusBadge } from '../components/Badges'
import { ControlBadge, BeforeAfter, ChainDisruption, Verdict } from '../components/MitigationParts'
import { getMitigationResult, getExperimentChains, apiError } from '../api/client'
import { getRun, controlLabel } from '../lib/mitigation'

const sec = (v) => (v == null ? '—' : `${v.toFixed(1)}s`)

export default function MitigationResult() {
  const { experimentId, runId } = useParams()
  const [state, setState] = useState({ loading: true, error: null, run: null, steps: [] })

  async function load() {
    setState({ loading: true, error: null, run: null, steps: [] })
    try {
      const run = await getMitigationResult(experimentId, runId)
      let steps = run.attack_chain_context?.steps ?? []
      if (!steps.length) {
        const chains = await getExperimentChains(experimentId)
        steps = chains.find((c) => c.chain_id === run.chain_id)?.steps ?? []
      }
      setState({ loading: false, error: null, run, steps })
    } catch (e) {
      setState({ loading: false, error: apiError(e), run: null, steps: [] })
    }
  }
  useEffect(() => { load() }, [experimentId, runId])

  const { loading, error, run, steps } = state
  const timings = getRun(runId)?.timings ?? {}
  const replay = run?.replay
  const dis = run?.disruption
  const blocked = replay ? (replay.blocked_after_mitigation ?? dis?.disrupted) === true : false
  const validated = !!dis?.disrupted && blocked

  return (
    <>
      <TopBar title={`Mitigation ${runId}`} subtitle={`${experimentId} · ${run?.chain_id ?? ''}`}
        actions={run && <StatusBadge status={run.status} />} />
      <main className="flex-1 overflow-y-auto scrollbar-thin p-6 space-y-6">
        {loading && <LoadingState label="Loading mitigation result…" />}
        {error && <ErrorState message={error} onRetry={load} />}
        {run && !replay && (
          <div className="border border-dashed border-base-600 rounded-lg p-6 text-sm space-y-2">
            <p>This run is <b>{run.status}</b>; the same-attack replay has not completed yet.</p>
            <Link className="text-signal underline text-xs" to={`/mitigation?exp=${experimentId}&run=${runId}`}>Continue workflow</Link>
          </div>
        )}
        {run && replay && dis && (
          <>
            <Verdict validated={validated} />
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
              <StatCard label="Selected control" value={<span className="text-base">{controlLabel(run.selection?.selected_control)}</span>}
                sub={`confidence ${Number(run.selection?.confidence ?? 0).toFixed(2)}`} />
              <StatCard label="Attack success" value={`${replay.before_result?.finding ? 1 : 0} → ${blocked ? 0 : 1}`} accent={validated ? '#5B9E6F' : '#E5484D'}
                sub={validated ? 'before → after' : 'still succeeds after mitigation'} />
              <StatCard label="Chain disrupted" value={dis.disrupted ? 'YES' : 'NO'} accent={dis.disrupted ? '#5B9E6F' : '#E5484D'} />
              <StatCard label="Residual vulnerable steps" value={dis.residual_vulnerable_steps?.length ?? 0}
                sub={dis.residual_vulnerable_steps?.join(', ') || 'none'} />
            </div>

            <section className="space-y-2">
              <h2 className="text-sm font-semibold">Why this control</h2>
              <div className="bg-base-900 border border-base-700 rounded-lg p-4 text-sm space-y-2">
                <ControlBadge control={run.selection?.selected_control} />
                <p className="text-base-200">{run.selection?.reason}</p>
                {run.selection?.retrieved_knowledge?.length > 0 && (
                  <details className="text-xs text-base-300"><summary className="cursor-pointer">RAG sources ({run.selection.retrieved_knowledge.length})</summary>
                    <ul className="list-disc pl-5 mt-2 space-y-1">{run.selection.retrieved_knowledge.map((k, i) => <li key={i}>{k}</li>)}</ul></details>
                )}
              </div>
            </section>

            <section className="space-y-2"><h2 className="text-sm font-semibold">Before vs after (same attack)</h2><BeforeAfter replay={replay} /></section>
            <section className="space-y-2"><h2 className="text-sm font-semibold">Chain disruption</h2>
              {steps.length ? <ChainDisruption steps={steps} replayTest={replay.test} blocked={blocked}
                residual={dis.residual_vulnerable_steps} disrupted={dis.disrupted} /> : <p className="text-xs text-base-400">Chain steps unavailable.</p>}
            </section>

            <section className="space-y-2"><h2 className="text-sm font-semibold">Run details</h2>
              <div className="grid md:grid-cols-2 gap-4 text-xs font-mono">
                <div className="bg-base-900 border border-base-700 rounded-lg p-4 space-y-1">
                  <div>application: {run.application?.status ?? '—'}</div>
                  <div>replay validation: {dis.validation_result?.status ?? '—'}</div>
                  <div>attack_blocked: {String(dis.validation_result?.attack_blocked ?? blocked)}</div>
                  <div className="text-base-400 pt-2">Measured in this browser</div>
                  <div>select {sec(timings.select)} · apply {sec(timings.apply)} · replay {sec(timings.replay)}</div>
                </div>
                <pre className="bg-base-900 border border-base-700 rounded-lg p-4 overflow-auto max-h-48 scrollbar-thin">{JSON.stringify(dis.validation_result, null, 2)}</pre>
              </div>
            </section>
          </>
        )}
      </main>
    </>
  )
}
