import { useEffect, useState } from 'react'
import TopBar from '../components/TopBar'
import {
  LoadingState,
  ErrorState,
  EmptyState,
} from '../components/States'
import {
  listExperiments,
  getExperimentLogs,
} from '../api/client'

export default function LiveLogs() {
  const [experiments, setExperiments] =
    useState([])

  const [selected, setSelected] =
    useState('')

  const [state, setState] = useState({
    loading: true,
    error: null,
    logs: [],
  })

  useEffect(() => {
    async function loadExperiments() {
      try {
        const exps =
          await listExperiments()

        setExperiments(exps)

        if (exps.length) {
          setSelected(
            exps[0].experiment_id,
          )
        }
      } catch (e) {
        setState({
          loading: false,
          error: e.message,
          logs: [],
        })
      }
    }

    loadExperiments()
  }, [])

  async function load(id) {
    if (!id) return

    setState({
      loading: true,
      error: null,
      logs: [],
    })

    try {
      const logs =
        await getExperimentLogs(id)

      setState({
        loading: false,
        error: null,
        logs,
      })
    } catch (e) {
      setState({
        loading: false,
        error: e.message,
        logs: [],
      })
    }
  }

  useEffect(() => {
    load(selected)
  }, [selected])

  return (
    <>
      <TopBar
        title="Live Logs"
        subtitle="Chronological event stream for a running or completed experiment"
        actions={
          <select
            value={selected}
            onChange={(e) =>
              setSelected(e.target.value)
            }
            className="bg-base-900 border border-base-700 rounded-md px-3 py-1.5 text-sm text-base-200 focus:border-signal outline-none"
          >
            {experiments.map((e) => (
              <option
                key={e.experiment_id}
                value={e.experiment_id}
              >
                {e.name}
              </option>
            ))}
          </select>
        }
      />

      <div className="flex-1 overflow-y-auto scrollbar-thin p-6">
        {state.loading && (
          <LoadingState />
        )}

        {state.error && (
          <ErrorState
            message={state.error}
            onRetry={() =>
              load(selected)
            }
          />
        )}

        {!state.loading &&
          !state.error &&
          state.logs.length === 0 && (
            <EmptyState
              title="No log events yet"
              description="Events appear as the experiment runs."
            />
          )}

        {!state.loading &&
          !state.error &&
          state.logs.length > 0 && (
            <div className="bg-base-900 border border-base-700 rounded-lg font-mono text-xs divide-y divide-base-700/60">
              {state.logs.map(
                (log, index) => (
                  <div
                    key={`${log.timestamp}-${index}`}
                    className="px-4 py-2.5 flex gap-3"
                  >
                    <span className="text-base-500 shrink-0 w-24">
                      {new Date(
                        log.timestamp,
                      ).toLocaleTimeString()}
                    </span>

                    <span className="text-base-300">
                      {log.message}
                    </span>
                  </div>
                ),
              )}
            </div>
          )}
      </div>
    </>
  )
}