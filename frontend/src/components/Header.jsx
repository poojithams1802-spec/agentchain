import { NavLink, Link } from 'react-router-dom'
import { Shield, Sun, Moon, Zap } from 'lucide-react'
import { useTheme } from '../lib/theme'

const NAV = [
  { to: '/', label: 'Dashboard', end: true },
  { to: '/new-experiment', label: 'New Experiment' },
  { to: '/experiments', label: 'History' },
  { to: '/logs', label: 'Live Logs' },
  { to: '/findings', label: 'Findings' },
  { to: '/chains', label: 'Attack Chains' },
  { to: '/analytics', label: 'Analytics' },
  { to: '/mitigation', label: 'Mitigation' },
  { to: '/phase2-analytics', label: 'Mitigation Metrics' },
]

export default function Header() {
  const { dark, toggle } = useTheme()
  return (
    <header className="sticky top-0 z-50 shrink-0 border-b border-base-700 bg-base-900/90 backdrop-blur-md transition-colors">
      <div className="px-4 sm:px-6 h-16 flex items-center gap-4">
        <Link to="/" className="flex items-center gap-3 shrink-0">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-blue-600 via-cyan-500 to-violet-600 grid place-items-center shadow-md shadow-blue-500/20 text-white">
            <Shield className="w-5 h-5" strokeWidth={2.5} />
          </div>
          <span className="font-extrabold text-xl tracking-tight">
            <span className="text-base-100">Agent</span>
            <span className="bg-gradient-to-r from-blue-600 to-violet-600 bg-clip-text text-transparent">Chain</span>
          </span>
          <span className="hidden sm:inline px-2 py-0.5 text-[10px] font-semibold tracking-wide uppercase rounded-full bg-blue-50 dark:bg-blue-950/60 text-blue-600 dark:text-blue-400 border border-blue-200 dark:border-blue-800/50">
            Phase 2
          </span>
        </Link>

        <nav className="flex-1 min-w-0 flex items-center gap-1 overflow-x-auto scrollbar-none text-xs font-medium">
          {NAV.map(({ to, label, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                `px-3 py-1.5 rounded-lg whitespace-nowrap transition-all ${
                  isActive
                    ? 'bg-blue-50 dark:bg-blue-900/40 text-blue-600 dark:text-blue-400 font-semibold'
                    : 'text-base-300 hover:text-base-100 hover:bg-base-800'
                }`
              }
            >
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="flex items-center gap-3 shrink-0">
          <button
            onClick={toggle}
            title="Toggle light / dark theme"
            aria-label="Toggle light / dark theme"
            className="flex items-center bg-base-800 p-1 rounded-full border border-base-700 transition"
          >
            <span className={`flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold transition ${!dark ? 'bg-white text-blue-600 shadow-sm' : 'text-base-400'}`}>
              <Sun className="w-3.5 h-3.5" />
              <span className="hidden md:inline">Light</span>
            </span>
            <span className={`flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold transition ${dark ? 'bg-slate-900 text-cyan-400 shadow-sm' : 'text-base-400'}`}>
              <Moon className="w-3.5 h-3.5" />
              <span className="hidden md:inline">Dark</span>
            </span>
          </button>

          <Link to="/new-experiment" className="btn-primary hidden sm:inline-flex px-3.5 py-1.5 text-xs">
            <Zap className="w-3.5 h-3.5 fill-current" />
            Start Experiment
          </Link>
        </div>
      </div>
    </header>
  )
}
