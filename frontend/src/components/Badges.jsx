const SEVERITY_STYLES = {
  critical: 'bg-sev-critical/15 text-sev-critical border-sev-critical/30',
  high: 'bg-sev-high/15 text-sev-high border-sev-high/30',
  medium: 'bg-sev-medium/15 text-sev-medium border-sev-medium/30',
  low: 'bg-sev-low/15 text-sev-low border-sev-low/30',
}

export function SeverityBadge({ severity }) {
  const cls = SEVERITY_STYLES[severity] ?? 'bg-base-700 text-base-300 border-base-600'
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs border font-mono ${cls}`}>
      {severity}
    </span>
  )
}

const STATUS_STYLES = {
  running: 'bg-info/15 text-info border-info/30',
  completed: 'bg-sev-low/15 text-sev-low border-sev-low/30',
  created: 'bg-base-600/40 text-base-200 border-base-500',
  validated: 'bg-sev-low/15 text-sev-low border-sev-low/30',
  candidate: 'bg-signal/15 text-signal border-signal/30',
  invalid: 'bg-sev-critical/15 text-sev-critical border-sev-critical/30',
}

export function StatusBadge({ status }) {
  const cls = STATUS_STYLES[status] ?? 'bg-base-700 text-base-300 border-base-600'
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs border capitalize ${cls}`}>
      {status}
    </span>
  )
}

export function ModeBadge({ mode }) {
  const isAdaptive = mode === 'adaptive'
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs border capitalize ${
        isAdaptive ? 'bg-signal/15 text-signal border-signal/30' : 'bg-info/15 text-info border-info/30'
      }`}
    >
      {mode}
    </span>
  )
}
