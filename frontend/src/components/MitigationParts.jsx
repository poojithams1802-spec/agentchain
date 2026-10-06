import { Check, X, Minus, ShieldCheck, ShieldX } from 'lucide-react'
import { controlLabel } from '../lib/mitigation'

export function ControlBadge({ control }) {
  return (
    <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-xs border font-mono bg-signal/10 text-signal border-signal/30">
      <ShieldCheck size={12} />
      {controlLabel(control)}
    </span>
  )
}

export function Stepper({ steps, current }) {
  return (
    <ol className="flex items-center gap-2 text-xs overflow-x-auto scrollbar-thin pb-1">
      {steps.map((label, i) => {
        const done = i < current
        const active = i === current
        return (
          <li key={label} className="flex items-center gap-2 shrink-0">
            <span
              className={`h-6 w-6 rounded-full grid place-items-center border font-mono ${
                done
                  ? 'bg-sev-low/20 border-sev-low/40 text-sev-low'
                  : active
                    ? 'bg-signal/15 border-signal text-signal'
                    : 'border-base-600 text-base-400'
              }`}
            >
              {done ? <Check size={12} /> : i + 1}
            </span>
            <span className={active ? 'text-base-100' : done ? 'text-base-300' : 'text-base-400'}>{label}</span>
            {i < steps.length - 1 && <span className="w-6 h-px bg-base-600" />}
          </li>
        )
      })}
    </ol>
  )
}

function Evidence({ value }) {
  if (value == null) return <span className="text-base-400">—</span>
  if (typeof value !== 'object') return <span>{String(value)}</span>
  return (
    <dl className="space-y-1">
      {Object.entries(value).map(([k, v]) => (
        <div key={k} className="flex gap-2">
          <dt className="text-base-400 shrink-0">{k}:</dt>
          <dd className="break-words">{typeof v === 'object' ? JSON.stringify(v) : String(v)}</dd>
        </div>
      ))}
    </dl>
  )
}

function ResultCard({ title, tone, result }) {
  const border = tone === 'bad' ? 'border-sev-critical/40' : 'border-sev-low/40'
  return (
    <div className={`bg-base-900 border ${border} rounded-lg p-4`}>
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold">{title}</h3>
        <span className={`text-xs font-mono ${tone === 'bad' ? 'text-sev-critical' : 'text-sev-low'}`}>
          {tone === 'bad' ? 'ATTACK SUCCEEDS' : 'ATTACK BLOCKED'}
        </span>
      </div>
      <div className="text-xs font-mono space-y-2">
        <div><span className="text-base-400">status: </span>{result?.status ?? '—'}</div>
        <div>
          <span className="text-base-400">finding: </span>
          {tone === 'good' ? `${result?.finding ?? 'none'} (attack blocked by ${result?.mitigation_control ?? 'control'})` : (result?.finding ?? 'none (no vulnerability observed)')}
        </div>
        <div className="text-base-200 bg-base-800 rounded p-2"><Evidence value={result?.evidence} /></div>
      </div>
    </div>
  )
}

export function BeforeAfter({ replay }) {
  const blocked = replay.blocked_after_mitigation === true
  return (
    <div className="grid md:grid-cols-2 gap-4">
      <ResultCard title={`Before · ${replay.test}`} tone="bad" result={replay.before_result} />
      <ResultCard title={`After · ${replay.test}`} tone={blocked ? 'good' : 'bad'} result={replay.after_result} />
    </div>
  )
}

const NODE = {
  vulnerable: { cls: 'border-sev-critical/60 text-sev-critical bg-sev-critical/10', icon: X, text: 'vulnerable' },
  blocked: { cls: 'border-sev-low/60 text-sev-low bg-sev-low/10', icon: Check, text: 'blocked' },
  not_replayed: { cls: 'border-base-500 text-base-300 bg-base-800', icon: Minus, text: 'not replayed' },
}

function Row({ title, steps, state, brokenFrom }) {
  return (
    <div>
      <div className="text-xs text-base-400 mb-2">{title}</div>
      <div className="flex items-center overflow-x-auto scrollbar-thin pb-1">
        {steps.map((s, i) => {
          const n = NODE[state(s)]
          const Icon = n.icon
          const broken = brokenFrom != null && i >= brokenFrom
          return (
            <div key={s} className="flex items-center shrink-0">
              <div className={`border rounded-md px-3 py-2 w-44 ${n.cls}`}>
                <div className="font-mono text-xs truncate">{s}</div>
                <div className="flex items-center gap-1 text-[11px] mt-1"><Icon size={11} />{n.text}</div>
              </div>
              {i < steps.length - 1 && (
                <div className="flex items-center w-12">
                  <div className={`h-px flex-1 ${broken ? 'bg-sev-low/60 border-t border-dashed border-sev-low' : 'bg-sev-critical/60'}`} />
                  {broken && <X size={12} className="text-sev-low -mx-1.5 bg-base-950" />}
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}

export function ChainDisruption({ steps, replayTest, blocked, residual = [], disrupted }) {
  const after = (s) =>
    s === replayTest ? (blocked ? 'blocked' : 'vulnerable') : residual.includes(s) ? 'vulnerable' : 'not_replayed'
  const idx = steps.indexOf(replayTest)
  const brokenFrom = disrupted && blocked && idx >= 0 ? idx : null
  return (
    <div className="bg-base-900 border border-base-700 rounded-lg p-4 space-y-5">
      <Row title="Before mitigation: chain fully exploitable" steps={steps} state={() => 'vulnerable'} />
      <Row title="After mitigation and same-attack replay" steps={steps} state={after} brokenFrom={brokenFrom} />
      <p className="text-xs text-base-400">
        Only the replayed step ({replayTest}) is re-tested. A dashed link means the chain cannot proceed past a blocked step.
        Steps marked "not replayed" were not re-tested by the sandbox.
      </p>
    </div>
  )
}

export function Verdict({ validated }) {
  const Icon = validated ? ShieldCheck : ShieldX
  return (
    <div
      className={`flex items-center gap-3 rounded-lg border px-4 py-3 ${
        validated ? 'border-sev-low/40 bg-sev-low/10 text-sev-low' : 'border-sev-critical/40 bg-sev-critical/10 text-sev-critical'
      }`}
    >
      <Icon size={20} />
      <div>
        <div className="text-sm font-semibold">{validated ? 'Mitigation VALIDATED' : 'Mitigation FAILED'}</div>
        <div className="text-xs opacity-80">
          {validated ? 'The same attack was blocked after the control was applied. Attack chain disrupted.' : 'The same attack still succeeds after the control was applied. Attack chain still active.'}
        </div>
      </div>
    </div>
  )
}
