import { useMemo, useState } from 'react'
import { Search, Check, ArrowRight } from 'lucide-react'
import { VULNERABILITIES, prettify } from '../lib/phase3'
import { Chip } from './Phase3Parts'

export function ScenarioPicker({ scenarios, value, onChange, loading, error }) {
  if (loading) return <p className="text-xs text-base-400">Loading registered scenarios…</p>
  if (error) return <p className="text-xs text-sev-medium">Could not load scenarios ({error}). The default 3-test chain will be used.</p>
  if (!scenarios?.length) return <p className="text-xs text-base-400">No scenarios registered.</p>

  return (
    <div className="grid sm:grid-cols-2 gap-2">
      <button
        type="button"
        onClick={() => onChange(null)}
        aria-pressed={!value}
        className={`text-left rounded-md border px-3 py-2.5 text-sm transition-colors ${
          !value ? 'border-signal bg-signal/10 text-signal' : 'border-base-700 text-base-300 hover:border-base-500'
        }`}
      >
        <div className="font-medium">Default chain</div>
        <div className="text-xs text-base-400 mt-0.5">permission → tool access → memory (legacy Phase 1/2 behaviour)</div>
      </button>

      {scenarios.map((s) => {
        const active = value === s.scenario_id
        return (
          <button
            type="button"
            key={s.scenario_id}
            onClick={() => onChange(s)}
            aria-pressed={active}
            className={`text-left rounded-md border px-3 py-2.5 text-sm transition-colors ${
              active ? 'border-signal bg-signal/10' : 'border-base-700 hover:border-base-500'
            }`}
          >
            <div className="flex items-center justify-between gap-2">
              <span className={`font-medium ${active ? 'text-signal' : 'text-base-100'}`}>{s.scenario_name}</span>
              {active && <Check size={14} className="text-signal shrink-0" />}
            </div>
            <div className="font-mono text-[11px] text-base-400 mt-0.5">{s.scenario_id}</div>
            <div className="flex flex-wrap items-center gap-1 mt-2">
              {s.steps.map((st, i) => (
                <span key={st} className="inline-flex items-center gap-1 text-[10px] font-mono text-base-300">
                  {i > 0 && <ArrowRight size={10} className="text-base-500" />}
                  <span className="px-1.5 py-0.5 rounded bg-base-800 border border-base-700">{st.replace(/_test$/, '')}</span>
                </span>
              ))}
            </div>
            {s.description && <div className="text-[11px] text-base-400 mt-2 leading-snug">{s.description}</div>}
          </button>
        )
      })}
    </div>
  )
}

// Order matters: the backend runs the tests in the order requested.
export function VulnerabilityPicker({ value, onChange, disabled }) {
  const [q, setQ] = useState('')
  const shown = useMemo(() => {
    const needle = q.trim().toLowerCase()
    return VULNERABILITIES.filter(
      (v) => !needle || [v.id, v.test, v.finding].some((x) => x.toLowerCase().includes(needle)),
    )
  }, [q])

  const toggle = (id) => onChange(value.includes(id) ? value.filter((x) => x !== id) : [...value, id])

  return (
    <div className={disabled ? 'opacity-50 pointer-events-none' : ''} aria-disabled={disabled}>
      <div className="relative mb-2">
        <Search size={13} className="absolute left-2.5 top-2.5 text-base-500" />
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Search V1–V12, test or finding…"
          aria-label="Search vulnerabilities"
          className="w-full bg-base-900 border border-base-700 rounded-md pl-8 pr-3 py-2 text-sm text-base-100 placeholder:text-base-500 focus:border-signal outline-none"
        />
      </div>
      <div className="grid sm:grid-cols-2 gap-1.5 max-h-60 overflow-y-auto scrollbar-thin pr-1">
        {shown.map((v) => {
          const idx = value.indexOf(v.id)
          const on = idx >= 0
          return (
            <button
              type="button"
              key={v.id}
              onClick={() => toggle(v.id)}
              aria-pressed={on}
              className={`flex items-center gap-2 text-left rounded-md border px-2.5 py-1.5 text-xs transition-colors ${
                on ? 'border-signal bg-signal/10 text-signal' : 'border-base-700 text-base-300 hover:border-base-500'
              }`}
            >
              <span className={`h-5 w-5 shrink-0 rounded-full grid place-items-center text-[10px] font-mono border ${on ? 'border-signal' : 'border-base-600'}`}>
                {on ? idx + 1 : ''}
              </span>
              <span className="min-w-0">
                <span className="font-mono">{v.id}</span> · {prettify(v.finding)}
                <span className="block font-mono text-[10px] text-base-500 truncate">{v.test}</span>
              </span>
            </button>
          )
        })}
        {shown.length === 0 && <p className="text-xs text-base-400 col-span-2 py-2">No vulnerability matches “{q}”.</p>}
      </div>
      {value.length > 0 && (
        <div className="flex flex-wrap items-center gap-1.5 mt-2">
          <span className="text-[11px] text-base-400">Run order:</span>
          {value.map((id) => (
            <Chip key={id}>{id}</Chip>
          ))}
          <button type="button" onClick={() => onChange([])} className="text-[11px] text-signal hover:underline ml-1">
            clear
          </button>
        </div>
      )}
    </div>
  )
}
