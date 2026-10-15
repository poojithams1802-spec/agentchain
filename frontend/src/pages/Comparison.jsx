import { useEffect, useMemo, useState } from 'react'
import { Download } from 'lucide-react'
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, Cell,
} from 'recharts'
import TopBar from '../components/TopBar'
import StatCard from '../components/StatCard'
import { LoadingState } from '../components/States'
import { Panel, Notice, Chip } from '../components/Phase3Parts'
import { getPhase3Analytics, getAblationAggregation, apiError } from '../api/client'
import { useTheme, chartColors } from '../lib/theme'
import {
  hasStaticAdaptiveData, staticAdaptiveCounts, staticAdaptiveRates,
  latestAblationRuns, ablationRateRows, ablationCostRows, ablationCaveats, isCleanAblation,
  ABLATION_RATE_METRICS, ABLATION_COST_METRICS, fmtPct, fmtSec,
} from '../lib/phase3'
import saSnapshot from '../mock/phase3_static_adaptive.json'
import ablSnapshot from '../mock/phase3_ablation.json'

const STATIC_C = '#5B8DEF'
const ADAPTIVE_C = '#8B5CF6'
const CODE_COLOR = { A: '#5B8DEF', B: '#8B5CF6', C: '#E8A33D', D: '#5B9E6F' }

function download(name, text, type) {
  const url = URL.createObjectURL(new Blob([text], { type }))
  Object.assign(document.createElement('a'), { href: url, download: name }).click()
  URL.revokeObjectURL(url)
}

// null = "no data for this item"; show it instead of a zero-height bar.
const fmtCell = (v, unit) => (v == null ? 'N/A' : unit === 's' ? fmtSec(v) : v)

