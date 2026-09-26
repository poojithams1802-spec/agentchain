export default function StatCard({ label, value, sub, accent }) {
  return (
    <div className="bg-base-900 border border-base-700 rounded-lg px-4 py-3.5">
      <div className="text-xs text-base-400">{label}</div>
      <div
        className="text-2xl font-semibold mt-1 font-mono"
        style={accent ? { color: accent } : undefined}
      >
        {value}
      </div>
      {sub && <div className="text-xs text-base-400 mt-1">{sub}</div>}
    </div>
  )
}
