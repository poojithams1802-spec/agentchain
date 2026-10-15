import { useEffect, useMemo, useState, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { Play, ShieldCheck, CheckCircle2, XCircle } from 'lucide-react'

import TopBar from '../components/TopBar'
import { SeverityBadge, StatusBadge } from '../components/Badges'
import { LoadingState, ErrorState, EmptyState } from '../components/States'
import ChainGraph, { GraphLegend } from '../components/ChainGraph'
import { Notice, Chip, JsonBlock } from '../components/Phase3Parts'

import {
  listExperiments,
  getExperimentFindings,
  getExperimentChains,
  validateChain,
  executeChain,
  listScenarios,
  apiError,
} from '../api/client'
import { isRegisteredChainId, prettify, fmtPct, fmtSec } from '../lib/phase3'

function StepResults({ result }) {
  if (!result?.steps?.length) return null
  return (
    <div className="mt-3 border border-base-700 rounded-md overflow-hidden">
      <table className="w-full text-[11px]">
        <thead className="bg-base-800 text-base-400">
          <tr>
            <th className="text-left px-2 py-1.5 font-medium">Step</th>
            <th className="text-left px-2 py-1.5 font-medium">Finding</th>
            <th className="px-2 py-1.5 font-medium">Dep.</th>
            <th className="px-2 py-1.5 font-medium">Valid</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-base-700 font-mono">
          {result.steps.map((s) => (
            <tr key={s.test} title={s.dependency_error ?? s.error ?? ''}>
              <td className="px-2 py-1.5 text-base-200 break-all">{s.test}</td>
              <td className={`px-2 py-1.5 ${s.finding_matches === false ? 'text-sev-high' : 'text-base-300'}`}>
                {prettify(s.finding ?? 'none')}
              </td>
              <td className="px-2 py-1.5 text-center">
                {s.dependency_valid === false ? <XCircle size={13} className="inline text-sev-critical" /> : <CheckCircle2 size={13} className="inline text-sev-low" />}
              </td>
              <td className="px-2 py-1.5 text-center">
                {s.valid ? <CheckCircle2 size={13} className="inline text-sev-low" /> : <XCircle size={13} className="inline text-sev-critical" />}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default function ChainExplorer() {
  const [state, setState] = useState({ loading: true, error: null, chains: [], findings: [], scenarios: [] })
  const [expFilter, setExpFilter] = useState('all')
  const [chainFilter, setChainFilter] = useState('all')
  const [selectedNode, setSelectedNode] = useState(null)
  const [busy, setBusy] = useState(null) // 'validate' | 'execute'
  const [results, setResults] = useState({}) // chain_id -> { kind, data | error }

  async function load() {
    setState((s) => ({ ...s, loading: true, error: null }))
    try {
      const experiments = await listExperiments()
      const [perExp, scenarios] = await Promise.all([
        Promise.all(
          experiments.map(async (exp) => {
            const [findings, chains] = await Promise.all([
              getExperimentFindings(exp.experiment_id),
              getExperimentChains(exp.experiment_id),
            ])
            return { findings, chains }
          }),
        ),
        listScenarios().catch(() => []), // scenarios are an enhancement; Phase 1 view still works without them
      ])
      setState({
        loading: false,
        error: null,
        chains: perExp.flatMap((r) => r.chains),
        findings: perExp.flatMap((r) => r.findings),
        scenarios,
      })
    } catch (e) {
      setState((s) => ({ ...s, loading: false, error: apiError(e) }))
    }
  }
  useEffect(() => { load() }, [])

  const experimentIds = useMemo(() => [...new Set(state.chains.map((c) => c.experiment_id))], [state.chains])
  const visibleChains = useMemo(
    () =>
      state.chains.filter(
        (c) => (expFilter === 'all' || c.experiment_id === expFilter) && (chainFilter === 'all' || c.chain_id === chainFilter),
      ),
    [state.chains, expFilter, chainFilter],
  )
  const chainOptions = useMemo(
    () => state.chains.filter((c) => expFilter === 'all' || c.experiment_id === expFilter),
    [state.chains, expFilter],
  )

  // Findings are matched per experiment (Phase 1 matched across all experiments).
  const graphInput = useMemo(
    () =>
      visibleChains.map((chain) => ({
        chain,
        findings: state.findings.filter((f) => f.experiment_id === chain.experiment_id),
        validationSteps: results[chain.chain_id]?.data?.steps,
      })),
    [visibleChains, state.findings, results],
  )

  const onNodeClick = useCallback((data) => setSelectedNode(data), [])
  const selectedChain = state.chains.find((c) => c.chain_id === selectedNode?.chainId)
  const selectedResult = selectedChain ? results[selectedChain.chain_id] : null
  const canExecute = selectedChain && isRegisteredChainId(selectedChain.chain_id, state.scenarios)

  async function run(kind, fn) {
    if (!selectedChain) return
    setBusy(kind)
    try {
      const data = await fn()
      setResults((r) => ({ ...r, [selectedChain.chain_id]: { kind, data } }))
    } catch (e) {
      setResults((r) => ({ ...r, [selectedChain.chain_id]: { kind, error: apiError(e) } }))
    } finally {
      setBusy(null)
    }
  }
  const handleValidate = () => run('validate', () => validateChain(selectedChain.chain_id))
  const handleExecute = () => run('execute', () => executeChain(selectedChain.experiment_id, selectedChain.chain_id))

  const selectCls = 'bg-base-900 border border-base-700 rounded-md px-2 py-1.5 text-xs text-base-100'

  return (
    <>
      <TopBar
        title="Attack Chain Explorer"
        subtitle="Multi-step findings linked into candidate chains, with dependencies and execution results"
        actions={
          <button
            onClick={load}
            disabled={state.loading}
            className="border border-base-700 text-base-300 text-xs font-medium px-3 py-1.5 rounded-md hover:border-signal hover:text-signal transition-colors disabled:opacity-50"
          >
            {state.loading ? 'Refreshing…' : 'Refresh'}
          </button>
        }
      />

      <div className="flex-1 flex overflow-hidden">
        <div className="flex-1 min-w-0 flex flex-col">
          {!state.loading && !state.error && state.chains.length > 0 && (
            <div className="shrink-0 flex flex-wrap items-center gap-x-4 gap-y-2 px-4 py-2 border-b border-base-700">
              <label className="flex items-center gap-1.5 text-xs text-base-400">
                Experiment
                <select className={selectCls} value={expFilter} onChange={(e) => { setExpFilter(e.target.value); setChainFilter('all') }}>
                  <option value="all">All</option>
                  {experimentIds.map((id) => <option key={id} value={id}>{id}</option>)}
                </select>
              </label>
              <label className="flex items-center gap-1.5 text-xs text-base-400">
                Chain
                <select className={selectCls} value={chainFilter} onChange={(e) => setChainFilter(e.target.value)}>
                  <option value="all">All ({chainOptions.length})</option>
                  {chainOptions.map((c) => <option key={c.chain_id} value={c.chain_id}>{c.chain_id}</option>)}
                </select>
              </label>
              <GraphLegend />
            </div>
          )}

          <div className="flex-1 relative min-h-0">
            {state.loading && <LoadingState />}
            {state.error && <ErrorState message={state.error} onRetry={load} />}

            {!state.loading && !state.error && state.chains.length === 0 && (
              <div className="p-6">
                <EmptyState title="No chains formed yet" description="Run an experiment to start discovering attack chains." />
              </div>
            )}
            {!state.loading && !state.error && state.chains.length > 0 && visibleChains.length === 0 && (
              <div className="p-6"><EmptyState title="No chains match these filters" /></div>
            )}

            {!state.loading && !state.error && visibleChains.length > 0 && (
              <ChainGraph chains={graphInput} onNodeClick={onNodeClick} selectedId={selectedNode?.id} />
            )}
          </div>
        </div>

        {selectedNode && selectedChain && (
          <aside className="w-96 max-w-[45vw] border-l border-base-700 bg-base-900 p-5 overflow-y-auto scrollbar-thin">
            <div className="text-xs text-base-400 font-mono mb-1">{selectedChain.chain_id} · {selectedChain.experiment_id}</div>
            <h3 className="text-sm font-medium text-base-100 mb-1">{selectedNode.step}</h3>
            <div className="flex flex-wrap items-center gap-2 mb-3">
              {selectedNode.vulnerability && <Chip>{selectedNode.vulnerability.id}</Chip>}
              {selectedNode.finding && <SeverityBadge severity={selectedNode.finding.severity} />}
            </div>

            {selectedNode.finding ? (
              <dl className="space-y-3 text-xs">
                <div>
                  <dt className="text-base-400 mb-1">Finding</dt>
                  <dd className="text-base-200 font-mono">{selectedNode.finding.finding}</dd>
                </div>
                <div>
                  <dt className="text-base-400 mb-1">Confidence</dt>
                  <dd className="text-base-200 font-mono">{fmtPct(selectedNode.finding.confidence)}</dd>
                </div>
                <div>
                  <dt className="text-base-400 mb-1">Evidence</dt>
                  <dd><JsonBlock value={selectedNode.finding.evidence} /></dd>
                </div>
              </dl>
            ) : (
              <p className="text-xs text-base-400">No finding data is available for this step.</p>
            )}

            <div className="mt-5 pt-4 border-t border-base-700 space-y-2">
              <div className="text-xs text-base-400">Chain</div>
              <div className="text-xs font-mono text-base-200 break-words">{selectedChain.steps.join(' → ')}</div>
              <div className="flex flex-wrap gap-1.5">
                {selectedChain.p4_chain_id ? <Chip tone="good" title="Associated P4 definition">P4: {selectedChain.p4_chain_id}</Chip> : <Chip>no P4 association</Chip>}
                <Chip>{selectedChain.dependencies ? 'dependencies stored' : 'order only'}</Chip>
              </div>
            </div>

            <div className="mt-4 grid grid-cols-2 gap-2">
              <button
                onClick={handleValidate}
                disabled={!!busy}
                className="btn-primary font-medium text-sm px-3 py-2 rounded-md transition-colors disabled:opacity-50"
              >
                {busy === 'validate' ? 'Validating…' : 'Validate Chain'}
              </button>
              <button
                onClick={handleExecute}
                disabled={!!busy || !canExecute}
                title={canExecute ? 'Run the registered chain in the sandbox' : 'Only chains with a registered P4 id can be executed'}
                className="inline-flex items-center justify-center gap-1.5 border border-signal/50 text-signal font-medium text-sm px-3 py-2 rounded-md disabled:opacity-40"
              >
                <Play size={13} /> {busy === 'execute' ? 'Running…' : 'Execute'}
              </button>
            </div>
            {!canExecute && (
              <p className="text-[11px] text-base-500 mt-2">
                Execute is available only for chains whose id is in the P4 registry; adaptive runs create generated ids.
                Validate works for every chain.
              </p>
            )}

            {selectedResult?.error && (
              <div className="mt-4"><Notice tone="bad">{selectedResult.error}</Notice></div>
            )}
            {selectedResult?.data && (
              <div className="mt-4 border border-base-700 rounded-md p-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-base-300">
                    {selectedResult.kind === 'execute' ? 'Execution result' : 'Validation result'}
                  </span>
                  <StatusBadge status={selectedResult.data.status} />
                </div>
                <div className="text-xs text-base-400 mt-2">
                  {selectedResult.data.validated_steps}/{selectedResult.data.total_steps} steps valid
                  {' · '}rate {fmtPct(selectedResult.data.validation_rate)}
                  {selectedResult.data.all_findings_reproduced != null && (
                    <> · findings reproduced: {selectedResult.data.all_findings_reproduced ? 'yes' : 'no'}</>
                  )}
                </div>
                {selectedResult.data.execution_cost && (
                  <div className="text-[11px] text-base-500 mt-1 font-mono">
                    cost: {selectedResult.data.execution_cost.test_count} tests · {fmtSec(selectedResult.data.execution_cost.execution_time_seconds)}
                  </div>
                )}
                <StepResults result={selectedResult.data} />
              </div>
            )}

            <Link
              to={`/chain-mitigation?exp=${selectedChain.experiment_id}&chain=${selectedChain.chain_id}`}
              className="mt-5 inline-flex items-center gap-1.5 text-xs text-signal hover:underline"
            >
              <ShieldCheck size={13} /> Test a mitigation on this chain →
            </Link>
          </aside>
        )}
      </div>
    </>
  )
}
