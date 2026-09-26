import { Loader2, AlertTriangle, Inbox } from 'lucide-react'

export function LoadingState({ label = 'Loading…' }) {
  return (
    <div className="flex items-center gap-2 text-base-400 text-sm py-12 justify-center">
      <Loader2 size={16} className="animate-spin" />
      {label}
    </div>
  )
}

export function ErrorState({ message = 'Something went wrong.', onRetry }) {
  return (
    <div className="flex flex-col items-center gap-3 text-sm py-12">
      <AlertTriangle size={20} className="text-sev-high" />
      <p className="text-base-300">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="text-signal border border-signal/40 rounded px-3 py-1.5 text-xs hover:bg-signal/10"
        >
          Retry
        </button>
      )}
    </div>
  )
}

export function EmptyState({ title, description, action }) {
  return (
    <div className="flex flex-col items-center gap-2 text-center py-16 border border-dashed border-base-700 rounded-lg">
      <Inbox size={20} className="text-base-500" />
      <p className="text-sm text-base-200">{title}</p>
      {description && <p className="text-xs text-base-400 max-w-sm">{description}</p>}
      {action}
    </div>
  )
}
