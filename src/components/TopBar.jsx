export default function TopBar({ title, subtitle, actions }) {
  return (
    <header className="h-16 border-b border-base-700 flex items-center justify-between px-6 shrink-0">
      <div>
        <h1 className="text-base font-semibold text-base-100">{title}</h1>
        {subtitle && <p className="text-xs text-base-400 mt-0.5">{subtitle}</p>}
      </div>
      {actions && <div className="flex items-center gap-2">{actions}</div>}
    </header>
  )
}
