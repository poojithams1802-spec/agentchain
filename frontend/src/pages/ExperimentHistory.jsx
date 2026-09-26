import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import TopBar from '../components/TopBar'
import { ModeBadge, StatusBadge } from '../components/Badges'
import { LoadingState, ErrorState, EmptyState } from '../components/States'
import { listExperiments } from '../api/client'

export default function ExperimentHistory() {
  const [state, setState] = useState({ loading: true, error: null, data: [] })

  async function load() {
    setState({ loading: true, error: null, data: [] })
    try {
      const data = await listExperiments()
      setState({ loading: false, error: null, data })
    } catch (e) {
      setState({ loading: false, error: e.message, data: [] })
    }
  }

  useEffect(() => {
    load()
  }, [])

  const { loading, error, data } = state

  return (
    <>
      <TopBar title="Experiment History" subtitle="All experiment runs, static and adaptive" />
      <div className="flex-1 overflow-y-auto scrollbar-thin p-6">
        {loading && <LoadingState />}
        {error && <ErrorState message={error} onRetry={load} />}
        {!loading && !error && data.length === 0 && (
          <EmptyState title="No experiments recorded yet" description="Experiments you run will appear here." />
        )}
        {!loading && !error && data.length > 0 && (
          <div className="border border-base-700 rounded-lg overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-base-900 text-base-400 text-xs">
                  <th className="text-left font-medium px-4 py-2.5">ID</th>
                  <th className="text-left font-medium px-4 py-2.5">Name</th>
                  <th className="text-left font-medium px-4 py-2.5">Mode</th>
                  <th className="text-left font-medium px-4 py-2.5">Status</th>
                  <th className="text-left font-medium px-4 py-2.5">Tests</th>
                  <th className="text-left font-medium px-4 py-2.5">Findings</th>
                  <th className="text-left font-medium px-4 py-2.5">Validated chains</th>
                  <th className="text-left font-medium px-4 py-2.5">Created</th>
                </tr>
              </thead>
              <tbody>
                {data.map((exp) => (
                  <tr key={exp.experiment_id} className="border-t border-base-700 hover:bg-base-900/60">
                    <td className="px-4 py-2.5 font-mono text-base-400 text-xs">{exp.experiment_id}</td>
                    <td className="px-4 py-2.5">
                      <Link to={`/experiments/${exp.experiment_id}`} className="text-base-100 hover:text-signal">
                        {exp.name}
                      </Link>
                    </td>
                    <td className="px-4 py-2.5"><ModeBadge mode={exp.mode} /></td>
                    <td className="px-4 py-2.5"><StatusBadge status={exp.status} /></td>
                    <td className="px-4 py-2.5 text-base-300 font-mono">{exp.tests_run}/{exp.max_tests}</td>
                    <td className="px-4 py-2.5 text-base-300 font-mono">{exp.findings_count}</td>
                    <td className="px-4 py-2.5 text-base-300 font-mono">{exp.validated_chains}/{exp.candidate_chains}</td>
                    <td className="px-4 py-2.5 text-base-400 text-xs">
                      {new Date(exp.created_at).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </>
  )
}
