import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  FlaskConical,
  FileSearch,
  ScrollText,
  ShieldAlert,
  GitBranch,
  BarChart3,
  History,
  Link2,
} from 'lucide-react'

const NAV = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard, end: true },
  { to: '/new-experiment', label: 'New Experiment', icon: FlaskConical },
  { to: '/experiments', label: 'Experiment History', icon: History },
  { to: '/logs', label: 'Live Logs', icon: ScrollText },
  { to: '/findings', label: 'Findings', icon: ShieldAlert },
  { to: '/chains', label: 'Attack Chain Explorer', icon: GitBranch },
  { to: '/analytics', label: 'Analytics', icon: BarChart3 },
]

export default function Sidebar() {
  return (
    <aside className="w-60 shrink-0 border-r border-base-700 bg-base-900 flex flex-col">
      <div className="h-16 flex items-center gap-2 px-5 border-b border-base-700">
        <Link2 size={18} className="text-signal" />
        <span className="font-semibold tracking-tight text-base-100">AgentChain</span>
      </div>
      <nav className="flex-1 py-3 px-2 space-y-0.5 overflow-y-auto scrollbar-thin">
        {NAV.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors ${
                isActive
                  ? 'bg-base-800 text-signal border-l-2 border-signal pl-[10px]'
                  : 'text-base-300 hover:text-base-100 hover:bg-base-800/60'
              }`
            }
          >
            <Icon size={16} strokeWidth={2} />
            {label}
          </NavLink>
        ))}
      </nav>
      <div className="px-4 py-3 border-t border-base-700 text-xs text-base-400 font-mono leading-relaxed">
        Controlled sandbox only.
        <br />
        No real-system targeting.
      </div>
    </aside>
  )
}
