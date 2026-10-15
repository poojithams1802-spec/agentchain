import { useMemo } from 'react'
import { AlertTriangle, Info, Bot, Brain, BookOpen, Cpu, Clock, FlaskConical } from 'lucide-react'
import { SeverityBadge } from './Badges'
import { fmtSec, fmtPct, prettify, vulnByTest } from '../lib/phase3'

// ---------------------------------------------------------------- generic
export function Panel({ title, subtitle, actions, children, className = '' }) {
  return (
    <section className={`bg-base-900 border border-base-700 rounded-lg p-4 ${className}`}>
      {(title || actions) && (
        <div className="flex items-start justify-between gap-3 mb-3">
          <div className="min-w-0">
            {title && <h2 className="text-sm font-semibold text-base-100">{title}</h2>}
            {subtitle && <p className="text-xs text-base-400 mt-0.5">{subtitle}</p>}
          </div>
          {actions && <div className="shrink-0 flex items-center gap-2">{actions}</div>}
        </div>
      )}
      {children}
    </section>
  )
}

const TONES = {
  warn: 'text-sev-medium border-sev-medium/30 bg-sev-medium/10',
  info: 'text-info border-info/30 bg-info/10',
  bad: 'text-sev-critical border-sev-critical/30 bg-sev-critical/10',
  good: 'text-sev-low border-sev-low/30 bg-sev-low/10',
}

export function Notice({ tone = 'info', title, children }) {
  const Icon = tone === 'info' ? Info : AlertTriangle
  return (
    <div className={`flex items-start gap-2 text-xs border rounded-lg px-3 py-2 ${TONES[tone]}`}>
      <Icon size={14} className="mt-0.5 shrink-0" />
      <div className="min-w-0">
        {title && <div className="font-semibold">{title}</div>}
        <div className="opacity-90">{children}</div>
      </div>
    </div>
  )
}

