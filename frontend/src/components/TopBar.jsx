export default function TopBar({ title, subtitle, actions }) {
  return (
    <header className="min-h-[4rem] border-b border-base-700 flex items-center justify-between gap-4 px-6 py-3 shrink-0 bg-base-950">
      <div className="min-w-0">
        <h1 className="text-lg font-extrabold tracking-tight text-base-100">{title}</h1>
        {subtitle && <p className="text-xs text-base-400 mt-0.5">{subtitle}</p>}
      </div>
      {actions && <div className="flex items-center gap-2 shrink-0">{actions}</div>}
    </header>
  )
}
