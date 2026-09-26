import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import TopBar from '../components/TopBar'
import StatCard from '../components/StatCard'
import { ModeBadge, StatusBadge, SeverityBadge } from '../components/Badges'
import { LoadingState, ErrorState, EmptyState } from '../components/States'
import { getExperiment, getExperimentFindings, getExperimentChains, getExperimentLogs } from '../api/client'

export default function ExperimentDetails() {
  const { id } = useParams()
  const [state, setState] = useState({ loading: true, error: null, exp: null, findings: [], chains: [], logs: [] })

  async function load() {
    setState((s) => ({ ...s, loading: true, error: null }))
    try {
      const [exp, findings, chains, logs] = await Promise.all([
        getExperiment(id),
        getExperimentFindings(id),
        getExperimentChains(id),
        getExperimentLogs(id),
      ])
      setState({ loading: false, error: null, exp, findings, chains, logs })
    } catch (e) {
      setState((s) => ({ ...s, loading: false, error: e.message }))
    }
  }

  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id])

  const { loading, error, exp, findings, chains, logs } = state

  return (
    <>
      <TopBar
        title={exp ? exp.name : 'Experiment'}
        subtitle={id}
        actions={exp && <ModeBadge mode={exp.mode} />}
      />
      <div className="flex-1 overflow-y-auto scrollbar-thin p-6 space-y-6">
        {loading && <LoadingState />}
        {error && <ErrorState message={error} onRetry={load} />}
        {!loading && !error && exp && (
          <>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <StatCard label="Status" value={<StatusBadge status={exp.status} />} />
              <StatCard label="Tests run" value={`${exp.tests_run}/${exp.max_tests}`} />
              <StatCard label="Findings" value={exp.findings_count} />
              <StatCard label="Validated chains" value={`${exp.validated_chains}/${exp.candidate_chains}`} />
            </div>

            <div>
              <h2 className="text-sm font-medium text-base-200 mb-3">Findings</h2>
              {findings.length === 0 ? (
                <EmptyState title="No findings recorded for this experiment yet" />
              ) : (
                <div className="space-y-2">
                  {findings.map((f) => (
                    <div key={f.finding_id} className="border border-base-700 rounded-lg px-4 py-3 bg-base-900">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-xs text-base-400">{f.finding_id}</span>
                          <span className="text-sm text-base-100">{f.type.replaceAll('_', ' ')}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <SeverityBadge severity={f.severity} />
                          {f.validated && <StatusBadge status="validated" />}
                        </div>
                      </div>
                      <p className="text-xs text-base-400 mt-1.5">{f.evidence}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div>
              <h2 className="text-sm font-medium text-base-200 mb-3">Candidate chains</h2>
              {chains.length === 0 ? (
                <EmptyState title="No chains formed yet" description="Chains appear once findings link across tests." />
              ) : (
                <div className="space-y-2">
                  {chains.map((c) => (
                    <div key={c.chain_id} className="border border-base-700 rounded-lg px-4 py-3 bg-base-900 flex items-center justify-between">
                      <div>
                        <span className="font-mono text-xs text-base-400">{c.chain_id}</span>
                        <span className="text-sm text-base-100 ml-2">{c.steps.join(' → ')}</span>
                      </div>
                      <StatusBadge status={c.status} />
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div>
              <h2 className="text-sm font-medium text-base-200 mb-3">Recent activity</h2>
              <Link to="/logs" className="text-xs text-signal hover:underline">
                View full live log →
              </Link>
              <div className="mt-3 space-y-1.5 font-mono text-xs text-base-400 max-h-48 overflow-y-auto scrollbar-thin">
                {logs.slice(0, 5).map((l) => (
                  <div key={l.id}>
                    <span className="text-base-500">{new Date(l.timestamp).toLocaleTimeString()}</span>{' '}
                    <span className="text-base-300">{l.event}</span> — {l.detail}
                  </div>
                ))}
              </div>
            </div>
          </>
        )}
      </div>
    </>
  )
}
