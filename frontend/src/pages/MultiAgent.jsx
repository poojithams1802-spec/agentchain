import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { Loader2, Play, ArrowRight, CheckCircle2, XCircle } from 'lucide-react'
import TopBar from '../components/TopBar'
import StatCard from '../components/StatCard'
import { LoadingState, ErrorState, EmptyState } from '../components/States'
import { Panel, Notice, Chip, JsonBlock, AgentGraph } from '../components/Phase3Parts'
import {
  listExperiments, getAgentSecurityResult, getAgentState, runAgentSecurityScenario, isNotFound, apiError,
} from '../api/client'
import { normalizeAgentResult, prettify } from '../lib/phase3'

const EDGE_TONE = { delivered: 'bad', denied: 'good', allowed: undefined }
const EDGE_TEXT = {
  delivered: 'message delivered',
  denied: 'message denied',
  allowed: 'interaction allowed by configuration',
}

export default function MultiAgent() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [list, setList] = useState({ loading: true, error: null, items: [] })
  const [state, setState] = useState({ loading: false, error: null, doc: null, live: null })
  const [running, setRunning] = useState(false)
  const [runError, setRunError] = useState(null)

  useEffect(() => {
    listExperiments()
      .then((items) => setList({ loading: false, error: null, items }))
      .catch((e) => setList({ loading: false, error: apiError(e), items: [] }))
  }, [])

  async function load() {
    if (!id) return
    setState({ loading: true, error: null, doc: null, live: null })
    try {
      const [doc, live] = await Promise.all([
        getAgentSecurityResult(id).catch((e) => { if (isNotFound(e)) return null; throw e }),
        getAgentState(id).catch((e) => { if (isNotFound(e)) return null; throw e }),
      ])
      setState({ loading: false, error: null, doc, live })
    } catch (e) {
      setState({ loading: false, error: apiError(e), doc: null, live: null })
    }
  }
  useEffect(() => { load() }, [id])

  async function run() {
    setRunning(true); setRunError(null)
    try {
      await runAgentSecurityScenario(id)
      await load()
    } catch (e) {
      setRunError(apiError(e))
    } finally { setRunning(false) }
  }

  const view = useMemo(() => normalizeAgentResult(state.doc), [state.doc])
  const live = useMemo(() => normalizeAgentResult(state.live), [state.live])
  const trig = view?.chainTriggered

  return (
    <>
      <TopBar
        title="Multi-Agent Interaction"
        subtitle="Agents, trust levels, communication and the cross-agent attack chain"
        actions={
          <select aria-label="Choose experiment" value={id ?? ''}
            onChange={(e) => navigate(e.target.value ? `/agents/${e.target.value}` : '/agents')}
            className="bg-base-900 border border-base-700 rounded-md px-2 py-1.5 text-xs text-base-100 max-w-[16rem]">
            <option value="">Select experiment…</option>
            {list.items.map((e) => <option key={e.experiment_id} value={e.experiment_id}>{e.experiment_id} · {e.name}</option>)}
          </select>
        }
      />
      <main className="flex-1 overflow-y-auto scrollbar-thin p-6 space-y-6">
        {list.loading && <LoadingState label="Loading experiments…" />}
        {list.error && <ErrorState message={list.error} onRetry={() => location.reload()} />}
        {!list.loading && !list.error && !id && (
          <EmptyState title="Select an experiment" description="Pick an experiment to view the multi-agent security result stored for it."
            action={<Link to="/new-experiment" className="text-signal text-xs underline">Create experiment</Link>} />
        )}

        {id && state.loading && <LoadingState label="Loading multi-agent result…" />}
        {id && state.error && <ErrorState message={state.error} onRetry={load} />}

        {id && !state.loading && !state.error && !view && (
          <EmptyState
            title="No multi-agent result stored for this experiment"
            description="Run P4's controlled two-agent scenario (V11 cross-agent trust → V10 unsafe delegation). It is local and synthetic; nothing leaves the sandbox."
            action={
              <button onClick={run} disabled={running} className="inline-flex items-center gap-2 btn-primary text-sm rounded px-3 py-1.5 disabled:opacity-50">
                {running ? <Loader2 size={14} className="animate-spin" /> : <Play size={14} />} Run controlled scenario
              </button>
            }
          />
        )}
        {runError && <Notice tone="bad">Run failed: {runError}</Notice>}

        {view && (
          <>
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
              <StatCard label="Agents" value={view.agents.length} />
              <StatCard label="Interactions" value={view.edges.length} sub={`${view.edges.filter((e) => e.kind === 'delivered').length} delivered`} />
              <StatCard label="Chain triggered" value={trig == null ? '—' : trig ? 'YES' : 'NO'} accent={trig ? '#E5484D' : trig === false ? '#5B9E6F' : undefined} sub={view.chainId ?? undefined} />
              <StatCard label="Chain validated" value={view.validation ? (view.validation.validated_chain ? 'YES' : 'NO') : '—'} sub={view.validation ? `${view.validation.chain_length ?? '?'} steps` : view.status ?? undefined} />
            </div>

            {view.edges.some((e) => e.crossesTrustBoundary && e.kind === 'delivered') && (
              <Notice tone="bad" title="Trust boundary crossed">
                A lower-trust agent successfully delivered a message to a higher-trust agent. This is the weakness the V11 step demonstrates in the sandbox.
              </Notice>
            )}

            <Panel title="Agent graph" subtitle="Left to right by increasing trust. Arrows show communication.">
              <AgentGraph agents={view.agents} edges={view.edges} />
              <div className="flex flex-wrap gap-x-5 gap-y-1 mt-2 text-[11px] text-base-400">
                <span><span className="text-sev-critical">━</span> delivered</span>
                <span><span className="text-sev-low">╌</span> denied</span>
                <span><span className="text-base-400">┄</span> allowed by configuration</span>
              </div>
            </Panel>

            <div className="grid lg:grid-cols-2 gap-4">
              <Panel title="Interactions">
                {view.edges.length === 0 ? (
                  <p className="text-xs text-base-400">No interactions were recorded.</p>
                ) : (
                  <ul className="space-y-2">
                    {view.edges.map((e, i) => (
                      <li key={i} className="border border-base-700 rounded-md px-3 py-2 text-xs space-y-1">
                        <div className="flex flex-wrap items-center gap-2 font-mono">
                          <span className="text-base-100">{e.from}</span><ArrowRight size={12} className="text-base-500" /><span className="text-base-100">{e.to}</span>
                          <Chip tone={EDGE_TONE[e.kind]}>{EDGE_TEXT[e.kind]}</Chip>
                          {e.crossesTrustBoundary && <Chip tone="warn">trust +{e.trustGap.toFixed(2)}</Chip>}
                        </div>
                        {e.message && <div className="text-base-300 font-sans">“{e.message}”</div>}
                      </li>
                    ))}
                  </ul>
                )}
              </Panel>

              <Panel title="Attack chain steps" subtitle={view.expectedChain.length ? `Expected: ${view.expectedChain.join(' → ')}` : undefined}>
                {view.chainSteps.length === 0 ? (
                  <p className="text-xs text-base-400">This record has no chain steps.</p>
                ) : (
                  <ol className="space-y-2">
                    {view.chainSteps.map((s, i) => (
                      <li key={i} className="flex flex-wrap items-center gap-2 border border-base-700 rounded-md px-3 py-2 text-xs">
                        <span className="h-6 w-6 rounded-full grid place-items-center font-mono border border-signal text-signal">{s.step ?? i + 1}</span>
                        {s.vulnerability_id && <Chip>{s.vulnerability_id}</Chip>}
                        <span className="font-mono text-base-100">{s.test}</span>
                        <span className="text-base-300">{prettify(s.finding)}</span>
                        <Chip tone={s.status === 'triggered' ? 'bad' : 'good'}>{s.status}</Chip>
                      </li>
                    ))}
                  </ol>
                )}
                {view.validation && (
                  <div className="mt-3 text-xs space-y-1">
                    <div className="flex items-center gap-1.5">
                      {view.validation.valid ? <CheckCircle2 size={14} className="text-sev-low" /> : <XCircle size={14} className="text-sev-critical" />}
                      <span className="text-base-200">Scenario validation {view.validation.valid ? 'passed' : 'failed'}</span>
                    </div>
                    {view.validation.errors?.map((er) => <div key={er} className="text-sev-high">{er}</div>)}
                    {view.validationRule && <p className="text-base-400">{view.validationRule}</p>}
                  </div>
                )}
              </Panel>
            </div>

            {(view.trustContext || view.sharedMemory || view.assessment) && (
              <div className="grid lg:grid-cols-3 gap-4">
                {view.trustContext && <Panel title="Trust context"><JsonBlock value={view.trustContext} /></Panel>}
                {view.sharedMemory && <Panel title="Shared memory"><JsonBlock value={view.sharedMemory} /></Panel>}
                {view.assessment && <Panel title="Assessment"><JsonBlock value={view.assessment} /></Panel>}
              </div>
            )}

            {live && (
              <Panel title="Live agent state" subtitle="From GET /agents/state">
                <div className="flex flex-wrap gap-2 text-xs">
                  {state.live.current_agent && <Chip>current agent: {state.live.current_agent}</Chip>}
                  {state.live.current_task && <Chip>task: {state.live.current_task}</Chip>}
                  <Chip>{live.agents.length} agents</Chip>
                </div>
              </Panel>
            )}

            <div className="flex flex-wrap items-center gap-3 text-xs text-base-400">
              {view.timestamp && <span>Stored {new Date(view.timestamp).toLocaleString()}</span>}
              <button onClick={run} disabled={running} className="inline-flex items-center gap-1.5 border border-base-600 rounded px-2.5 py-1.5 text-base-200 hover:bg-base-800 disabled:opacity-50">
                {running ? <Loader2 size={12} className="animate-spin" /> : <Play size={12} />} Run controlled scenario again
              </button>
              <span>The API returns the first record stored for an experiment, so a re-run adds a record without changing this view.</span>
            </div>

            <details className="text-xs text-base-400">
              <summary className="cursor-pointer">Raw record</summary>
              <div className="mt-2"><JsonBlock value={state.doc} max="max-h-96" /></div>
            </details>
          </>
        )}
      </main>
    </>
  )
}
