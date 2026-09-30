import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import TopBar from '../components/TopBar'
import StatCard from '../components/StatCard'
import {
  ModeBadge,
  StatusBadge,
  SeverityBadge,
} from '../components/Badges'
import {
  LoadingState,
  ErrorState,
  EmptyState,
} from '../components/States'
import {
  getExperiment,
  getExperimentStatus,
  getExperimentFindings,
  getExperimentChains,
  getExperimentLogs,
} from '../api/client'

export default function ExperimentDetails() {
  const { id } = useParams()

  const [state, setState] = useState({
    loading: true,
    error: null,
    exp: null,
    status: null,
    findings: [],
    chains: [],
    logs: [],
  })

  async function load() {
    setState((current) => ({
      ...current,
      loading: true,
      error: null,
    }))

    try {
      const [
        exp,
        status,
        findings,
        chains,
        logs,
      ] = await Promise.all([
        getExperiment(id),
        getExperimentStatus(id),
        getExperimentFindings(id),
        getExperimentChains(id),
        getExperimentLogs(id),
      ])

      setState({
        loading: false,
        error: null,
        exp,
        status,
        findings,
        chains,
        logs,
      })
    } catch (e) {
      setState((current) => ({
        ...current,
        loading: false,
        error: e.message,
      }))
    }
  }

  useEffect(() => {
    load()
  }, [id])

  const {
    loading,
    error,
    exp,
    status,
    findings,
    chains,
    logs,
  } = state

  return (
    <>
      <TopBar
        title={exp ? exp.name : 'Experiment'}
        subtitle={id}
        actions={
          exp ? <ModeBadge mode={exp.mode} /> : null
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

        {!loading && !error && exp && (
          <>
            {/* Summary */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <StatCard
                label="Status"
                value={
                  <StatusBadge
                    status={status?.status ?? exp.status}
                  />
                }
              />

              <StatCard
                label="Tests with findings"
                value={`${findings.length}/${exp.max_tests}`}
              />

              <StatCard
                label="Findings"
                value={findings.length}
              />

              <StatCard
                label="Candidate chains"
                value={chains.length}
              />
            </div>

            {/* Findings */}
            <section>
              <h2 className="text-sm font-medium text-base-200 mb-3">
                Findings
              </h2>

              {findings.length === 0 ? (
                <EmptyState
                  title="No findings recorded for this experiment yet"
                />
              ) : (
                <div className="space-y-2">
                  {findings.map((finding, index) => (
                    <div
                      key={`${finding.test}-${index}`}
                      className="border border-base-700 rounded-lg px-4 py-3 bg-base-900"
                    >
                      <div className="flex items-center justify-between gap-4">
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-xs text-base-400">
                            {finding.test}
                          </span>

                          <span className="text-sm text-base-100">
                            {finding.finding?.replaceAll('_', ' ')}
                          </span>
                        </div>

                        <SeverityBadge
                          severity={finding.severity}
                        />
                      </div>

                      <p className="text-xs text-base-400 mt-1.5">
                        Confidence:{' '}
                        {typeof finding.confidence === 'number'
                          ? `${Math.round(
                              finding.confidence * 100,
                            )}%`
                          : '—'}
                      </p>

                      <pre className="text-xs text-base-400 mt-2 whitespace-pre-wrap font-mono">
                        {JSON.stringify(
                          finding.evidence,
                          null,
                          2,
                        )}
                      </pre>
                    </div>
                  ))}
                </div>
              )}
            </section>

            {/* Chains */}
            <section>
              <h2 className="text-sm font-medium text-base-200 mb-3">
                Candidate chains
              </h2>

              {chains.length === 0 ? (
                <EmptyState
                  title="No chains formed yet"
                  description="Chains appear once findings link across tests."
                />
              ) : (
                <div className="space-y-2">
                  {chains.map((chain) => (
                    <div
                      key={chain.chain_id}
                      className="border border-base-700 rounded-lg px-4 py-3 bg-base-900"
                    >
                      <div className="flex items-center justify-between gap-4">
                        <div>
                          <span className="font-mono text-xs text-base-400">
                            {chain.chain_id}
                          </span>

                          <div className="text-sm text-base-100 mt-1">
                            {chain.steps.join(' → ')}
                          </div>
                        </div>

                        <span className="text-xs text-base-400">
                          {chain.steps.length} steps
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </section>

            {/* Logs */}
            <section>
              <h2 className="text-sm font-medium text-base-200 mb-3">
                Recent activity
              </h2>

              <Link
                to={`/logs?experiment=${id}`}
                className="text-xs text-signal hover:underline"
              >
                View full live log →
              </Link>

              {logs.length === 0 ? (
                <p className="text-xs text-base-500 mt-3">
                  No log events available.
                </p>
              ) : (
                <div className="mt-3 space-y-1.5 font-mono text-xs text-base-400 max-h-48 overflow-y-auto scrollbar-thin">
                  {logs.slice(0, 5).map((log, index) => (
                    <div key={`${log.timestamp}-${index}`}>
                      <span className="text-base-500">
                        {new Date(
                          log.timestamp,
                        ).toLocaleTimeString()}
                      </span>{' '}

                      <span className="text-base-300">
                        {log.message}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </section>
          </>
        )}
      </div>
    </>
  )
}