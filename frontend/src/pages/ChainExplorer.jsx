import {
  useEffect,
  useMemo,
  useState,
  useCallback,
} from 'react'
import ReactFlow, {
  Background,
  Controls,
  MarkerType,
} from 'reactflow'
import 'reactflow/dist/style.css'

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
  getExperimentChains,
  validateChain,
} from '../api/client'
import { useTheme, chartColors } from '../lib/theme'

const SEV_COLOR = {
  critical: '#E5484D',
  high: '#E8734D',
  medium: '#E8A33D',
  low: '#5B9E6F',
}

function buildGraph(chains, findings, cc) {
  const findingMap = Object.fromEntries(
    findings.map((f) => [f.test, f]),
  )

  const nodes = []
  const edges = []

  let x = 0

  chains.forEach((chain) => {
    chain.steps.forEach((step, idx) => {
      const finding = findingMap[step]

      const nodeId = `${chain.chain_id}-${step}`

      nodes.push({
        id: nodeId,
        position: {
          x,
          y: idx * 130,
        },

        data: {
          label: step,
          finding,
          chainId: chain.chain_id,
        },

        type: 'default',

        style: {
          background: cc.nodeBg,
          border: `1.5px solid ${finding
              ? SEV_COLOR[finding.severity]
              : cc.nodeBorder
            }`,
          borderRadius: 8,
          color: cc.nodeText,
          fontFamily: 'IBM Plex Mono, monospace',
          fontSize: 12,
          padding: 8,
          width: 190,
        },
      })

      if (idx > 0) {
        const previousStep =
          chain.steps[idx - 1]

        const previousId =
          `${chain.chain_id}-${previousStep}`

        edges.push({
          id: `${previousId}-${nodeId}`,
          source: previousId,
          target: nodeId,
          animated: true,
          style: {
            stroke: cc.edge,
          },
          markerEnd: {
            type: MarkerType.ArrowClosed,
            color: cc.edge,
          },
        })
      }
    })

    x += 260
  })

  return {
    nodes,
    edges,
  }
}

export default function ChainExplorer() {
  const { dark } = useTheme()
  const cc = chartColors(dark)
  const [state, setState] = useState({
    loading: true,
    error: null,
    chains: [],
    findings: [],
  })

  const [selectedNode, setSelectedNode] =
    useState(null)

  const [validating, setValidating] =
    useState(false)

  const [validationResult, setValidationResult] =
    useState(null)

  async function load() {
    setState({
      loading: true,
      error: null,
      chains: [],
      findings: [],
    })

    try {
      const experiments =
        await listExperiments()

      const results = await Promise.all(
        experiments.map(async (exp) => {
          const [findings, chains] =
            await Promise.all([
              getExperimentFindings(
                exp.experiment_id,
              ),
              getExperimentChains(
                exp.experiment_id,
              ),
            ])

          return {
            findings,
            chains,
          }
        }),
      )

      setState({
        loading: false,
        error: null,
        chains: results.flatMap(
          (r) => r.chains,
        ),
        findings: results.flatMap(
          (r) => r.findings,
        ),
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

  const { nodes, edges } = useMemo(
    () =>
      buildGraph(
        state.chains,
        state.findings,
        cc,
      ),
    [state.chains, state.findings, dark],
  )

  const onNodeClick = useCallback(
    (_, node) =>
      setSelectedNode(node.data),
    [],
  )

  async function handleValidate(chainId) {
    setValidating(true)
    setValidationResult(null)

    try {
      const result =
        await validateChain(chainId)

      setValidationResult(result)
    } catch (e) {
      setValidationResult({
        error: e.message,
      })
    } finally {
      setValidating(false)
    }
  }

  return (
    <>
      <TopBar
        title="Attack Chain Explorer"
        subtitle="Multi-step findings linked into candidate chains"
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
        <div className="flex-1 relative">
          {state.loading && (
            <LoadingState />
          )}

          {state.error && (
            <ErrorState
              message={state.error}
              onRetry={load}
            />
          )}

          {!state.loading &&
            !state.error &&
            nodes.length === 0 && (
              <div className="p-6">
                <EmptyState
                  title="No chains formed yet"
                  description="Run an experiment to start discovering attack chains."
                />
              </div>
            )}

          {!state.loading &&
            !state.error &&
            nodes.length > 0 && (
              <ReactFlow
                nodes={nodes}
                edges={edges}
                onNodeClick={onNodeClick}
                fitView
                proOptions={{
                  hideAttribution: true,
                }}
              >
                <Background
                  color={cc.dots}
                  gap={20}
                />
                <Controls />
              </ReactFlow>
            )}
        </div>

        {selectedNode && (
          <aside className="w-80 border-l border-base-700 bg-base-900 p-5 overflow-y-auto scrollbar-thin">
            <div className="text-xs text-base-400 font-mono mb-1">
              {selectedNode.chainId}
            </div>

            <h3 className="text-sm font-medium text-base-100 mb-3">
              {selectedNode.label}
            </h3>

            {selectedNode.finding ? (
              <>
                <div className="flex items-center gap-2 mb-3">
                  <SeverityBadge
                    severity={
                      selectedNode.finding.severity
                    }
                  />
                </div>

                <dl className="space-y-3 text-xs">
                  <div>
                    <dt className="text-base-400 mb-1">
                      Finding
                    </dt>

                    <dd className="text-base-200 font-mono">
                      {selectedNode.finding.finding}
                    </dd>
                  </div>

                  <div>
                    <dt className="text-base-400 mb-1">
                      Confidence
                    </dt>

                    <dd className="text-base-200 font-mono">
                      {typeof selectedNode.finding
                        .confidence === 'number'
                        ? `${Math.round(
                          selectedNode.finding.confidence *
                          100,
                        )}%`
                        : '—'}
                    </dd>
                  </div>

                  <div>
                    <dt className="text-base-400 mb-1">
                      Evidence
                    </dt>

                    <dd className="text-base-200 leading-relaxed">
                      <pre className="whitespace-pre-wrap font-mono text-xs">
                        {JSON.stringify(
                          selectedNode.finding
                            .evidence,
                          null,
                          2,
                        )}
                      </pre>
                    </dd>
                  </div>
                </dl>
              </>
            ) : (
              <p className="text-xs text-base-400">
                No finding data is available for
                this step.
              </p>
            )}

            <button
              onClick={() =>
                handleValidate(
                  selectedNode.chainId,
                )
              }
              disabled={validating}
              className="mt-5 w-full btn-primary font-medium text-sm px-3 py-2 rounded-md  transition-colors disabled:opacity-50"
            >
              {validating
                ? 'Validating…'
                : 'Validate Chain'}
            </button>

            {validationResult && (
              <div className="mt-4 border border-base-700 rounded-md p-3">
                {validationResult.error ? (
                  <p className="text-xs text-sev-critical">
                    {validationResult.error}
                  </p>
                ) : (
                  <>
                    <div className="text-xs text-base-300">
                      Validation status
                    </div>

                    <div className="text-sm text-base-100 font-medium mt-1">
                      {validationResult.status}
                    </div>

                    <div className="text-xs text-base-400 mt-2">
                      {validationResult.validated_steps}
                      /
                      {validationResult.total_steps}
                      {' '}steps valid
                    </div>
                  </>
                )}
              </div>
            )}
          </aside>
        )}
      </div>
    </>
  )
}