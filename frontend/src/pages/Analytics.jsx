import { useEffect, useMemo, useState } from 'react'
import TopBar from '../components/TopBar'
import StatCard from '../components/StatCard'
import {
  LoadingState,
  ErrorState,
} from '../components/States'
import { getAnalytics, listExperiments } from '../api/client'
import { useTheme, chartColors } from '../lib/theme'

import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from 'recharts'

export default function Analytics() {
  const { dark } = useTheme()
  const cc = chartColors(dark)
  const [state, setState] = useState({
    loading: true,
    error: null,
    data: null,
    experiments: [],
  })

  async function load() {
    setState((current) => ({
      ...current,
      loading: true,
      error: null,
    }))

    try {
      const [analytics, experiments] =
        await Promise.all([
          getAnalytics(),
          listExperiments(),
        ])

      setState({
        loading: false,
        error: null,
        data: analytics,
        experiments,
      })
    } catch (e) {
      setState({
        loading: false,
        error: e.message,
        data: null,
        experiments: [],
      })
    }
  }

  useEffect(() => {
    load()
  }, [])

  const {
    loading,
    error,
    data,
    experiments,
  } = state

  const modeData = useMemo(() => {
    const counts = {}

    experiments.forEach((experiment) => {
      const mode = experiment.mode || 'unknown'

      counts[mode] = (counts[mode] || 0) + 1
    })

    return Object.entries(counts).map(
      ([mode, count]) => ({
        mode,
        count,
      }),
    )
  }, [experiments])

  const statusData = useMemo(() => {
    const counts = {}

    experiments.forEach((experiment) => {
      const status =
        experiment.status || 'unknown'

      counts[status] =
        (counts[status] || 0) + 1
    })

    return Object.entries(counts).map(
      ([status, count]) => ({
        status,
        count,
      }),
    )
  }, [experiments])

  return (
    <>
      <TopBar
      title="Analytics"
      subtitle="Current AgentChain backend evaluation totals"
      actions={
      <button
      onClick={load}
      disabled={loading}
      className="btn-primary text-xs font-medium px-3 py-1.5 rounded-md  transition-colors disabled:opacity-50"
      >
      {loading ? 'Refreshing…' : 'Refresh'}
      </button>
      }
      />

      <div className="flex-1 overflow-y-auto scrollbar-thin p-6 space-y-6">
        {loading && <LoadingState />}

        {error && (
          <ErrorState
            message={error}
            onRetry={load}
          />
        )}

        {!loading && !error && data && (
          <>
            {/* Backend totals */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
              <StatCard
                label="Total experiments"
                value={data.total_experiments}
              />

              <StatCard
                label="Total findings"
                value={data.total_findings}
              />

              <StatCard
                label="Total chains"
                value={data.total_chains}
              />

              <StatCard
                label="Evaluation results"
                value={
                  data.total_evaluation_results
                }
              />
            </div>

            {/* Experiments by mode */}
            <div className="border border-base-700 rounded-lg bg-base-900 p-5">
              <h2 className="text-sm font-medium text-base-200 mb-4">
                Experiments by Mode
              </h2>

              {modeData.length === 0 ? (
                <p className="text-xs text-base-400">
                  No experiment mode data available.
                </p>
              ) : (
                <div className="h-64">
                  <ResponsiveContainer
                    width="100%"
                    height="100%"
                  >
                    <BarChart data={modeData}>
                      <CartesianGrid
                        strokeDasharray="3 3"
                        stroke={cc.grid}
                      />

                      <XAxis
                        dataKey="mode"
                        tick={{
                          fill: cc.axis,
                          fontSize: 12,
                        }}
                      />

                      <YAxis
                        allowDecimals={false}
                        tick={{
                          fill: cc.axis,
                          fontSize: 12,
                        }}
                      />

                      <Tooltip contentStyle={cc.tooltip} cursor={{ fill: cc.cursor }} />

                      <Bar
                        dataKey="count"
                        name="Experiments"
                        fill="#3B82F6"
                        radius={[4, 4, 0, 0]}
                      />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}
            </div>

            {/* Experiments by status */}
            <div className="border border-base-700 rounded-lg bg-base-900 p-5">
              <h2 className="text-sm font-medium text-base-200 mb-4">
                Experiments by Status
              </h2>

              {statusData.length === 0 ? (
                <p className="text-xs text-base-400">
                  No experiment status data available.
                </p>
              ) : (
                <div className="h-64">
                  <ResponsiveContainer
                    width="100%"
                    height="100%"
                  >
                    <BarChart data={statusData}>
                      <CartesianGrid
                        strokeDasharray="3 3"
                        stroke={cc.grid}
                      />

                      <XAxis
                        dataKey="status"
                        tick={{
                          fill: cc.axis,
                          fontSize: 12,
                        }}
                      />

                      <YAxis
                        allowDecimals={false}
                        tick={{
                          fill: cc.axis,
                          fontSize: 12,
                        }}
                      />

                      <Tooltip contentStyle={cc.tooltip} cursor={{ fill: cc.cursor }} />

                      <Bar
                        dataKey="count"
                        name="Experiments"
                        fill="#8B5CF6"
                        radius={[4, 4, 0, 0]}
                      />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}
            </div>

            {/* Backend analytics information */}
            <div className="border border-base-700 rounded-lg bg-base-900 p-5">
              <h2 className="text-sm font-medium text-base-200 mb-2">
                Backend Analytics
              </h2>

              <p className="text-xs text-base-400 leading-relaxed">
                These values are supplied directly by
                Person 2's current
                <span className="font-mono text-base-300">
                  {' '}GET /analytics
                </span>
                {' '}endpoint. Experiment mode and status
                charts are derived from the real
                <span className="font-mono text-base-300">
                  {' '}GET /experiments
                </span>
                {' '}response.
              </p>
            </div>
          </>
        )}
      </div>
    </>
  )
}