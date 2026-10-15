import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { Search, X, ArrowRight, ShieldCheck } from 'lucide-react'
import TopBar from '../components/TopBar'
import { SeverityBadge } from '../components/Badges'
import { LoadingState, ErrorState, EmptyState } from '../components/States'
import { Panel, Chip, JsonBlock, Notice } from '../components/Phase3Parts'
import { listExperiments, getExperimentFindings, listScenarios, apiError } from '../api/client'
import { controlLabel } from '../lib/mitigation'
import {
  aggregateVulnerabilities, filterVulnerabilities, SEVERITY_ORDER, prettify, fmtPct,
} from '../lib/phase3'

const selectCls = 'bg-base-900 border border-base-700 rounded-md px-2 py-1.5 text-xs text-base-100'

function Detail({ v, onClose }) {
  return (
    <aside className="w-[26rem] max-w-[50vw] border-l border-base-700 bg-base-900 p-5 overflow-y-auto scrollbar-thin" aria-label={`${v.id} details`}>
      <div className="flex items-start justify-between gap-2">
        <div>
          <div className="text-xs font-mono text-base-400">{v.id} · {v.test}</div>
          <h3 className="text-sm font-semibold text-base-100 mt-0.5">{v.title}</h3>
        </div>
        <button onClick={onClose} aria-label="Close details" className="text-base-400 hover:text-base-100"><X size={16} /></button>
      </div>

      <dl className="mt-4 space-y-3 text-xs">
        <div><dt className="text-base-400 mb-1">Finding name</dt><dd className="font-mono text-base-200">{v.finding}</dd></div>
        <div>
          <dt className="text-base-400 mb-1">Predefined defensive control</dt>
          <dd>{v.control
            ? <Chip tone="good"><ShieldCheck size={11} />{controlLabel(v.control)}</Chip>
            : <span className="text-base-300">None. Only authorization, tool and memory weaknesses have a predefined control.</span>}</dd>
        </div>
        <div>
          <dt className="text-base-400 mb-1">Appears in scenarios</dt>
          <dd className="space-y-1.5">
            {v.scenarios.length === 0 && <span className="text-base-300">No registered scenario includes this test.</span>}
            {v.scenarios.map((s) => (
              <div key={s.scenario_id} className="flex flex-wrap items-center gap-1 font-mono text-[11px]">
                <span className="text-base-200">{s.scenario_id}</span>
                <span className="text-base-500">:</span>
                {s.steps.map((st, i) => (
                  <span key={st} className="flex items-center gap-1">
                    {i > 0 && <ArrowRight size={10} className="text-base-500" />}
                    <span className={`px-1.5 py-0.5 rounded border ${st === v.test ? 'border-signal text-signal bg-signal/10' : 'border-base-700 text-base-400'}`}>{st.replace(/_test$/, '')}</span>
                  </span>
                ))}
              </div>
            ))}
          </dd>
        </div>
      </dl>

      <h4 className="text-xs font-semibold text-base-200 mt-5 mb-2">Observations ({v.count})</h4>
      {v.count === 0 ? (
        <p className="text-xs text-base-400">Not observed in any experiment yet.</p>
      ) : (
        <div className="space-y-2">
          {v.observations.map((o, i) => (
            <div key={`${o.experiment_id}-${i}`} className="border border-base-700 rounded-md p-2.5 space-y-1.5">
              <div className="flex flex-wrap items-center gap-2 text-xs">
                <Link to={`/experiments/${o.experiment_id}`} className="font-mono text-signal hover:underline">{o.experiment_id}</Link>
                <SeverityBadge severity={o.severity} />
                <span className="text-base-400">confidence {fmtPct(o.confidence)}</span>
                {o.timestamp && <span className="text-base-500 text-[11px]">{new Date(o.timestamp).toLocaleString()}</span>}
              </div>
              <JsonBlock value={o.evidence} max="max-h-32" />
            </div>
          ))}
        </div>
      )}
    </aside>
  )
}

