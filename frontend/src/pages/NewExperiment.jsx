import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import TopBar from '../components/TopBar'
import { ScenarioPicker, VulnerabilityPicker } from '../components/Pickers'
import { Notice } from '../components/Phase3Parts'
import { createExperiment, startExperiment, listScenarios, apiError } from '../api/client'
import { saveAdaptiveRun } from '../lib/adaptiveRuns'
import { VULNERABILITIES } from '../lib/phase3'

const DEFAULT_CHAIN_LENGTH = 3

export default function NewExperiment() {
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const [name, setName] = useState('')
  const [mode, setMode] = useState('adaptive')
  const [maxTests, setMaxTests] = useState(10)
  const [budget, setBudget] = useState(20)
  const [scenario, setScenario] = useState(null)
  const [vulns, setVulns] = useState([])
  const [scenarios, setScenarios] = useState({ loading: true, error: null, items: [] })
  const [submitting, setSubmitting] = useState(false)
  const [phase, setPhase] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    listScenarios()
      .then((items) => {
        setScenarios({ loading: false, error: null, items })
        // Deep link from the Vulnerabilities page: /new-experiment?scenario=CHAIN_B
        const wanted = items.find((s) => s.scenario_id === params.get('scenario'))
        if (wanted) setScenario(wanted)
      })
      .catch((e) => setScenarios({ loading: false, error: apiError(e), items: [] }))
  }, [])

  // Mirrors backend: min(max_tests, number of available tests); a scenario wins over vulnerability_ids.
  const available = scenario ? scenario.steps.length : vulns.length || DEFAULT_CHAIN_LENGTH
  const effective = Math.min(Number(maxTests) || 0, available)
  const vulnLabels = useMemo(() => Object.fromEntries(VULNERABILITIES.map((v) => [v.id, v.test])), [])

  async function handleStart(e) {
    e.preventDefault()
    if (!name.trim()) {
      setError('Give the experiment a name.')
      return
    }
    setSubmitting(true)
    setError(null)
    try {
      setPhase('Creating experiment…')
      const created = await createExperiment({
        name,
        mode,
        max_tests: maxTests,
        testing_budget: budget,
        scenario_id: scenario?.scenario_id,
        scenario_name: scenario?.scenario_name,
        vulnerability_ids: scenario ? [] : vulns,
      })
      setPhase('Running planner and sandbox (this can take a minute)…')
      const started = await startExperiment(created.experiment_id)
      // The decision timeline needs this response; the backend has no GET for it yet.
      saveAdaptiveRun(created.experiment_id, started)
      navigate(`/experiments/${created.experiment_id}`)
    } catch (e) {
      setError(apiError(e))
      setSubmitting(false)
      setPhase(null)
    }
  }

  return (
    <>
      <TopBar title="New Experiment" subtitle="Configure a Static or Adaptive testing run" />
      <div className="flex-1 overflow-y-auto scrollbar-thin p-6">
        <form onSubmit={handleStart} className="max-w-3xl space-y-6">
          <div className="max-w-lg">
            <label htmlFor="exp-name" className="block text-sm text-base-200 mb-1.5">Experiment name</label>
            <input
              id="exp-name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Adaptive Run — Memory Chain Focus"
              className="w-full bg-base-900 border border-base-700 rounded-md px-3 py-2 text-sm text-base-100 placeholder:text-base-500 focus:border-signal outline-none"
            />
          </div>

          <div className="max-w-lg">
            <label className="block text-sm text-base-200 mb-1.5">Testing mode</label>
            <div className="grid grid-cols-2 gap-2">
              {['adaptive', 'static'].map((m) => (
                <button
                  type="button"
                  key={m}
                  onClick={() => setMode(m)}
                  className={`rounded-md border px-3 py-2.5 text-left text-sm transition-colors ${mode === m
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
            {mode === 'static' && (
              <div className="mt-2">
                <Notice tone="warn">
                  The backend start flow currently runs the planner loop for every experiment; the mode is stored with
                  the experiment and used for analytics grouping only.
                </Notice>
              </div>
            )}
          </div>

          <div>
            <div className="flex items-baseline justify-between mb-1.5">
              <label className="block text-sm text-base-200">Scenario</label>
              <span className="text-xs text-base-400">A registered scenario defines the chain steps.</span>
            </div>
            <ScenarioPicker
              scenarios={scenarios.items}
              loading={scenarios.loading}
              error={scenarios.error}
              value={scenario?.scenario_id ?? null}
              onChange={setScenario}
            />
          </div>

          <div>
            <div className="flex items-baseline justify-between mb-1.5">
              <label className="block text-sm text-base-200">Vulnerabilities (optional)</label>
              <span className="text-xs text-base-400">
                {scenario ? 'Ignored while a scenario is selected.' : 'Tests run in the order selected.'}
              </span>
            </div>
            <VulnerabilityPicker value={vulns} onChange={setVulns} disabled={!!scenario} />
          </div>

          <div className="grid grid-cols-2 gap-4 max-w-lg">
            <div>
              <label htmlFor="max-tests" className="block text-sm text-base-200 mb-1.5">Maximum tests</label>
              <input
                id="max-tests"
                type="number"
                min={1}
                max={50}
                value={maxTests}
                onChange={(e) => setMaxTests(Number(e.target.value))}
                className="w-full bg-base-900 border border-base-700 rounded-md px-3 py-2 text-sm text-base-100 font-mono focus:border-signal outline-none"
              />
            </div>
            <div>
              <label htmlFor="budget" className="block text-sm text-base-200 mb-1.5">Testing budget</label>
              <input
                id="budget"
                type="number"
                min={1}
                max={100}
                value={budget}
                onChange={(e) => setBudget(Number(e.target.value))}
                className="w-full bg-base-900 border border-base-700 rounded-md px-3 py-2 text-sm text-base-100 font-mono focus:border-signal outline-none"
              />
            </div>
          </div>

          <div className="max-w-lg space-y-2">
            <p className="text-xs text-base-300">
              Up to <b className="font-mono">{effective}</b> test{effective === 1 ? '' : 's'} will run
              <span className="text-base-400"> (maximum tests, capped by the {available} available in this selection).</span>
            </p>
            <p className="text-xs text-base-400">
              Testing budget is stored with the experiment. The planner’s LLM-call and time caps are set server-side and
              are reported after the run in Adaptive Run → Budget.
            </p>
            {vulns.length > 0 && !scenario && (
              <p className="text-[11px] font-mono text-base-500 break-words">
                {vulns.map((v) => `${v}=${vulnLabels[v]}`).join(' → ')}
              </p>
            )}
          </div>

          {error && <p className="text-sm text-sev-critical" role="alert">{error}</p>}

          <div className="flex items-center gap-2">
            <button
              type="submit"
              disabled={submitting}
              className="btn-primary font-medium text-sm px-4 py-2 rounded-md  transition-colors disabled:opacity-50"
            >
              {submitting ? 'Starting…' : 'Start Experiment'}
            </button>

            <button
              type="button"
              onClick={() => navigate('/')}
              disabled={submitting}
              className="border border-base-700 text-base-300 font-medium text-sm px-4 py-2 rounded-md hover:border-base-500 hover:text-base-100 transition-colors disabled:opacity-50"
            >
              Cancel
            </button>
          </div>
          <p className="text-xs text-base-500" aria-live="polite">
            {phase ?? 'Starting an experiment will create the run and immediately begin testing.'}
          </p>
        </form>
      </div>
    </>
  )
}