export default function Comparison() {
  const { dark } = useTheme()
  const cc = chartColors(dark)
  const AXIS = { fill: cc.axis, fontSize: 11 }

  const [sa, setSa] = useState({ loading: true, error: null, data: null, source: 'live' })
  const [abl, setAbl] = useState({ loading: true, error: null, data: null, source: 'live' })

  async function load() {
    setSa((s) => ({ ...s, loading: true }))
    setAbl((s) => ({ ...s, loading: true }))
    getPhase3Analytics()
      .then((d) => setSa(hasStaticAdaptiveData(d.metrics)
        ? { loading: false, error: null, data: d, source: 'live' }
        : { loading: false, error: null, data: saSnapshot, source: 'snapshot-empty' }))
      .catch((e) => setSa({ loading: false, error: apiError(e), data: saSnapshot, source: 'snapshot-error' }))
    getAblationAggregation()
      .then((d) => setAbl(d.comparisons?.length
        ? { loading: false, error: null, data: d, source: 'live' }
        : { loading: false, error: null, data: ablSnapshot, source: 'snapshot-empty' }))
      .catch((e) => setAbl({ loading: false, error: apiError(e), data: ablSnapshot, source: 'snapshot-error' }))
  }
  useEffect(() => { load() }, [])

  const counts = useMemo(() => (sa.data ? staticAdaptiveCounts(sa.data.metrics) : []), [sa.data])
  const rates = useMemo(() => (sa.data ? staticAdaptiveRates(sa.data.metrics) : []), [sa.data])
  const runs = useMemo(() => latestAblationRuns(abl.data?.comparisons ?? []), [abl.data])
  const rateRows = useMemo(() => ablationRateRows(runs), [runs])
  const caveats = useMemo(() => ablationCaveats(runs), [runs])
  const clean = isCleanAblation(runs)
  const anyRate = rateRows.some((r) => ['A', 'B', 'C', 'D'].some((k) => r[k] != null))

  const banner = (state, label, snapNote) =>
    state.source === 'live' ? null : (
      <Notice tone="warn" title={state.source === 'snapshot-error' ? `${label}: live endpoint failed (${state.error})` : `${label}: no persisted data yet`}>
        Showing a bundled snapshot of a saved raw run ({snapNote}). This is not live data.
      </Notice>
    )

  const tip = { contentStyle: cc.tooltip, cursor: { fill: cc.cursor } }
  const m = sa.data?.metrics

  return (
    <>
      <TopBar
        title="Static vs Adaptive & Ablation"
        subtitle="Phase 3 comparison dashboard: testing modes and the A/B/C/D planner configurations"
        actions={
          <>
            <button onClick={load} className="border border-base-700 text-base-300 text-xs font-medium px-3 py-1.5 rounded-md hover:border-signal hover:text-signal transition-colors">
              Refresh
            </button>
            {(sa.data || abl.data) && (
              <button
                onClick={() => download('phase3_comparison.json', JSON.stringify({ static_vs_adaptive: sa.data, ablation: abl.data, sources: { sa: sa.source, ablation: abl.source } }, null, 2), 'application/json')}
                className="inline-flex items-center gap-1.5 text-xs btn-primary rounded px-2.5 py-1.5"
              ><Download size={12} />JSON</button>
            )}
          </>
        }
      />
      <main className="flex-1 overflow-y-auto scrollbar-thin p-6 space-y-8">
        {/* ---------------------------------------------------- static vs adaptive */}
        <section className="space-y-4">
          <h2 className="text-base font-extrabold text-base-100">Static vs adaptive</h2>
          {sa.loading && <LoadingState label="Loading comparison…" />}
          {!sa.loading && banner(sa, 'Static vs adaptive', saSnapshot.note)}
          {!sa.loading && sa.data && (
            <>
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                <StatCard label="Static runs" value={m.static?.experiments ?? 0} accent={STATIC_C} />
                <StatCard label="Adaptive runs" value={m.adaptive?.experiments ?? 0} accent={ADAPTIVE_C} />
                <StatCard label="Static validation rate" value={fmtPct(m.static?.validation_rate)} />
                <StatCard label="Adaptive validation rate" value={fmtPct(m.adaptive?.validation_rate)} />
              </div>

              <div className="grid lg:grid-cols-3 gap-4">
                <Panel title="Counts by mode" className="lg:col-span-2">
                  <div className="h-64">
                    <ResponsiveContainer>
                      <BarChart data={counts}>
                        <CartesianGrid stroke={cc.grid} vertical={false} />
                        <XAxis dataKey="label" tick={AXIS} interval={0} />
                        <YAxis tick={AXIS} allowDecimals={false} />
                        <Tooltip {...tip} />
                        <Legend wrapperStyle={{ fontSize: 11 }} />
                        <Bar dataKey="Static" fill={STATIC_C} />
                        <Bar dataKey="Adaptive" fill={ADAPTIVE_C} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </Panel>
                <Panel title="Validation rate (%)">
                  <div className="h-64">
                    <ResponsiveContainer>
                      <BarChart data={rates}>
                        <CartesianGrid stroke={cc.grid} vertical={false} />
                        <XAxis dataKey="label" tick={AXIS} />
                        <YAxis domain={[0, 100]} tick={AXIS} />
                        <Tooltip {...tip} />
                        <Legend wrapperStyle={{ fontSize: 11 }} />
                        <Bar dataKey="Static" fill={STATIC_C} />
                        <Bar dataKey="Adaptive" fill={ADAPTIVE_C} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </Panel>
              </div>

              <Notice tone="info">
                Counts are descriptive totals over recorded chain executions, not a significance test. With few runs (or runs that
                use the same chain in both modes) static and adaptive can look identical; read the gap, not the ranking.
                {m.static?.execution_time_seconds != null && (
                  <> Execution time in the snapshot: static {fmtSec(m.static.execution_time_seconds)}, adaptive {fmtSec(m.adaptive?.execution_time_seconds)}.</>
                )}
              </Notice>
            </>
          )}
        </section>

        {/* ---------------------------------------------------- ablation */}
        <section className="space-y-4">
          <div className="flex flex-wrap items-center gap-2">
            <h2 className="text-base font-extrabold text-base-100">A/B/C/D ablation</h2>
            <span className="text-xs text-base-400">planner configurations over the same scenario</span>
          </div>
          {abl.loading && <LoadingState label="Loading ablation…" />}
          {!abl.loading && banner(abl, 'Ablation', ablSnapshot.note)}

          {!abl.loading && abl.data && (
            <>
              <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3">
                {runs.map((r) => (
                  <div key={r.key} className="bg-base-900 border border-base-700 rounded-lg px-4 py-3">
                    <div className="flex items-center gap-2">
                      <span className="h-6 w-6 rounded grid place-items-center text-xs font-mono text-white" style={{ background: CODE_COLOR[r.code] }}>{r.code}</span>
                      <span className="text-sm text-base-100">{r.label}</span>
                    </div>
                    {r.record ? (
                      <div className="mt-2 flex flex-wrap gap-1.5">
                        <Chip tone={r.record.status === 'completed' ? 'good' : 'warn'}>{r.record.status}</Chip>
                        {r.record.fallback_used && <Chip tone="warn">fallback</Chip>}
                        <Chip>{r.runs} run{r.runs === 1 ? '' : 's'}</Chip>
                      </div>
                    ) : (
                      <div className="mt-2 text-xs text-base-500">no persisted run</div>
                    )}
                  </div>
                ))}
              </div>

              {!clean && (
                <Notice tone="warn" title="Not a like-for-like comparison">
                  <ul className="list-disc pl-4 mt-1 space-y-0.5">{caveats.map((c) => <li key={c}>{c}</li>)}</ul>
                  <p className="mt-1">Differences below reflect these conditions as much as the configurations. Do not read the charts as a ranking.</p>
                </Notice>
              )}

              <div className="grid lg:grid-cols-2 gap-4">
                <Panel title="Quality metrics (%)" subtitle="Latest run per configuration; gaps mean the metric was not recorded">
                  {anyRate ? (
                    <div className="h-72">
                      <ResponsiveContainer>
                        <BarChart data={rateRows}>
                          <CartesianGrid stroke={cc.grid} vertical={false} />
                          <XAxis dataKey="metric" tick={AXIS} interval={0} />
                          <YAxis domain={[0, 100]} tick={AXIS} />
                          <Tooltip {...tip} formatter={(v) => (v == null ? 'N/A' : `${v}%`)} />
                          <Legend wrapperStyle={{ fontSize: 11 }} />
                          {runs.map((r) => <Bar key={r.code} dataKey={r.code} name={`${r.code} · ${r.label}`} fill={CODE_COLOR[r.code]} />)}
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  ) : (
                    <p className="text-xs text-base-400 py-8 text-center">None of the quality metrics (selection accuracy, chain discovery, mitigation, disruption, validation) were recorded for these runs.</p>
                  )}
                </Panel>

                {['llm_calls', 'latency'].map((key) => {
                  const [, label, unit] = ABLATION_COST_METRICS.find((x) => x[0] === key)
                  const rows = ablationCostRows(runs, key)
                  return (
                    <Panel key={key} title={`${label}${unit ? ` (${unit})` : ''}`}>
                      <div className="h-72">
                        <ResponsiveContainer>
                          <BarChart data={rows}>
                            <CartesianGrid stroke={cc.grid} vertical={false} />
                            <XAxis dataKey="code" tick={AXIS} />
                            <YAxis tick={AXIS} />
                            <Tooltip {...tip} formatter={(v) => fmtCell(v, unit)} labelFormatter={(c) => runs.find((r) => r.code === c)?.label} />
                            <Bar dataKey="value" name={label}>
                              {rows.map((r) => <Cell key={r.code} fill={CODE_COLOR[r.code]} />)}
                            </Bar>
                          </BarChart>
                        </ResponsiveContainer>
                      </div>
                    </Panel>
                  )
                })}
              </div>

              <Panel title="All metrics">
                <div className="overflow-x-auto scrollbar-thin">
                  <table className="w-full text-xs">
                    <thead className="bg-base-800 text-base-300">
                      <tr>
                        <th className="text-left p-2">Metric</th>
                        {runs.map((r) => <th key={r.code} className="p-2 text-right">{r.code} · {r.label}</th>)}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-base-700 font-mono">
                      {ABLATION_RATE_METRICS.map(([k, label]) => (
                        <tr key={k}><td className="p-2 font-sans">{label}</td>
                          {runs.map((r) => <td key={r.code} className="p-2 text-right">{fmtPct(r.record?.[k])}</td>)}</tr>
                      ))}
                      {ABLATION_COST_METRICS.map(([k, label, unit]) => (
                        <tr key={k}><td className="p-2 font-sans">{label}</td>
                          {runs.map((r) => <td key={r.code} className="p-2 text-right">{fmtCell(r.record?.[k], unit)}</td>)}</tr>
                      ))}
                      <tr><td className="p-2 font-sans">Selected tests</td>
                        {runs.map((r) => <td key={r.code} className="p-2 text-right break-all">{r.record?.selected_tests?.length ? r.record.selected_tests.map((t) => t.replace(/_test$/, '')).join(', ') : '—'}</td>)}</tr>
                    </tbody>
                  </table>
                </div>
              </Panel>
            </>
          )}
        </section>
      </main>
    </>
  )
}
