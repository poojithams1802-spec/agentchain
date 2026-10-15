import { Check, X, ShieldCheck, ShieldAlert, ShieldX } from 'lucide-react'
import { fmtPct, prettify } from '../lib/phase3'

// Verdict is read straight from the replay response: HTTP 200 alone does not mean
// the mitigation worked (API_CONTRACT §2.12), so inspect validation_result,
// chain_disrupted, blocked_steps and residual_vulnerable_steps.
export function replayVerdict(result) {
  const vr = result?.validation_result ?? {}
  const disrupted = result?.chain_disrupted === true
  if (vr.status === 'validated' && disrupted) {
    return { tone: 'good', Icon: ShieldCheck, title: 'Mitigation validated', text: 'The control blocked a step and the full chain no longer completes as before.' }
  }
  if (disrupted) {
    return { tone: 'warn', Icon: ShieldAlert, title: 'Chain disrupted, validation incomplete', text: 'A step was blocked, but the replay did not satisfy every validation check.' }
  }
  return { tone: 'bad', Icon: ShieldX, title: 'Mitigation did not disrupt the chain', text: 'No step in this chain was blocked by the selected control.' }
}

const TONE = {
  good: 'border-sev-low/40 bg-sev-low/10 text-sev-low',
  warn: 'border-sev-medium/40 bg-sev-medium/10 text-sev-medium',
  bad: 'border-sev-critical/40 bg-sev-critical/10 text-sev-critical',
}

export function ReplayVerdict({ result }) {
  const v = replayVerdict(result)
  return (
    <div className={`flex items-center gap-3 rounded-lg border px-4 py-3 ${TONE[v.tone]}`} role="status">
      <v.Icon size={20} />
      <div>
        <div className="text-sm font-semibold">{v.title}</div>
        <div className="text-xs opacity-80">{v.text}</div>
      </div>
    </div>
  )
}

const NODE = {
  vulnerable: { cls: 'border-sev-critical/60 text-sev-critical bg-sev-critical/10', Icon: X, text: 'vulnerable' },
  blocked: { cls: 'border-sev-low/60 text-sev-low bg-sev-low/10', Icon: Check, text: 'blocked' },
}

function Row({ title, steps, state, brokenFrom }) {
  return (
    <div>
      <div className="text-xs text-base-400 mb-2">{title}</div>
      <div className="flex items-center overflow-x-auto scrollbar-thin pb-1">
        {steps.map((s, i) => {
          const n = NODE[state(s)]
          const broken = brokenFrom != null && i >= brokenFrom
          return (
            <div key={s} className="flex items-center shrink-0">
              <div className={`border rounded-md px-3 py-2 w-44 ${n.cls}`}>
                <div className="font-mono text-xs truncate" title={s}>{s}</div>
                <div className="flex items-center gap-1 text-[11px] mt-1"><n.Icon size={11} />{n.text}</div>
              </div>
              {i < steps.length - 1 && (
                <div className="flex items-center w-12" aria-hidden>
                  <div className={`h-px flex-1 ${broken ? 'border-t border-dashed border-sev-low' : 'bg-sev-critical/60'}`} />
                  {broken && <X size={12} className="text-sev-low -mx-1.5 bg-base-900" />}
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}

// Before: every step ran and produced its finding. After: P4 marks blocked steps;
// every other step is residual (still vulnerable). Links after the first blocked
// step are drawn broken because the chain cannot proceed past it.
export function ChainBeforeAfter({ result }) {
  const steps = result.chain_steps ?? []
  const blocked = result.blocked_steps ?? []
  const firstBlocked = steps.findIndex((s) => blocked.includes(s))
  return (
    <div className="bg-base-900 border border-base-700 rounded-lg p-4 space-y-5">
      <Row title="Before mitigation" steps={steps} state={() => 'vulnerable'} />
      <Row
        title={`After applying ${prettify(result.control)} and replaying the whole chain`}
        steps={steps}
        state={(s) => (blocked.includes(s) ? 'blocked' : 'vulnerable')}
        brokenFrom={firstBlocked >= 0 ? firstBlocked : null}
      />
    </div>
  )
}

function Mark({ ok }) {
  return ok ? <Check size={13} className="inline text-sev-low" aria-label="yes" /> : <X size={13} className="inline text-sev-critical" aria-label="no" />
}

export function StepValidationTable({ before, after, blocked = [] }) {
  const rows = (before?.steps ?? []).map((b, i) => ({ b, a: after?.steps?.[i] }))
  if (!rows.length) return null
  return (
    <div className="overflow-x-auto border border-base-700 rounded-lg scrollbar-thin">
      <table className="w-full text-xs">
        <thead className="bg-base-800 text-base-300">
          <tr>
            <th className="text-left p-2">Step</th>
            <th className="p-2">Before: valid</th>
            <th className="p-2">After: valid</th>
            <th className="p-2 text-left">After: state</th>
            <th className="p-2 text-left">Expected finding</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-base-700 font-mono">
          {rows.map(({ b, a }) => (
            <tr key={b.test}>
              <td className="p-2 text-base-100">{b.test}</td>
              <td className="p-2 text-center"><Mark ok={b.valid} /></td>
              <td className="p-2 text-center">{a ? <Mark ok={a.valid} /> : '—'}</td>
              <td className={`p-2 ${blocked.includes(b.test) ? 'text-sev-low' : 'text-sev-critical'}`}>
                {blocked.includes(b.test) ? 'blocked' : 'still vulnerable'}
              </td>
              <td className="p-2 text-base-300">{prettify(b.expected_finding)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <div className="px-2 py-1.5 text-[11px] text-base-400 border-t border-base-700 flex gap-4 bg-base-800/50">
        <span>before: {fmtPct(before?.validation_rate)} valid</span>
        <span>after: {fmtPct(after?.validation_rate)} valid</span>
      </div>
    </div>
  )
}