export function Chip({ children, tone, title }) {
  const cls = tone ? TONES[tone] : 'border-base-600 text-base-300 bg-base-800'
  return (
    <span title={title} className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] border font-mono ${cls}`}>
      {children}
    </span>
  )
}

export function JsonBlock({ value, max = 'max-h-48' }) {
  if (value == null) return <span className="text-base-400 text-xs">—</span>
  const text = typeof value === 'string' ? value : JSON.stringify(value, null, 2)
  return (
    <pre className={`text-[11px] font-mono text-base-300 bg-base-800 rounded p-2 overflow-auto whitespace-pre-wrap break-words scrollbar-thin ${max}`}>
      {text}
    </pre>
  )
}

// ---------------------------------------------------------------- budget
// `cap` is only drawn when the API actually tells us the limit.
export function BudgetMeters({ meters }) {
  if (!meters?.length) return null
  return (
    <div className="grid sm:grid-cols-3 gap-3">
      {meters.map((m) => {
        const Icon = m.key === 'tests' ? FlaskConical : m.key === 'llm' ? Brain : Clock
        const hasCap = typeof m.cap === 'number' && m.cap > 0
        const ratio = hasCap ? Math.min(1, (m.used ?? 0) / m.cap) : null
        const full = ratio === 1
        const shown = m.key === 'time' ? fmtSec(m.used) : (m.used ?? '—')
        return (
          <div key={m.key} className="border border-base-700 rounded-lg p-3 bg-base-800/50">
            <div className="flex items-center gap-1.5 text-xs text-base-400">
              <Icon size={13} /> {m.label}
            </div>
            <div className="mt-1 font-mono text-xl text-base-100">
              {shown}
              {hasCap && <span className="text-sm text-base-400"> / {m.cap}</span>}
            </div>
            {hasCap ? (
              <div className="mt-2 h-1.5 rounded-full bg-base-700 overflow-hidden" role="progressbar" aria-valuenow={m.used} aria-valuemax={m.cap}>
                <div className={`h-full ${full ? 'bg-sev-high' : 'bg-signal'}`} style={{ width: `${ratio * 100}%` }} />
              </div>
            ) : (
              <div className="mt-2 text-[11px] text-base-500">limit set server-side · not exposed by API</div>
            )}
          </div>
        )
      })}
    </div>
  )
}

// ---------------------------------------------------------------- decision timeline
const SOURCE = {
  deterministic_fallback: { label: 'deterministic fallback', tone: 'warn', Icon: Cpu },
  gemini: { label: 'LLM (gemini)', tone: 'good', Icon: Brain },
}

function ragChip(rag) {
  if (rag.used === true) return <Chip tone="good" title="RAG context was used in the decision">RAG used</Chip>
  if (rag.retrieved === true) return <Chip title="Context was retrieved but not used">RAG retrieved</Chip>
  if (rag.status && rag.status !== 'unknown') return <Chip title="RAG retrieval status">RAG: {rag.status}</Chip>
  return null
}

export function DecisionTimeline({ events }) {
  if (!events?.length) return null
  return (
    <ol className="relative space-y-4 pl-8 before:absolute before:left-[13px] before:top-2 before:bottom-2 before:w-px before:bg-base-600">
      {events.map((e) => {
        const src = SOURCE[e.source] ?? { label: e.source === 'unknown' ? 'source not reported' : e.source, tone: undefined, Icon: Bot }
        const vuln = vulnByTest[e.test]
        return (
          <li key={e.index} className="relative">
            <span className="absolute -left-8 top-1 h-7 w-7 rounded-full grid place-items-center text-xs font-mono border bg-base-900 border-signal text-signal">
              {e.index}
            </span>
            <div className="bg-base-900 border border-base-700 rounded-lg p-3 space-y-2">
              <div className="flex flex-wrap items-center gap-2">
                <span className="font-mono text-sm text-base-100">{e.test}</span>
                {vuln && <Chip title={vuln.finding}>{vuln.id}</Chip>}
                <Chip tone={src.tone}>
                  <src.Icon size={11} /> {src.label}
                </Chip>
                {ragChip(e.rag)}
                {e.priority != null && <Chip>priority {e.priority.toFixed(2)}</Chip>}
                {e.confidence != null && <Chip>confidence {e.confidence.toFixed(2)}</Chip>}
              </div>

              {e.reason && (
                <p className="text-xs text-base-300 flex gap-1.5">
                  <BookOpen size={12} className="mt-0.5 shrink-0 text-base-500" />
                  <span>{e.reason}</span>
                </p>
              )}
              {e.fallbackReason && (
                <p className="text-[11px] text-sev-medium font-mono break-words">
                  fallback reason: {String(e.fallbackReason).slice(0, 220)}
                  {e.recovery ? ` · recovery: ${e.recovery}` : ''}
                </p>
              )}

              {e.executed ? (
                <div className="border-t border-base-700 pt-2 text-xs space-y-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-base-400">sandbox:</span>
                    <span className="font-mono text-base-200">{e.result.status}</span>
                    {e.result.finding && <span className="font-mono text-base-100">{prettify(e.result.finding)}</span>}
                    {e.result.severity && <SeverityBadge severity={e.result.severity} />}
                    {e.result.confidence != null && <span className="text-base-400">confidence {fmtPct(e.result.confidence)}</span>}
                  </div>
                  {e.result.evidence != null && (
                    <details className="text-base-400">
                      <summary className="cursor-pointer text-[11px]">evidence</summary>
                      <JsonBlock value={e.result.evidence} max="max-h-32" />
                    </details>
                  )}
                </div>
              ) : (
                <Notice tone="warn">Planned but not executed: the run stopped before this test reached the sandbox.</Notice>
              )}
            </div>
          </li>
        )
      })}
    </ol>
  )
}

// ---------------------------------------------------------------- multi-agent graph
const V = (name) => `rgb(var(--${name}))`
const EDGE_STYLE = {
  delivered: { color: V('sev-critical'), dash: undefined, label: 'delivered' },
  denied: { color: V('sev-low'), dash: '6 4', label: 'denied' },
  allowed: { color: V('base-400'), dash: '3 4', label: 'allowed by config' },
}

export function AgentGraph({ agents, edges }) {
  const W = 220
  const H = 118
  const gap = 150
  const ordered = useMemo(() => [...agents].sort((a, b) => (a.trust_level ?? 0) - (b.trust_level ?? 0)), [agents])
  const pos = Object.fromEntries(ordered.map((a, i) => [a.agent_id, { x: 40 + i * (W + gap), y: 90 }]))
  const width = 80 + ordered.length * W + Math.max(0, ordered.length - 1) * gap
  const height = 330

  return (
    <div className="overflow-x-auto scrollbar-thin">
      <svg viewBox={`0 0 ${width} ${height}`} style={{ minWidth: Math.min(width, 640), width: '100%', maxHeight: 360 }} role="img" aria-label="Agent interaction graph">
        <defs>
          {Object.entries(EDGE_STYLE).map(([k, s]) => (
            <marker key={k} id={`ah-${k}`} viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
              <path d="M0 0 L10 5 L0 10 z" fill={s.color} />
            </marker>
          ))}
        </defs>

        {edges.map((e, i) => {
          const a = pos[e.from]
          const b = pos[e.to]
          if (!a || !b) return null
          const s = EDGE_STYLE[e.kind] ?? EDGE_STYLE.allowed
          const forward = a.x <= b.x
          const x1 = a.x + (forward ? W : 0)
          const x2 = b.x + (forward ? 0 : W)
          const mid = (x1 + x2) / 2
          const lift = forward ? -70 : 70
          const y = a.y + H / 2
          const path = `M ${x1} ${y} Q ${mid} ${y + lift * 1.6} ${x2} ${y}`
          const ly = y + lift * 0.8 + (forward ? -8 : 16)
          return (
            <g key={`${e.from}-${e.to}-${i}`}>
              <path d={path} fill="none" stroke={s.color} strokeWidth="2" strokeDasharray={s.dash} markerEnd={`url(#ah-${e.kind in EDGE_STYLE ? e.kind : 'allowed'})`} />
              <text x={mid} y={ly} textAnchor="middle" fontSize="11" fill={s.color} fontFamily="IBM Plex Mono, monospace">
                {s.label}
              </text>
              {e.crossesTrustBoundary && (
                <text x={mid} y={ly + 14} textAnchor="middle" fontSize="10" fill={V('sev-high')} fontFamily="IBM Plex Mono, monospace">
                  crosses trust boundary
                </text>
              )}
            </g>
          )
        })}

        {ordered.map((a) => {
          const p = pos[a.agent_id]
          const trust = typeof a.trust_level === 'number' ? a.trust_level : null
          return (
            <g key={a.agent_id} transform={`translate(${p.x} ${p.y})`}>
              <rect width={W} height={H} rx="12" fill={V('base-900')} stroke={V('base-600')} strokeWidth="1.5" />
              <text x="14" y="24" fontSize="12" fontWeight="600" fill={V('base-100')} fontFamily="IBM Plex Mono, monospace">
                {a.agent_id.length > 24 ? `${a.agent_id.slice(0, 23)}…` : a.agent_id}
              </text>
              <text x="14" y="42" fontSize="11" fill={V('base-400')}>{a.role ?? 'role n/a'}</text>
              <text x="14" y="62" fontSize="10" fill={V('base-400')}>trust {trust != null ? trust.toFixed(2) : 'n/a'}</text>
              <rect x="14" y="68" width={W - 28} height="6" rx="3" fill={V('base-700')} />
              {trust != null && (
                <rect x="14" y="68" width={(W - 28) * trust} height="6" rx="3" fill={trust < 0.4 ? V('sev-high') : V('sev-low')} />
              )}
              <text x="14" y="94" fontSize="10" fill={V('base-300')} fontFamily="IBM Plex Mono, monospace">
                tools: {(a.tools ?? []).join(', ') || '—'}
              </text>
              <text x="14" y="109" fontSize="10" fill={V('base-300')} fontFamily="IBM Plex Mono, monospace">
                perms: {(a.permissions ?? []).join(', ') || '—'}
              </text>
            </g>
          )
        })}
      </svg>
    </div>
  )
}
