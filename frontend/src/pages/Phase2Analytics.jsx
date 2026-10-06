import { useEffect, useMemo, useState } from 'react'
import { Download } from 'lucide-react'
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts'
import TopBar from '../components/TopBar'
import StatCard from '../components/StatCard'
import { LoadingState, ErrorState } from '../components/States'
import { getPhase2Analytics, apiError } from '../api/client'
import { CONDITIONS, pct, controlLabel } from '../lib/mitigation'
import { useTheme, chartColors } from '../lib/theme'

const COLS = [
  ['mitigation_selection_accuracy', 'Selection accuracy'],
  ['mitigation_application_success', 'Application success'],
  ['attack_success_rate_before', 'Attack success before'],
  ['attack_success_rate_after', 'Attack success after'],
  ['chain_disruption_rate', 'Chain disruption'],
  ['mitigation_validation_rate', 'Validation rate'],
]

function download(name, text, type) {
  const url = URL.createObjectURL(new Blob([text], { type }))
  const a = Object.assign(document.createElement('a'), { href: url, download: name })
  a.click()
  URL.revokeObjectURL(url)
}

function markdown(metrics, records) {
  const head = `| Condition | n | ${COLS.map((c) => c[1]).join(' | ')} | Residual steps | LLM calls |\n|---|---|${COLS.map(() => '---').join('|')}|---|---|\n`
  const rows = Object.entries(CONDITIONS).filter(([k]) => metrics[k]).map(([k, label]) => {
    const m = metrics[k]
    return `| ${label} | ${m.experiment_count} | ${COLS.map(([f]) => pct(m[f])).join(' | ')} | ${m.residual_vulnerable_steps.length} | ${m.llm_calls} |`
  })
  const recs = records.map((r) => `| ${r.experiment_id} | ${CONDITIONS[r.condition]} | ${r.test} | ${r.expected_control} | ${r.selected_control} | ${r.chain_disrupted ? 'yes' : 'no'} | ${r.mitigation_validation ? 'VALIDATED' : 'not validated'} |`)
  return `# AgentChain Phase 2: Mitigation Report\n\n## Metrics by condition\n\n${head}${rows.join('\n')}\n\n## Experiments\n\n| ID | Condition | Test | Expected | Selected | Disrupted | Status |\n|---|---|---|---|---|---|---|\n${recs.join('\n')}\n`
}