export default function Vulnerabilities() {
  const [state, setState] = useState({ loading: true, error: null, findings: [], scenarios: [], scenariosError: null })
  const [query, setQuery] = useState('')
  const [severity, setSeverity] = useState('all')
  const [status, setStatus] = useState('all')
  const [scenarioId, setScenarioId] = useState('all')
  const [selected, setSelected] = useState(null)

  async function load() {
    setState((s) => ({ ...s, loading: true, error: null }))
    try {
      const experiments = await listExperiments()
      const [findings, scenarios] = await Promise.all([
        Promise.all(experiments.map((e) => getExperimentFindings(e.experiment_id))).then((r) => r.flat()),
        listScenarios().then((items) => ({ items, error: null })).catch((e) => ({ items: [], error: apiError(e) })),
      ])
      setState({ loading: false, error: null, findings, scenarios: scenarios.items, scenariosError: scenarios.error })
    } catch (e) {
      setState((s) => ({ ...s, loading: false, error: apiError(e) }))
    }
  }
  useEffect(() => { load() }, [])

  const rows = useMemo(() => aggregateVulnerabilities(state.findings, state.scenarios), [state.findings, state.scenarios])
  const shown = useMemo(() => filterVulnerabilities(rows, { query, severity, status, scenarioId }), [rows, query, severity, status, scenarioId])
  const activeScenario = state.scenarios.find((s) => s.scenario_id === scenarioId)
  const detail = rows.find((r) => r.test === selected)
  const observed = rows.filter((r) => r.count > 0).length

  return (
    <>
      <TopBar
        title="Vulnerabilities"
        subtitle={`${rows.length} controlled vulnerability types · ${observed} observed so far`}
        actions={
          <button onClick={load} disabled={state.loading}
            className="border border-base-700 text-base-300 text-xs font-medium px-3 py-1.5 rounded-md hover:border-signal hover:text-signal transition-colors disabled:opacity-50">
            {state.loading ? 'Refreshing…' : 'Refresh'}
          </button>
        }
      />

      <div className="flex-1 flex overflow-hidden">
        <main className="flex-1 min-w-0 overflow-y-auto scrollbar-thin p-6 space-y-4">
          {state.loading && <LoadingState label="Loading vulnerabilities…" />}
          {state.error && <ErrorState message={state.error} onRetry={load} />}
          {state.scenariosError && !state.loading && (
            <Notice tone="warn">Scenarios could not be loaded ({state.scenariosError}); scenario filtering is unavailable.</Notice>
          )}

          {!state.loading && !state.error && (
            <>
              <div className="flex flex-wrap items-center gap-3">
                <div className="relative">
                  <Search size={13} className="absolute left-2.5 top-2 text-base-500" />
                  <input value={query} onChange={(e) => setQuery(e.target.value)} aria-label="Search vulnerabilities"
                    placeholder="Search id, test, finding, evidence…"
                    className="w-72 bg-base-900 border border-base-700 rounded-md pl-8 pr-3 py-1.5 text-xs text-base-100 placeholder:text-base-500 focus:border-signal outline-none" />
                </div>
                <div className="flex gap-1" role="group" aria-label="Severity filter">
                  {['all', ...SEVERITY_ORDER].map((s) => (
                    <button key={s} onClick={() => setSeverity(s)} aria-pressed={severity === s}
                      className={`text-xs px-2.5 py-1 rounded-md border capitalize ${severity === s ? 'border-signal text-signal bg-signal/10' : 'border-base-700 text-base-400 hover:text-base-200'}`}>{s}</button>
                  ))}
                </div>
                <select className={selectCls} value={status} onChange={(e) => setStatus(e.target.value)} aria-label="Observation status">
                  <option value="all">Any status</option>
                  <option value="observed">Observed</option>
                  <option value="not_observed">Not observed</option>
                </select>
                <select className={selectCls} value={scenarioId} onChange={(e) => setScenarioId(e.target.value)} aria-label="Scenario" disabled={!state.scenarios.length}>
                  <option value="all">All scenarios</option>
                  {state.scenarios.map((s) => <option key={s.scenario_id} value={s.scenario_id}>{s.scenario_id} · {s.scenario_name}</option>)}
                </select>
                <span className="text-xs text-base-400 ml-auto">{shown.length} of {rows.length}</span>
              </div>

              {activeScenario && (
                <Panel title={activeScenario.scenario_name} subtitle={activeScenario.description}
                  actions={<Link to={`/new-experiment?scenario=${activeScenario.scenario_id}`} className="btn-primary text-xs px-3 py-1.5 rounded-md">Run this scenario</Link>}>
                  <div className="flex flex-wrap items-center gap-1.5 text-xs font-mono">
                    {activeScenario.steps.map((st, i) => (
                      <span key={st} className="flex items-center gap-1.5">
                        {i > 0 && <ArrowRight size={12} className="text-base-500" />}
                        <span className="px-2 py-0.5 rounded bg-base-800 border border-base-600">{st}</span>
                      </span>
                    ))}
                  </div>
                </Panel>
              )}

              {shown.length === 0 ? (
                <EmptyState title="No vulnerabilities match these filters" />
              ) : (
                <div className="border border-base-700 rounded-lg overflow-hidden">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="bg-base-900 text-base-400 text-xs">
                        {['ID', 'Vulnerability', 'Test', 'Worst severity', 'Observed', 'Avg. confidence', 'Control'].map((h) => (
                          <th key={h} className="text-left font-medium px-4 py-2.5">{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {shown.map((r) => (
                        <tr key={r.test} onClick={() => setSelected(r.test)} tabIndex={0}
                          onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && setSelected(r.test)}
                          className={`border-t border-base-700 cursor-pointer hover:bg-base-900/60 ${selected === r.test ? 'bg-signal/5' : ''}`}>
                          <td className="px-4 py-2.5 font-mono text-xs text-base-300">{r.id}</td>
                          <td className="px-4 py-2.5 text-base-100">{prettify(r.finding)}</td>
                          <td className="px-4 py-2.5 font-mono text-xs text-base-400">{r.test}</td>
                          <td className="px-4 py-2.5">{r.severity ? <SeverityBadge severity={r.severity} /> : <span className="text-base-500 text-xs">—</span>}</td>
                          <td className="px-4 py-2.5 font-mono text-xs">{r.count > 0 ? `${r.count} in ${r.experiments.length} exp.` : <span className="text-base-500">not yet</span>}</td>
                          <td className="px-4 py-2.5 font-mono text-xs text-base-300">{fmtPct(r.avgConfidence)}</td>
                          <td className="px-4 py-2.5 text-xs text-base-300">{r.control ? controlLabel(r.control) : '—'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </>
          )}
        </main>
        {detail && <Detail v={detail} onClose={() => setSelected(null)} />}
      </div>
    </>
  )
}
