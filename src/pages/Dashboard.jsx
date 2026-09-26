import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Plus } from 'lucide-react'
import TopBar from '../components/TopBar'
import StatCard from '../components/StatCard'
import { ModeBadge, StatusBadge } from '../components/Badges'
import { LoadingState, ErrorState, EmptyState } from '../components/States'
import { listExperiments, getAllFindings, getAllChains } from '../api/client'

export default function Dashboard() {
  const [state, setState] = useState({ loading: true, error: null, experiments: [], findings: [], chains: [] })

  async function load() {
    setState((s) => ({ ...s, loading: true, error: null }))
    try {
      const [experiments, findings, chains] = await Promise.all([
        listExperiments(),
        getAllFindings(),
        getAllChains(),
      ])
      setState({ loading: false, error: null, experiments, findings, chains })
    } catch (e) {
      setState((s) => ({ ...s, loading: false, error: e.message }))
    }
  }

  useEffect(() => {
    load()
  }, [])

  const { loading, error, experiments, findings, chains } = state
  const validated = chains.filter((c) => c.status === 'validated')
  const validationRate = chains.length ? Math.round((validated.length / chains.length) * 100) : 0
  const avgChainLength = chains.length
    ? (chains.reduce((sum, c) => sum + c.length, 0) / chains.length).toFixed(1)
    : '0.0'

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
              <StatCard label="Experiments" value={experiments.length} />
              <StatCard label="Findings" value={findings.length} />
              <StatCard label="Candidate chains" value={chains.length} />
              <StatCard label="Validated chains" value={validated.length} accent="#5B9E6F" />
              <StatCard label="Validation rate" value={`${validationRate}%`} />
              <StatCard label="Avg chain length" value={avgChainLength} />
            </div>

            <div>
              <h2 className="text-sm font-medium text-base-200 mb-3">Recent experiments</h2>
              {experiments.length === 0 ? (
                <EmptyState
                  title="No experiments yet"
                  description="Start one to begin discovering attack chains."
                  action={
                    <Link to="/new-experiment" className="text-signal text-xs mt-1 hover:underline">
                      Create your first experiment →
                    </Link>
                  }
                />
              ) : (
                <div className="border border-base-700 rounded-lg overflow-hidden">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="bg-base-900 text-base-400 text-xs">
                        <th className="text-left font-medium px-4 py-2.5">Name</th>
                        <th className="text-left font-medium px-4 py-2.5">Mode</th>
                        <th className="text-left font-medium px-4 py-2.5">Status</th>
                        <th className="text-left font-medium px-4 py-2.5">Tests</th>
                        <th className="text-left font-medium px-4 py-2.5">Findings</th>
                        <th className="text-left font-medium px-4 py-2.5">Chains</th>
                      </tr>
                    </thead>
                    <tbody>
                      {experiments.map((exp) => (
                        <tr
                          key={exp.experiment_id}
                          className="border-t border-base-700 hover:bg-base-900/60 cursor-pointer"
                        >
                          <td className="px-4 py-2.5">
                            <Link to={`/experiments/${exp.experiment_id}`} className="text-base-100 hover:text-signal">
                              {exp.name}
                            </Link>
                            <div className="text-xs text-base-400 font-mono">{exp.experiment_id}</div>
                          </td>
                          <td className="px-4 py-2.5"><ModeBadge mode={exp.mode} /></td>
                          <td className="px-4 py-2.5"><StatusBadge status={exp.status} /></td>
                          <td className="px-4 py-2.5 text-base-300 font-mono">
                            {exp.tests_run}/{exp.max_tests}
                          </td>
                          <td className="px-4 py-2.5 text-base-300 font-mono">{exp.findings_count}</td>
                          <td className="px-4 py-2.5 text-base-300 font-mono">
                            {exp.validated_chains}/{exp.candidate_chains}
                          </td>
                        </tr>
                      ))}
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