export default function Phase2Analytics() {
  const { dark } = useTheme()
  const cc = chartColors(dark)
  const AXIS = { fill: cc.axis, fontSize: 11 }
  const TIP = cc.tooltip
  const [state, setState] = useState({ loading: true, error: null, data: null })
  async function load() {
    setState({ loading: true, error: null, data: null })
    try { setState({ loading: false, error: null, data: await getPhase2Analytics() }) }
    catch (e) { setState({ loading: false, error: apiError(e), data: null }) }
  }
  useEffect(() => { load() }, [])

  const { data } = state
  const rows = useMemo(() => data ? Object.entries(CONDITIONS).filter(([k]) => data.metrics[k]).map(([k, label]) => ({ key: k, label, ...data.metrics[k] })) : [], [data])
  const l3 = rows.find((r) => r.key === 'level3_proposed')
  const wrong = rows.find((r) => r.key === 'wrong_control')
  const chartA = rows.filter((r) => r.attack_success_rate_before != null).map((r) => ({
    name: r.label, Before: r.attack_success_rate_before * 100, After: r.attack_success_rate_after * 100 }))
  const chartB = rows.filter((r) => r.chain_disruption_rate != null).map((r) => ({
    name: r.label, 'Chain disruption': r.chain_disruption_rate * 100, 'Validation rate': r.mitigation_validation_rate * 100,
    'Selection accuracy': r.mitigation_selection_accuracy * 100 }))

  return (
    <>
      <TopBar title="Phase 2 Metrics & Report" subtitle="Four experimental conditions: baselines vs Level-3 vs wrong-control"
        actions={data && <>
          <button onClick={() => download('phase2_results.json', JSON.stringify(data, null, 2), 'application/json')}
            className="inline-flex items-center gap-1.5 text-xs border border-base-600 rounded px-2.5 py-1.5 hover:bg-base-800"><Download size={12} />JSON</button>
          <button onClick={() => download('phase2_report.md', markdown(data.metrics, data.records), 'text/markdown')}
            className="inline-flex items-center gap-1.5 text-xs btn-primary rounded px-2.5 py-1.5"><Download size={12} />Report (.md)</button></>} />
      <main className="flex-1 overflow-y-auto scrollbar-thin p-6 space-y-6">
        {state.loading && <LoadingState label="Loading Phase 2 metrics…" />}
        {state.error && <ErrorState message={state.error} onRetry={load} />}
        {data && (
          <>
            {data.source === 'snapshot' && (
              <p className="text-xs text-sev-medium border border-sev-medium/30 bg-sev-medium/10 rounded px-3 py-2">
                Showing the bundled snapshot (src/mock/phase2.json{data.generated_at ? `, generated ${new Date(data.generated_at).toLocaleString()}` : ''}). The live <code>/phase2/analytics</code> endpoint was not found.
              </p>
            )}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
              <StatCard label="Level-3 chain disruption" value={pct(l3?.chain_disruption_rate)} accent="#5B9E6F" sub={`n=${l3?.experiment_count ?? 0}`} />
              <StatCard label="Level-3 validation rate" value={pct(l3?.mitigation_validation_rate)} accent="#5B9E6F" />
              <StatCard label="Wrong-control validation" value={pct(wrong?.mitigation_validation_rate)} accent="#E5484D"
                sub={`application success ${pct(wrong?.mitigation_application_success)}`} />
              <StatCard label="Total LLM calls" value={rows.reduce((a, r) => a + (r.llm_calls ?? 0), 0)} />
            </div>

            {wrong && wrong.mitigation_application_success === 1 && wrong.mitigation_validation_rate === 0 && (
              <p className="text-sm border border-base-600 rounded-lg p-4 bg-base-900">
                <b>Wrong-control finding:</b> every wrong control was applied successfully ({pct(wrong.mitigation_application_success)}) yet none disrupted the attack
                ({pct(wrong.mitigation_validation_rate)} validated). Applying a control does not imply the mitigation worked, which is why the replay step matters.
              </p>
            )}

            <div className="grid lg:grid-cols-2 gap-4">
              {[['Attack success rate: before vs after (%)', chartA, [['Before', '#E5484D'], ['After', '#5B9E6F']]],
                ['Selection, disruption & validation (%)', chartB, [['Selection accuracy', '#5B8DEF'], ['Chain disruption', '#8B5CF6'], ['Validation rate', '#5B9E6F']]]].map(([title, d, bars]) => (
                <div key={title} className="bg-base-900 border border-base-700 rounded-lg p-4">
                  <h3 className="text-sm font-semibold mb-3">{title}</h3>
                  <div className="h-64"><ResponsiveContainer>
                    <BarChart data={d}><CartesianGrid stroke={cc.grid} vertical={false} />
                      <XAxis dataKey="name" tick={AXIS} /><YAxis domain={[0, 100]} tick={AXIS} />
                      <Tooltip contentStyle={TIP} cursor={{ fill: cc.cursor }} /><Legend wrapperStyle={{ fontSize: 11 }} />
                      {bars.map(([k, c]) => <Bar key={k} dataKey={k} fill={c} />)}</BarChart></ResponsiveContainer></div>
                </div>))}
            </div>
            <p className="text-xs text-base-400 -mt-3">The LLM recommendation-only condition is excluded from the first chart: it never applies or replays a control, so before/after is N/A.</p>

            <section className="space-y-2"><h2 className="text-sm font-semibold">Metrics by condition</h2>
              <div className="overflow-x-auto border border-base-700 rounded-lg scrollbar-thin">
                <table className="w-full text-xs"><thead className="bg-base-800 text-base-300"><tr>
                  <th className="text-left p-2">Condition</th><th className="p-2">n</th>
                  {COLS.map(([, l]) => <th key={l} className="p-2 text-right">{l}</th>)}<th className="p-2 text-right">Residual steps</th><th className="p-2 text-right">LLM calls</th></tr></thead>
                  <tbody className="divide-y divide-base-700 font-mono">{rows.map((r) => (
                    <tr key={r.key}><td className="p-2 font-sans">{r.label}</td><td className="p-2 text-center">{r.experiment_count}</td>
                      {COLS.map(([f]) => <td key={f} className="p-2 text-right">{pct(r[f])}</td>)}
                      <td className="p-2 text-right">{r.residual_vulnerable_steps.length}</td><td className="p-2 text-right">{r.llm_calls}</td></tr>))}</tbody></table>
              </div>
            </section>

            <section className="space-y-2"><h2 className="text-sm font-semibold">Individual experiments</h2>
              <div className="overflow-x-auto border border-base-700 rounded-lg scrollbar-thin">
                <table className="w-full text-xs"><thead className="bg-base-800 text-base-300"><tr>
                  {['ID', 'Condition', 'Test', 'Expected', 'Selected', 'Disrupted', 'Result'].map((h) => <th key={h} className="text-left p-2">{h}</th>)}</tr></thead>
                  <tbody className="divide-y divide-base-700">{data.records.map((r) => (
                    <tr key={r.experiment_id}><td className="p-2 font-mono">{r.experiment_id}</td><td className="p-2">{CONDITIONS[r.condition]}</td>
                      <td className="p-2 font-mono">{r.test}</td><td className="p-2">{controlLabel(r.expected_control)}</td>
                      <td className={`p-2 ${r.selection_correct ? '' : 'text-sev-high'}`}>{controlLabel(r.selected_control)}</td>
                      <td className="p-2">{r.condition === 'llm_recommendation_only' ? 'N/A' : r.chain_disrupted ? 'Yes' : 'No'}</td>
                      <td className="p-2">{r.condition === 'llm_recommendation_only' ? 'Not applied' : r.mitigation_validation ? <span className="text-sev-low">VALIDATED</span> : <span className="text-sev-critical">FAILED</span>}</td></tr>))}</tbody></table>
              </div>
            </section>
          </>
        )}
      </main>
    </>
  )
}
