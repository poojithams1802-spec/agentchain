import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import TopBar from '../components/TopBar'
import { createExperiment, startExperiment } from '../api/client'

export default function NewExperiment() {
  const navigate = useNavigate()
  const [name, setName] = useState('')
  const [mode, setMode] = useState('adaptive')
  const [maxTests, setMaxTests] = useState(10)
  const [budget, setBudget] = useState(20)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)

  async function handleStart(e) {
    e.preventDefault()
    if (!name.trim()) {
      setError('Give the experiment a name.')
      return
    }
    setSubmitting(true)
    setError(null)
    try {
      const created = await createExperiment({ name, mode, max_tests: maxTests })
      await startExperiment(created.experiment_id)
      navigate(`/experiments/${created.experiment_id}`)
    } catch (e) {
      setError(e.message)
      setSubmitting(false)
    }
  }

  return (
    <>
      <TopBar title="New Experiment" subtitle="Configure a Static or Adaptive testing run" />
      <div className="flex-1 overflow-y-auto scrollbar-thin p-6">
        <form onSubmit={handleStart} className="max-w-lg space-y-6">
          <div>
            <label className="block text-sm text-base-200 mb-1.5">Experiment name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Adaptive Run — Memory Chain Focus"
              className="w-full bg-base-900 border border-base-700 rounded-md px-3 py-2 text-sm text-base-100 placeholder:text-base-500 focus:border-signal outline-none"
            />
          </div>

          <div>
            <label className="block text-sm text-base-200 mb-1.5">Testing mode</label>
            <div className="grid grid-cols-2 gap-2">
              {['adaptive', 'static'].map((m) => (
                <button
                  type="button"
                  key={m}
                  onClick={() => setMode(m)}
                  className={`rounded-md border px-3 py-2.5 text-left text-sm transition-colors ${
                    mode === m
                      ? 'border-signal bg-signal/10 text-signal'
                      : 'border-base-700 text-base-300 hover:border-base-500'
                  }`}
                >
                  <div className="font-medium capitalize">{m}</div>
                  <div className="text-xs text-base-400 mt-0.5">
                    {m === 'adaptive'
                      ? 'Planner selects next test from findings so far.'
                      : 'Fixed, pre-determined test sequence.'}
                  </div>
                </button>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-base-200 mb-1.5">Maximum tests</label>
              <input
                type="number"
                min={1}
                max={50}
                value={maxTests}
                onChange={(e) => setMaxTests(Number(e.target.value))}
                className="w-full bg-base-900 border border-base-700 rounded-md px-3 py-2 text-sm text-base-100 font-mono focus:border-signal outline-none"
              />
            </div>
            <div>
              <label className="block text-sm text-base-200 mb-1.5">Testing budget</label>
              <input
                type="number"
                min={1}
                max={100}
                value={budget}
                onChange={(e) => setBudget(Number(e.target.value))}
                className="w-full bg-base-900 border border-base-700 rounded-md px-3 py-2 text-sm text-base-100 font-mono focus:border-signal outline-none"
              />
            </div>
          </div>

          {error && <p className="text-sm text-sev-critical">{error}</p>}

          <button
            type="submit"
            disabled={submitting}
            className="bg-signal text-base-950 font-medium text-sm px-4 py-2 rounded-md hover:bg-signal-bright transition-colors disabled:opacity-50"
          >
            {submitting ? 'Starting…' : 'Start Experiment'}
          </button>
        </form>
      </div>
    </>
  )
}
