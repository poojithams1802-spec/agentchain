import { useEffect, useState } from 'react'
import TopBar from '../components/TopBar'
import StatCard from '../components/StatCard'
import {
  LoadingState,
  ErrorState,
} from '../components/States'
import { getAnalytics } from '../api/client'

export default function Analytics() {
  const [state, setState] = useState({
    loading: true,
    error: null,
    data: null,
  })

  async function load() {
    setState({
      loading: true,
      error: null,
      data: null,
    })

    try {
      const data =
        await getAnalytics()

      setState({
        loading: false,
        error: null,
        data,
      })
    } catch (e) {
      setState({
        loading: false,
        error: e.message,
        data: null,
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
  } = state

  return (
    <>
      <TopBar
        title="Analytics"
        subtitle="Current AgentChain backend evaluation totals"
      />

      <div className="flex-1 overflow-y-auto scrollbar-thin p-6 space-y-6">
        {loading && <LoadingState />}

        {error && (
          <ErrorState
            message={error}
            onRetry={load}
          />
        )}

        {!loading &&
          !error &&
          data && (
            <>
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                <StatCard
                  label="Total experiments"
                  value={
                    data.total_experiments
                  }
                />

                <StatCard
                  label="Total findings"
                  value={
                    data.total_findings
                  }
                />

                <StatCard
                  label="Total chains"
                  value={
                    data.total_chains
                  }
                />

                <StatCard
                  label="Evaluation results"
                  value={
                    data.total_evaluation_results
                  }
                />
              </div>

              <div className="border border-base-700 rounded-lg bg-base-900 p-5">
                <h2 className="text-sm font-medium text-base-200 mb-4">
                  Backend analytics
                </h2>

                <div className="space-y-3 text-sm">
                  <div className="flex justify-between border-b border-base-700 pb-3">
                    <span className="text-base-400">
                      Experiments recorded
                    </span>

                    <span className="font-mono text-base-100">
                      {data.total_experiments}
                    </span>
                  </div>

                  <div className="flex justify-between border-b border-base-700 pb-3">
                    <span className="text-base-400">
                      Findings recorded
                    </span>

                    <span className="font-mono text-base-100">
                      {data.total_findings}
                    </span>
                  </div>

                  <div className="flex justify-between border-b border-base-700 pb-3">
                    <span className="text-base-400">
                      Candidate chains
                    </span>

                    <span className="font-mono text-base-100">
                      {data.total_chains}
                    </span>
                  </div>

                  <div className="flex justify-between">
                    <span className="text-base-400">
                      Evaluation results
                    </span>

                    <span className="font-mono text-base-100">
                      {data.total_evaluation_results}
                    </span>
                  </div>
                </div>
              </div>

              <div className="border border-base-700 rounded-lg bg-base-900 p-5">
                <h2 className="text-sm font-medium text-base-200 mb-2">
                  API coverage
                </h2>

                <p className="text-xs text-base-400 leading-relaxed">
                  These values are supplied directly by
                  Person 2's current
                  <span className="font-mono text-base-300">
                    {' '}GET /analytics
                  </span>
                  {' '}endpoint. Static vs Adaptive
                  comparison metrics, severity breakdowns,
                  and per-experiment chart data are not
                  currently included in that API response.
                </p>
              </div>
            </>
          )}
      </div>
    </>
  )
}