import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Plus } from 'lucide-react'
import TopBar from '../components/TopBar'
import StatCard from '../components/StatCard'
import { ModeBadge, StatusBadge } from '../components/Badges'
import { LoadingState, ErrorState, EmptyState } from '../components/States'
import {
  listExperiments,
  getExperimentFindings,
  getExperimentChains,
  getAnalytics,
} from '../api/client'

export default function Dashboard() {
  const [state, setState] = useState({
    loading: true,
    error: null,
    experiments: [],
    findings: [],
    chains: [],
    analytics: null,
  })

  async function load() {
    setState((s) => ({ ...s, loading: true, error: null }))

    try {
      const experiments = await listExperiments()

      const experimentData = await Promise.all(
        experiments.map(async (exp) => {
          const [findings, chains] = await Promise.all([
            getExperimentFindings(exp.experiment_id),
            getExperimentChains(exp.experiment_id),
          ])

          return { exp, findings, chains }
        }),
      )

      const findings = experimentData.flatMap((item) => item.findings)
      const chains = experimentData.flatMap((item) => item.chains)
      const analytics = await getAnalytics()

      setState({
        loading: false,
        error: null,
        experiments,
        findings,
        chains,
        analytics,
      })
    } catch (e) {
      setState((s) => ({
        ...s,
        loading: false,
        error: e.message,
      }))
    }
  }

  useEffect(() => {
    load()
  }, [])

  const {
    loading,
    error,
    experiments,
    findings,
    chains,
    analytics,
  } = state

  const totalExperiments =
    analytics?.total_experiments ?? experiments.length

  const totalFindings =
    analytics?.total_findings ?? findings.length

  const totalChains =
    analytics?.total_chains ?? chains.length

  return (
    <>
      <TopBar
        title="Dashboard"
        subtitle="Adaptive Attack-Chain Discovery — research overview"
        actions={
          <Link
            to="/new-experiment"
            className="flex items-center gap-1.5 bg-signal text-base-950 text-sm font-medium px-3 py-1.5 rounded-md hover:bg-signal-bright transition-colors"
          >
            <Plus size={15} /> New Experiment
          </Link>
        }
      />

      <div className="flex-1 overflow-y-auto scrollbar-thin p-6 space-y-6">
        {loading && <LoadingState label="Loading dashboard…" />}

        {error && <ErrorState message={error} onRetry={load} />}

        {!loading && !error && (
          <>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
              <StatCard
                label="Experiments"
                value={totalExperiments}
              />

              <StatCard
                label="Findings"
                value={totalFindings}
              />

              <StatCard
                label="Candidate chains"
                value={totalChains}
              />

              <StatCard
                label="Validation results"
                value={analytics?.total_evaluation_results ?? 0}
              />

              <StatCard
                label="Completed"
                value={
                  experiments.filter(
                    (e) => e.status === 'completed',
                  ).length
                }
              />

              <StatCard
                label="Active"
                value={
                  experiments.filter(
                    (e) => e.status === 'running',
                  ).length
                }
              />
            </div>

            <div>
              <h2 className="text-sm font-medium text-base-200 mb-3">
                Recent experiments
              </h2>

              {experiments.length === 0 ? (
                <EmptyState
                  title="No experiments yet"
                  description="Start one to begin discovering attack chains."
                  action={
                    <Link
                      to="/new-experiment"
                      className="text-signal text-xs mt-1 hover:underline"
                    >
                      Create your first experiment →
                    </Link>
                  }
                />
              ) : (
                <div className="border border-base-700 rounded-lg overflow-hidden">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="bg-base-900 text-base-400 text-xs">
                        <th className="text-left font-medium px-4 py-2.5">
                          Name
                        </th>
                        <th className="text-left font-medium px-4 py-2.5">
                          Mode
                        </th>
                        <th className="text-left font-medium px-4 py-2.5">
                          Status
                        </th>
                        <th className="text-left font-medium px-4 py-2.5">
                          Max tests
                        </th>
                        <th className="text-left font-medium px-4 py-2.5">
                          Findings
                        </th>
                        <th className="text-left font-medium px-4 py-2.5">
                          Chains
                        </th>
                      </tr>
                    </thead>

                    <tbody>
                      {experiments.map((exp) => {
                        const expFindings = findings.filter(
                          (f) =>
                            f.experiment_id === exp.experiment_id,
                        )

                        const expChains = chains.filter(
                          (c) =>
                            c.experiment_id === exp.experiment_id,
                        )

                        return (
                          <tr
                            key={exp.experiment_id}
                            className="border-t border-base-700 hover:bg-base-900/60"
                          >
                            <td className="px-4 py-2.5">
                              <Link
                                to={`/experiments/${exp.experiment_id}`}
                                className="text-base-100 hover:text-signal"
                              >
                                {exp.name}
                              </Link>

                              <div className="text-xs text-base-400 font-mono">
                                {exp.experiment_id}
                              </div>
                            </td>

                            <td className="px-4 py-2.5">
                              <ModeBadge mode={exp.mode} />
                            </td>

                            <td className="px-4 py-2.5">
                              <StatusBadge status={exp.status} />
                            </td>

                            <td className="px-4 py-2.5 text-base-300 font-mono">
                              {exp.max_tests}
                            </td>

                            <td className="px-4 py-2.5 text-base-300 font-mono">
                              {expFindings.length}
                            </td>

                            <td className="px-4 py-2.5 text-base-300 font-mono">
                              {expChains.length}
                            </td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </>
  )
}