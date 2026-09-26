import { useEffect, useMemo, useState, useCallback } from 'react'
import ReactFlow, { Background, Controls, MarkerType } from 'reactflow'
import 'reactflow/dist/style.css'
import TopBar from '../components/TopBar'
import { SeverityBadge, StatusBadge } from '../components/Badges'
import { LoadingState, ErrorState, EmptyState } from '../components/States'
import { getAllChains, getAllFindings } from '../api/client'

const SEV_COLOR = { critical: '#E5484D', high: '#E8734D', medium: '#E8A33D', low: '#5B9E6F' }

function buildGraph(chains, findings) {
  const findingMap = Object.fromEntries(findings.map((f) => [f.finding_id, f]))
  const nodes = []
  const edges = []
  let x = 0

  chains.forEach((chain) => {
    let y = 0
    chain.steps.forEach((stepId, idx) => {
      const finding = findingMap[stepId]
      const nodeId = `${chain.chain_id}-${stepId}`
      nodes.push({
        id: nodeId,
        position: { x, y: y * 110 },
        data: { label: stepId, finding, chainId: chain.chain_id },
        type: 'default',
        style: {
          background: '#14171C',
          border: `1.5px solid ${finding ? SEV_COLOR[finding.severity] : '#3A4048'}`,
          borderRadius: 8,
          color: '#E4E6EA',
          fontFamily: 'IBM Plex Mono, monospace',
          fontSize: 12,
          padding: 8,
          width: 190,
        },
      })
      if (idx > 0) {
        const prevId = `${chain.chain_id}-${chain.steps[idx - 1]}`
        edges.push({
          id: `${prevId}-${nodeId}`,
          source: prevId,
          target: nodeId,
          animated: chain.status === 'candidate',
          style: { stroke: chain.status === 'validated' ? '#5B9E6F' : '#5C636D' },
          markerEnd: { type: MarkerType.ArrowClosed, color: chain.status === 'validated' ? '#5B9E6F' : '#5C636D' },
        })
      }
      y += 1
    })
    x += 260
  })

  return { nodes, edges }
}

export default function ChainExplorer() {
  const [state, setState] = useState({ loading: true, error: null, chains: [], findings: [] })
  const [selectedNode, setSelectedNode] = useState(null)

  async function load() {
    setState({ loading: true, error: null, chains: [], findings: [] })
    try {
      const [chains, findings] = await Promise.all([getAllChains(), getAllFindings()])
      setState({ loading: false, error: null, chains, findings })
    } catch (e) {
      setState((s) => ({ ...s, loading: false, error: e.message }))
    }
  }

  useEffect(() => {
    load()
  }, [])

  const { nodes, edges } = useMemo(
    () => buildGraph(state.chains, state.findings),
    [state.chains, state.findings],
  )

  const onNodeClick = useCallback((_, node) => setSelectedNode(node.data), [])

  return (
    <>
      <TopBar title="Attack Chain Explorer" subtitle="Multi-step findings linked into candidate and validated chains" />
      <div className="flex-1 flex overflow-hidden">
        <div className="flex-1 relative">
          {state.loading && <LoadingState />}
          {state.error && <ErrorState message={state.error} onRetry={load} />}
          {!state.loading && !state.error && nodes.length === 0 && (
            <div className="p-6">
              <EmptyState title="No chains formed yet" description="Run an experiment to start discovering attack chains." />
            </div>
          )}
          {!state.loading && !state.error && nodes.length > 0 && (
            <ReactFlow
              nodes={nodes}
              edges={edges}
              onNodeClick={onNodeClick}
              fitView
              proOptions={{ hideAttribution: true }}
            >
              <Background color="#1B1F26" gap={20} />
              <Controls />
            </ReactFlow>
          )}
        </div>
        {selectedNode?.finding && (
          <aside className="w-80 border-l border-base-700 bg-base-900 p-5 overflow-y-auto scrollbar-thin">
            <div className="text-xs text-base-400 font-mono mb-1">{selectedNode.chainId}</div>
            <h3 className="text-sm font-medium text-base-100 mb-3">
              {selectedNode.finding.type.replaceAll('_', ' ')}
            </h3>
            <div className="flex items-center gap-2 mb-3">
              <SeverityBadge severity={selectedNode.finding.severity} />
              {selectedNode.finding.validated && <StatusBadge status="validated" />}
            </div>
            <dl className="space-y-3 text-xs">
              <div>
                <dt className="text-base-400 mb-1">Confidence</dt>
                <dd className="text-base-200 font-mono">{(selectedNode.finding.confidence * 100).toFixed(0)}%</dd>
              </div>
              <div>
                <dt className="text-base-400 mb-1">Test</dt>
                <dd className="text-base-200 font-mono">{selectedNode.finding.test}</dd>
              </div>
              <div>
                <dt className="text-base-400 mb-1">Evidence</dt>
                <dd className="text-base-200 leading-relaxed">{selectedNode.finding.evidence}</dd>
              </div>
            </dl>
          </aside>
        )}
      </div>
    </>
  )
}
