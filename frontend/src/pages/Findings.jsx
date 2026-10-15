import { useEffect, useMemo, useState } from 'react'
import TopBar from '../components/TopBar'
import { SeverityBadge } from '../components/Badges'
import {
  LoadingState,
  ErrorState,
  EmptyState,
} from '../components/States'
import {
  listExperiments,
  getExperimentFindings,
} from '../api/client'

const SEVERITIES = [
  'all',
  'critical',
  'high',
  'medium',
  'low',
]

export default function Findings() {
  const [state, setState] = useState({
    loading: true,
    error: null,
    data: [],
  })

  const [severity, setSeverity] = useState('all')
  const [query, setQuery] = useState('')

  async function load() {
    setState({
      loading: true,
      error: null,
      data: [],
    })

    try {
      const experiments = await listExperiments()

      const results = await Promise.all(
        experiments.map((experiment) =>
          getExperimentFindings(
            experiment.experiment_id,
          ),
        ),
      )

      setState({
        loading: false,
        error: null,
        data: results.flat(),
      })
    } catch (e) {
      setState({
        loading: false,
        error: e.message,
        data: [],
      })
    }
  }

  useEffect(() => {
    load()
  }, [])

  const filtered = useMemo(() => {
    const needle = query.trim().toLowerCase()

    return state.data.filter((finding) => {
      if (severity !== 'all' && finding.severity !== severity) {
        return false
      }

      if (!needle) {
        return true
      }

      // Phase 3: free-text search over experiment, test, finding and evidence.
      return [
        finding.experiment_id,
        finding.test,
        finding.finding,
        JSON.stringify(finding.evidence ?? ''),
      ].some((value) => String(value ?? '').toLowerCase().includes(needle))
    })
  }, [state.data, severity, query])

  return (
    <>
      <TopBar
        title="Findings"
        subtitle="Every finding recorded across all experiments"
        actions={
          <div className="flex items-center gap-2">
            <button
              onClick={load}
              disabled={state.loading}
              className="border border-base-700 text-base-300 text-xs font-medium px-3 py-1.5 rounded-md hover:border-signal hover:text-signal transition-colors disabled:opacity-50"
            >
              {state.loading ? 'Refreshing…' : 'Refresh'}
            </button>

            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              aria-label="Search findings"
              placeholder="Search findings…"
              className="w-48 bg-base-900 border border-base-700 rounded-md px-2.5 py-1 text-xs text-base-100 placeholder:text-base-500 focus:border-signal outline-none"
            />

            <div className="flex gap-1">
              {SEVERITIES.map((item) => (
                <button
                  key={item}
                  onClick={() => setSeverity(item)}
                  className={`text-xs px-2.5 py-1 rounded-md border capitalize ${
                    severity === item
                      ? 'border-signal text-signal bg-signal/10'
                      : 'border-base-700 text-base-400 hover:text-base-200'
                  }`}
                >
                  {item}
                </button>
              ))}
            </div>
          </div>
        }
      />

      <div className="flex-1 overflow-y-auto scrollbar-thin p-6">
        {state.loading && <LoadingState />}

        {state.error && (
          <ErrorState
            message={state.error}
            onRetry={load}
          />
        )}

        {!state.loading &&
          !state.error &&
          filtered.length === 0 && (
            <EmptyState
              title="No findings match this filter"
            />
          )}

        {!state.loading &&
          !state.error &&
          filtered.length > 0 && (
            <div className="border border-base-700 rounded-lg overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-base-900 text-base-400 text-xs">
                    <th className="text-left font-medium px-4 py-2.5">
                      Experiment
                    </th>

                    <th className="text-left font-medium px-4 py-2.5">
                      Test
                    </th>

                    <th className="text-left font-medium px-4 py-2.5">
                      Finding
                    </th>

                    <th className="text-left font-medium px-4 py-2.5">
                      Severity
                    </th>

                    <th className="text-left font-medium px-4 py-2.5">
                      Confidence
                    </th>

                    <th className="text-left font-medium px-4 py-2.5">
                      Evidence
                    </th>

                    <th className="text-left font-medium px-4 py-2.5">
                      Time
                    </th>
                  </tr>
                </thead>

                <tbody>
                  {filtered.map((finding, index) => (
                    <tr
                      key={`${finding.experiment_id}-${finding.test}-${index}`}
                      className="border-t border-base-700 hover:bg-base-900/60"
                    >
                      <td className="px-4 py-2.5 font-mono text-xs text-base-400">
                        {finding.experiment_id}
                      </td>

                      <td className="px-4 py-2.5 font-mono text-xs text-base-300">
                        {finding.test}
                      </td>

                      <td className="px-4 py-2.5 text-base-100">
                        {finding.finding?.replaceAll('_', ' ')}
                      </td>

                      <td className="px-4 py-2.5">
                        <SeverityBadge
                          severity={finding.severity}
                        />
                      </td>

                      <td className="px-4 py-2.5 font-mono text-base-300">
                        {typeof finding.confidence === 'number'
                          ? `${Math.round(
                              finding.confidence * 100,
                            )}%`
                          : '—'}
                      </td>

                      <td
                        className="px-4 py-2.5 text-base-400 text-xs max-w-md truncate"
                        title={JSON.stringify(
                          finding.evidence,
                        )}
                      >
                        {JSON.stringify(
                          finding.evidence,
                        )}
                      </td>

                      <td className="px-4 py-2.5 text-xs text-base-400">
                        {finding.timestamp
                          ? new Date(
                              finding.timestamp,
                            ).toLocaleString()
                          : '—'}
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