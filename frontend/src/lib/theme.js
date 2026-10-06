import { useCallback, useEffect, useState } from 'react'

const KEY = 'agentchain.theme'
const EVENT = 'agentchain-theme'

export function applyTheme(dark) {
  document.documentElement.classList.toggle('dark', dark)
  try {
    localStorage.setItem(KEY, dark ? 'dark' : 'light')
  } catch {
    /* storage unavailable: ignore */
  }
  window.dispatchEvent(new Event(EVENT))
}

export function useTheme() {
  const read = () => document.documentElement.classList.contains('dark')
  const [dark, setDark] = useState(read)
  useEffect(() => {
    const sync = () => setDark(read())
    window.addEventListener(EVENT, sync)
    return () => window.removeEventListener(EVENT, sync)
  }, [])
  const toggle = useCallback(() => applyTheme(!read()), [])
  return { dark, toggle }
}

// Colors for places that cannot use Tailwind classes (charts, graph canvas).
export function chartColors(dark) {
  return {
    grid: dark ? '#1E2D4D' : '#E2E8F0',
    axis: dark ? '#94A3B8' : '#64748B',
    cursor: dark ? '#1E2D4D' : '#F1F5F9',
    tooltip: {
      background: dark ? '#111F3A' : '#FFFFFF',
      border: `1px solid ${dark ? '#1E2D4D' : '#E2E8F0'}`,
      borderRadius: 12,
      fontSize: 12,
      color: dark ? '#F1F5F9' : '#0F172A',
    },
    nodeBg: dark ? '#111F3A' : '#FFFFFF',
    nodeText: dark ? '#F1F5F9' : '#0F172A',
    nodeBorder: dark ? '#3E5078' : '#CBD5E1',
    edge: dark ? '#6B7C9C' : '#94A3B8',
    dots: dark ? '#1E2D4D' : '#E2E8F0',
  }
}
