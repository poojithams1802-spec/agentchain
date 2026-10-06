import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Brain, Play, ShieldCheck, Sparkles } from 'lucide-react'
import { CONTROLS } from '../lib/mitigation'

// Static illustration of the agreed Level-3 workflow. No live data.
const NODES = [
  { name: 'Discover', desc: 'Adaptive red-team tests find vulnerabilities', color: 'text-blue-400', bg: 'bg-blue-500/10', border: 'border-blue-500/40' },
  { name: 'Analyze', desc: 'Findings are linked into an attack chain', color: 'text-indigo-400', bg: 'bg-indigo-500/10', border: 'border-indigo-500/40' },
  { name: 'LLM + Security RAG', desc: 'Security knowledge guides the analysis', color: 'text-cyan-400', bg: 'bg-cyan-500/10', border: 'border-cyan-500/40' },
  { name: 'Select Control', desc: 'One predefined control is chosen', color: 'text-purple-400', bg: 'bg-purple-500/10', border: 'border-purple-500/40' },
  { name: 'Apply Control', desc: 'The control is applied in the sandbox', color: 'text-blue-300', bg: 'bg-blue-600/10', border: 'border-blue-600/40' },
  { name: 'Replay Same Attack', desc: 'The exact same attack is run again', color: 'text-cyan-300', bg: 'bg-cyan-600/10', border: 'border-cyan-600/40' },
  { name: 'Validate', desc: 'Before/after shows whether the chain broke', color: 'text-emerald-400', bg: 'bg-emerald-500/10', border: 'border-emerald-500/40' },
]

export default function LoopHero() {
  const [active, setActive] = useState(0)
  useEffect(() => {
    const t = setInterval(() => setActive((p) => (p + 1) % NODES.length), 3000)
    return () => clearInterval(t)
  }, [])
  const cur = NODES[active]

  return (
    <section className="relative overflow-hidden rounded-2xl bg-[#07111F] text-slate-100 border border-slate-800/80">
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#101f38_1px,transparent_1px),linear-gradient(to_bottom,#101f38_1px,transparent_1px)] bg-[size:3rem_3rem] [mask-image:radial-gradient(ellipse_70%_60%_at_50%_0%,#000_70%,transparent_100%)] opacity-40" />
      <div className="absolute top-0 right-1/4 w-80 h-80 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-0 left-1/4 w-80 h-80 bg-violet-600/10 rounded-full blur-3xl pointer-events-none" />

      <div className="relative z-10 grid grid-cols-1 lg:grid-cols-12 gap-8 items-center p-6 lg:p-8">
        <div className="lg:col-span-5 space-y-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/30 text-blue-400 text-xs font-medium">
            <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
            Knowledge-guided closed-loop defense
          </div>
          <h2 className="text-4xl font-black tracking-tight text-white">
            Agent<span className="bg-gradient-to-r from-blue-400 via-cyan-400 to-violet-400 bg-clip-text text-transparent">Chain</span>
          </h2>
          <p className="text-sm font-semibold text-slate-200">
            Adaptive Attack-Chain Mitigation and Validation in Agentic AI Systems
          </p>
          <p className="text-xs text-slate-400 leading-relaxed">
            Discover attack chains, let an LLM with security RAG select a predefined defensive control, apply it in the
            controlled sandbox, replay the same attack, and validate whether the chain was disrupted.
          </p>
          <div className="flex flex-wrap gap-3 pt-1">
            <Link to="/mitigation" className="btn-primary px-5 py-2.5 text-xs shadow-lg">
              <Play className="w-4 h-4 fill-current" />
              Run Mitigation
            </Link>
            <Link to="/new-experiment" className="btn-ghost-dark px-5 py-2.5 text-xs">
              New Experiment
            </Link>
          </div>
        </div>

        <div className="lg:col-span-4 flex flex-col items-center">
          <div className="relative w-72 h-72 flex items-center justify-center">
            <div className="absolute inset-0 rounded-full border-2 border-dashed border-cyan-500/30 animate-[spin_40s_linear_infinite]" />
            <div className="absolute inset-4 rounded-full border border-violet-500/20" />
            <div className="relative z-20 w-24 h-24 rounded-full bg-gradient-to-br from-slate-900 via-blue-950 to-slate-900 border-2 border-cyan-500/50 flex flex-col items-center justify-center text-center shadow-2xl shadow-cyan-500/20">
              <Brain className="w-5 h-5 text-cyan-400 mb-1" />
              <span className="text-[10px] font-extrabold uppercase tracking-widest text-cyan-300">Detect</span>
              <span className="text-[8px] font-medium text-slate-400">Mitigate · Validate</span>
            </div>
            {NODES.map((n, i) => {
              const a = (i * (360 / NODES.length) - 90) * (Math.PI / 180)
              const x = Math.round(112 * Math.cos(a))
              const y = Math.round(112 * Math.sin(a))
              const on = i === active
              return (
                <button
                  key={n.name}
                  onClick={() => setActive(i)}
                  aria-label={n.name}
                  style={{ transform: `translate(${x}px, ${y}px)` }}
                  className={`absolute z-30 transition-all duration-300 ${on ? 'scale-110' : 'hover:scale-105'}`}
                >
                  <span className={`w-10 h-10 rounded-full border grid place-items-center backdrop-blur-md shadow-lg ${n.bg} ${n.border} ${on ? 'ring-2 ring-cyan-400 ring-offset-2 ring-offset-slate-950' : ''}`}>
                    <span className={`text-xs font-bold ${n.color}`}>{i + 1}</span>
                  </span>
                </button>
              )
            })}
          </div>
          <div className="mt-3 text-center min-h-[2.5rem]">
            <div className="text-xs font-bold text-cyan-300">{active + 1}. {cur.name}</div>
            <div className="text-[11px] text-slate-400">{cur.desc}</div>
          </div>
        </div>

        <div className="lg:col-span-3">
          <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 backdrop-blur-xl space-y-3">
            <div className="flex items-center gap-2 pb-2 border-b border-slate-800">
              <ShieldCheck className="w-4 h-4 text-cyan-400" />
              <span className="text-xs font-bold uppercase tracking-wider text-slate-300">Predefined controls</span>
            </div>
            {Object.entries(CONTROLS).map(([id, c]) => (
              <div key={id} className="p-2 rounded-lg bg-slate-950/50 border border-slate-800/60 text-xs">
                <div className="font-semibold text-slate-200">{c.label}</div>
                <div className="text-[10px] text-slate-400 font-mono">{id} · replays {c.test}</div>
              </div>
            ))}
            <p className="text-[10px] text-slate-500">The LLM selects only from this list. It never writes code.</p>
          </div>
        </div>
      </div>
    </section>
  )
}
