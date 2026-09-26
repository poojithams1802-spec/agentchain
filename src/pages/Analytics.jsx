import { useEffect, useState } from 'react'
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  PieChart,
  Pie,
  Cell,
} from 'recharts'
import TopBar from '../components/TopBar'
import StatCard from '../components/StatCard'
import { LoadingState, ErrorState } from '../components/States'
import { getAnalytics } from '../api/client'

const SEV_COLOR = { critical: '#E5484D', high: '#E8734D', medium: '#E8A33D', low: '#5B9E6F' }

const tooltipStyle = {
  background: '#14171C',
  border: '1px solid #262B33',
  borderRadius: 6,
  fontSize: 12,
  color: '#E4E6EA',
}

export default function Analytics() {
  const [state, setState] = useState({ loading: true, error: null, data: null })

  async function load() {
    setState({ loading: true, error: null, data: null })
    try {
      const data = await getAnalytics()
      setState({ loading: false, error: null, data })
    } catch (e) {
      setState({ loading: false, error: e.message, data: null })
    }
  }

  useEffect(() => {
    load()
  }, [])

  const { loading, error, data } = state

  const comparisonData = data
    ? [
        { metric: 'Total tests', Static: data.summary.static.total_tests, Adaptive: data.summary.adaptive.total_tests },
        { metric: 'Findings', Static: data.summary.static.total_findings, Adaptive: data.summary.adaptive.total_findings },
        { metric: 'Valid findings', Static: data.summary.static.valid_findings, Adaptive: data.summary.adaptive.valid_findings },
        { metric: 'Validated chains', Static: data.summary.static.validated_chains, Adaptive: data.summary.adaptive.validated_chains },
      ]
    : []

  return (
    <>
      <TopBar title="Analytics" subtitle="Static vs Adaptive testing — research comparison" />
      <div className="flex-1 overflow-y-auto scrollbar-thin p-6 space-y-6">
        {loading && <LoadingState />}
        {error && <ErrorState message={error} onRetry={load} />}
        {!loading && !error && data && (
          <>
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
              <StatCard label="Adaptive validation rate" value={`${Math.round(data.summary.adaptive.validation_rate * 100)}%`} accent="#E8A33D" />
              <StatCard label="Static validation rate" value={`${Math.round(data.summary.static.validation_rate * 100)}%`} accent="#5B8DEF" />
              <StatCard label="Avg chain length (adaptive)" value={data.summary.adaptive.avg_chain_length.toFixed(1)} />
              <StatCard label="LLM calls (adaptive)" value={data.summary.adaptive.llm_calls.toFixed(1)} />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <div className="border border-base-700 rounded-lg bg-base-900 p-4">
                <h2 className="text-sm font-medium text-base-200 mb-4">Static vs Adaptive — key metrics</h2>
                <ResponsiveContainer width="100%" height={280}>
                  <BarChart data={comparisonData} barGap={6}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1B1F26" vertical={false} />
                    <XAxis dataKey="metric" tick={{ fill: '#8A909A', fontSize: 11 }} axisLine={{ stroke: '#262B33' }} tickLine={false} />
                    <YAxis tick={{ fill: '#8A909A', fontSize: 11 }} axisLine={{ stroke: '#262B33' }} tickLine={false} />
                    <Tooltip contentStyle={tooltipStyle} cursor={{ fill: '#1B1F26' }} />
                    <Legend wrapperStyle={{ fontSize: 12, color: '#B8BDC5' }} />
                    <Bar dataKey="Static" fill="#5B8DEF" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="Adaptive" fill="#E8A33D" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              <div className="border border-base-700 rounded-lg bg-base-900 p-4">
                <h2 className="text-sm font-medium text-base-200 mb-4">Findings by severity</h2>
                <ResponsiveContainer width="100%" height={280}>
                  <PieChart>
                    <Pie
                      data={data.severityBreakdown}
                      dataKey="count"
                      nameKey="severity"
                      innerRadius={55}
                      outerRadius={90}
                      paddingAngle={2}
                    >
                      {data.severityBreakdown.map((entry) => (
                        <Cell key={entry.severity} fill={SEV_COLOR[entry.severity]} stroke="#0F1115" />
                      ))}
                    </Pie>
                    <Tooltip contentStyle={tooltipStyle} />
                    <Legend wrapperStyle={{ fontSize: 12, color: '#B8BDC5' }} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="border border-base-700 rounded-lg bg-base-900 p-4">
              <h2 className="text-sm font-medium text-base-200 mb-4">Tests vs findings by experiment</h2>
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={data.byExperiment} barGap={6}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1B1F26" vertical={false} />
                  <XAxis dataKey="experiment_id" tick={{ fill: '#8A909A', fontSize: 11 }} axisLine={{ stroke: '#262B33' }} tickLine={false} />
                  <YAxis tick={{ fill: '#8A909A', fontSize: 11 }} axisLine={{ stroke: '#262B33' }} tickLine={false} />
                  <Tooltip contentStyle={tooltipStyle} cursor={{ fill: '#1B1F26' }} />
                  <Legend wrapperStyle={{ fontSize: 12, color: '#B8BDC5' }} />
                  <Bar dataKey="tests" name="Tests run" fill="#5C636D" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="findings" name="Findings" fill="#E8A33D" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </>
        )}
      </div>
    </>
  )
}
