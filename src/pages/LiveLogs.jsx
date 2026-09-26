import { useEffect, useState } from 'react'
import TopBar from '../components/TopBar'
import { LoadingState, ErrorState, EmptyState } from '../components/States'
import { listExperiments, getExperimentLogs } from '../api/client'

const EVENT_COLOR = {
  experiment_started: 'text-info',
  test_selected: 'text-signal',
  finding_recorded: 'text-sev-high',
  rag_retrieval: 'text-base-300',
  candidate_chain_formed: 'text-sev-medium',
}

export default function LiveLogs() {
  const [experiments, setExperiments] = useState([])
  const [selected, setSelected] = useState('')
  const [state, setState] = useState({ loading: true, error: null, logs: [] })

  useEffect(() => {
    listExperiments().then((exps) => {
      setExperiments(exps)
      if (exps.length) setSelected(exps[0].experiment_id)
    })
  }, [])

  async function load(id) {
    if (!id) return
    setState({ loading: true, error: null, logs: [] })
    try {
      const logs = await getExperimentLogs(id)
      setState({ loading: false, error: null, logs })
    } catch (e) {
      setState({ loading: false, error: e.message, logs: [] })
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
            onChange={(e) => setSelected(e.target.value)}
            className="bg-base-900 border border-base-700 rounded-md px-3 py-1.5 text-sm text-base-200 focus:border-signal outline-none"
          >
            {experiments.map((e) => (
              <option key={e.experiment_id} value={e.experiment_id}>
                {e.name}
              </option>
            ))}
          </select>
        }
      />
      <div className="flex-1 overflow-y-auto scrollbar-thin p-6">
        {state.loading && <LoadingState />}
        {state.error && <ErrorState message={state.error} onRetry={() => load(selected)} />}
        {!state.loading && !state.error && state.logs.length === 0 && (
          <EmptyState title="No log events yet" description="Events appear as the experiment runs." />
        )}
        {!state.loading && !state.error && state.logs.length > 0 && (
          <div className="bg-base-900 border border-base-700 rounded-lg font-mono text-xs divide-y divide-base-700/60">
            {state.logs.map((l) => (
              <div key={l.id} className="px-4 py-2.5 flex gap-3">
                <span className="text-base-500 shrink-0 w-20">{new Date(l.timestamp).toLocaleTimeString()}</span>
                <span className={`shrink-0 w-40 ${EVENT_COLOR[l.event] ?? 'text-base-300'}`}>{l.event}</span>
                <span className="text-base-300">{l.detail}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </>
  )
}
