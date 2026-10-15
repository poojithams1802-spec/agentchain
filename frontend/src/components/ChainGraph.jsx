import { useMemo } from 'react'
import ReactFlow, { Background, Controls, MarkerType } from 'reactflow'
import 'reactflow/dist/style.css'
import { buildChainGraph, NODE_H, NODE_W, prettify } from '../lib/phase3'
import { useTheme, chartColors } from '../lib/theme'

// Same severity palette as the Phase 1 Chain Explorer.
const SEV_COLOR = { critical: '#E5484D', high: '#E8734D', medium: '#E8A33D', low: '#5B9E6F' }
const OK = '#5B9E6F'
const BAD = '#E5484D'

const STATUS_TEXT = {
  reproduced: ['reproduced', OK],
  failed: ['validation failed', BAD],
  finding: ['finding recorded', null],
  unknown: ['not validated', null],
}

function NodeLabel({ n, cc }) {
  const [text, color] = STATUS_TEXT[n.status]
  return (
    <div style={{ textAlign: 'left', lineHeight: 1.35 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 6 }}>
        <span style={{ fontWeight: 600, wordBreak: 'break-all' }}>{n.step}</span>
        {n.vulnerability && <span style={{ color: cc.axis }}>{n.vulnerability.id}</span>}
      </div>
      <div style={{ color: cc.axis, fontSize: 11, marginTop: 2 }}>
        {n.finding ? prettify(n.finding.finding) : 'no finding stored'}
      </div>
      <div style={{ fontSize: 11, marginTop: 4, color: color ?? cc.axis }}>● {text}</div>
    </div>
  )
}

/**
 * chains: [{ chain, findings, validationSteps }]
 * Dependency edges are drawn solid; plain execution order (no dependency data) dashed.
 * Edges whose dependency check failed during validation turn red.
 */
export default function ChainGraph({ chains, onNodeClick, selectedId, height = '100%' }) {
  const { dark } = useTheme()
  const cc = chartColors(dark)

  const { nodes, edges } = useMemo(() => {
    let offsetY = 0
    const all = { nodes: [], edges: [] }
    chains.forEach(({ chain, findings, validationSteps }) => {
      const g = buildChainGraph(chain, { findings, validationSteps, offsetY })
      offsetY += g.height + 40
      g.nodes.forEach((n) => {
        const border =
          n.status === 'reproduced' ? OK : n.status === 'failed' ? BAD : n.finding ? SEV_COLOR[n.finding.severity] ?? cc.nodeBorder : cc.nodeBorder
        all.nodes.push({
          id: n.id,
          position: { x: n.x, y: n.y },
          data: { ...n, label: <NodeLabel n={n} cc={cc} /> },
          style: {
            background: cc.nodeBg,
            color: cc.nodeText,
            border: `${selectedId === n.id ? 2.5 : 1.5}px solid ${border}`,
            borderRadius: 10,
            fontFamily: 'IBM Plex Mono, monospace',
            fontSize: 12,
            padding: 10,
            width: NODE_W,
            minHeight: NODE_H - 20,
          },
        })
      })
      g.edges.forEach((e) => {
        const stroke = e.satisfied === false ? BAD : e.satisfied === true ? OK : cc.edge
        all.edges.push({
          id: e.id,
          source: e.source,
          target: e.target,
          animated: e.kind === 'dependency' && e.satisfied !== false,
          label: e.kind === 'order' ? 'order' : e.satisfied === false ? 'dependency unmet' : 'depends on',
          labelStyle: { fontSize: 10, fill: cc.axis },
          labelBgStyle: { fill: cc.nodeBg },
          style: { stroke, strokeDasharray: e.kind === 'order' ? '5 4' : undefined, strokeWidth: 1.6 },
          markerEnd: { type: MarkerType.ArrowClosed, color: stroke },
        })
      })
    })
    return all
  }, [chains, dark, selectedId])

  return (
    <div style={{ height }} className="w-full">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodeClick={(_, node) => onNodeClick?.(node.data)}
        nodesDraggable={false}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        proOptions={{ hideAttribution: true }}
      >
        <Background color={cc.dots} gap={20} />
        <Controls showInteractive={false} />
      </ReactFlow>
    </div>
  )
}

export function GraphLegend() {
  const Item = ({ color, dashed, label }) => (
    <span className="inline-flex items-center gap-1.5">
      <span style={{ width: 18, borderTop: `2px ${dashed ? 'dashed' : 'solid'} ${color}` }} />
      {label}
    </span>
  )
  return (
    <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-[11px] text-base-400">
      <Item color="rgb(var(--base-400))" label="dependency (from stored P4 association)" />
      <Item color="rgb(var(--base-400))" dashed label="execution order only (no dependency data)" />
      <Item color={OK} label="dependency satisfied" />
      <Item color={BAD} label="dependency unmet" />
    </div>
  )
}
