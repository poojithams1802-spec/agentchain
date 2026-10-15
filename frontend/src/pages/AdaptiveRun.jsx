import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { ArrowRight, ShieldCheck, Network } from 'lucide-react'
import TopBar from '../components/TopBar'
import StatCard from '../components/StatCard'
import { StatusBadge, ModeBadge, SeverityBadge } from '../components/Badges'
import { LoadingState, ErrorState, EmptyState } from '../components/States'
import { Panel, Notice, BudgetMeters, DecisionTimeline, Chip } from '../components/Phase3Parts'
import {
  listExperiments,
  getExperiment,
  getExperimentFindings,
  getExperimentLogs,
  apiError,
} from '../api/client'
import { loadAdaptiveRun, listAdaptiveRunIds } from '../lib/adaptiveRuns'
import { normalizeAdaptiveRun, budgetMeters, latestFindingByTest, fmtSec, prettify } from '../lib/phase3'

export default function AdaptiveRun() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [list, setList] = useState({ loading: true, error: null, items: [] })
  const [state, setState] = useState({ loading: false, error: null, exp: null, findings: [], logs: [] })

  useEffect(() => {
    listExperiments()
      .then((items) => setList({ loading: false, error: null, items }))
      .catch((e) => setList({ loading: false, error: apiError(e), items: [] }))
  }, [])

  async function load() {
    if (!id) return
    setState((s) => ({ ...s, loading: true, error: null }))
    try {
      const [exp, findings, logs] = await Promise.all([getExperiment(id), getExperimentFindings(id), getExperimentLogs(id)])
      setState({ loading: false, error: null, exp, findings, logs })
    } catch (e) {
      setState({ loading: false, error: apiError(e), exp: null, findings: [], logs: [] })
    }
  }
  useEffect(() => { load() }, [id])

  const stored = useMemo(() => (id ? loadAdaptiveRun(id) : null), [id])
  const run = useMemo(() => normalizeAdaptiveRun(stored?.response), [stored])
  const { exp, findings, logs } = state
  const byTest = useMemo(() => latestFindingByTest(findings), [findings])
  const meters = budgetMeters(run, exp)
  const withRun = useMemo(() => new Set(listAdaptiveRunIds()), [list.items])

  return (
    <>
      <TopBar
        title="Adaptive Run"
        subtitle="Testing budget and planner decision timeline"
        actions={
          <select
            aria-label="Choose experiment"
            value={id ?? ''}
            onChange={(e) => navigate(e.target.value ? `/adaptive/${e.target.value}` : '/adaptive')}
            className="bg-base-900 border border-base-700 rounded-md px-2 py-1.5 text-xs text-base-100 max-w-[16rem]"
          >
            <option value="">Select experiment…</option>
            {list.items.map((e) => (
              <option key={e.experiment_id} value={e.experiment_id}>
                {e.experiment_id} · {e.name}
                {withRun.has(e.experiment_id) ? ' · timeline' : ''}
              </option>
            ))}
          </select>
        }
      />

      <main className="flex-1 overflow-y-auto scrollbar-thin p-6 space-y-6">
        {list.loading && <LoadingState label="Loading experiments…" />}
        {list.error && <ErrorState message={list.error} onRetry={() => location.reload()} />}
        {!list.loading && !list.error && !id && (
          <EmptyState
            title="Select an experiment"
            description="Pick an experiment above to see its budget usage and the order in which the planner chose tests."
            action={<Link to="/new-experiment" className="text-signal text-xs underline">Create experiment</Link>}
          />
        )}

        {id && state.loading && <LoadingState label="Loading run…" />}
        {id && state.error && <ErrorState message={state.error} onRetry={load} />}

        {id && exp && !state.loading && (
          <>
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-mono text-sm text-base-100">{exp.experiment_id}</span>
              <span className="text-sm text-base-300">{exp.name}</span>
              <ModeBadge mode={exp.mode} />
              <StatusBadge status={exp.status} />
              {exp.scenario_name && <Chip title={exp.scenario_id}>{exp.scenario_name}</Chip>}
              {exp.vulnerability_ids?.length > 0 && <Chip>{exp.vulnerability_ids.join(' → ')}</Chip>}
            </div>

            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
              <StatCard label="Max tests" value={exp.max_tests} />
              <StatCard label="Testing budget" value={exp.testing_budget ?? '—'} sub="stored with the experiment" />
              <StatCard label="Tests selected" value={exp.selected_tests?.length ?? 0} />
              <StatCard label="Tests executed" value={exp.executed_tests?.length ?? 0} sub={`budget_used ${exp.budget_used ?? 0}`} />
            </div>

            {run ? (
              <>
                <Panel
                  title="Budget used"
                  subtitle={`Reported by the adaptive loop · saved ${new Date(stored.saved_at).toLocaleString()}`}
                >
                  <BudgetMeters meters={meters} />
                  <div className="flex flex-wrap items-center gap-2 mt-3 text-xs text-base-400">
                    <Chip tone={run.fallbackUsed ? 'warn' : 'good'}>
                      {run.fallbackUsed ? `fallback used · ${run.fallbackDecisions} of ${run.events.length} decisions` : 'no fallback'}
                    </Chip>
                    <Chip>planned {run.events.length}</Chip>
                    <Chip>executed {run.events.filter((e) => e.executed).length}</Chip>
                    <Chip>run time {fmtSec(run.budget.timeSeconds)}</Chip>
                  </div>
                  {run.cutBeforeExecution && (
                    <div className="mt-3">
                      <Notice tone="warn" title="Run stopped before every planned test executed">
                        The planner chose a test that never reached the sandbox, which happens when the time budget is reached after planning.
                      </Notice>
                    </div>
                  )}
                </Panel>

                <Panel title="Decision timeline" subtitle="One entry per planner decision, joined with its sandbox result">
                  <DecisionTimeline events={run.events} />
                </Panel>

                {run.candidateChain?.chain_id && (
                  <Panel title="Resulting chain">
                    <div className="flex flex-wrap items-center gap-2 text-xs font-mono">
                      <span className="text-base-400">{run.candidateChain.chain_id}</span>
                      {run.candidateChain.steps.map((s, i) => (
                        <span key={s} className="flex items-center gap-2">
                          {i > 0 && <ArrowRight size={12} className="text-base-500" />}
                          <span className="px-2 py-0.5 rounded bg-base-800 border border-base-600">{s}</span>
                        </span>
                      ))}
                      {run.validation?.status && <StatusBadge status={run.validation.status} />}
                      {run.validation && (
                        <span className="text-base-400">
                          {run.validation.validated_steps}/{run.validation.total_steps} steps validated
                        </span>
                      )}
                    </div>
                    <div className="flex flex-wrap gap-3 mt-3">
                      <Link to="/chains" className="inline-flex items-center gap-1.5 text-xs text-signal hover:underline">
                        <Network size={13} /> View in Attack Chains
                      </Link>
                      <Link to="/chain-mitigation" className="inline-flex items-center gap-1.5 text-xs text-signal hover:underline">
                        <ShieldCheck size={13} /> Mitigate this chain
                      </Link>
                    </div>
                  </Panel>
                )}
              </>
            ) : (
              <>
                <Notice tone="info" title="Planner decisions are not available for this experiment in this browser">
                  The decision reasons, planner source and budget usage are only returned by the start request, and the
                  backend has no endpoint to read them back later. Run an experiment from this app to capture them. The
                  recorded sequence below comes from the experiment record and its findings.
                </Notice>

                <Panel title="Recorded sequence" subtitle="From GET /experiments/{id} and /findings">
                  {exp.selected_tests?.length ? (
                    <ol className="space-y-2">
                      {exp.selected_tests.map((t, i) => {
                        const f = byTest[t]
                        return (
                          <li key={`${t}-${i}`} className="flex flex-wrap items-center gap-2 text-xs border border-base-700 rounded-lg px-3 py-2 bg-base-900">
                            <span className="h-6 w-6 rounded-full grid place-items-center font-mono border border-signal text-signal">{i + 1}</span>
                            <span className="font-mono text-sm text-base-100">{t}</span>
                            {exp.executed_tests?.includes(t) ? <StatusBadge status="completed" /> : <StatusBadge status="failed" />}
                            {f && <span className="text-base-300">{prettify(f.finding)}</span>}
                            {f && <SeverityBadge severity={f.severity} />}
                          </li>
                        )
                      })}
                    </ol>
                  ) : (
                    <p className="text-xs text-base-400">No tests were selected yet (status: {exp.status}).</p>
                  )}
                </Panel>

                {logs.length > 0 && (
                  <Panel title="Activity log">
                    <div className="font-mono text-xs text-base-400 space-y-1 max-h-48 overflow-y-auto scrollbar-thin">
                      {logs.map((l, i) => (
                        <div key={i}>
                          <span className="text-base-500">{new Date(l.timestamp).toLocaleTimeString()}</span>{' '}
                          <span className="text-base-300">{l.message}</span>
                        </div>
                      ))}
                    </div>
                  </Panel>
                )}
              </>
            )}
          </>
        )}
      </main>
    </>
  )
}
