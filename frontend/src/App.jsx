import { Routes, Route } from 'react-router-dom'
import Header from './components/Header'
import Dashboard from './pages/Dashboard'
import NewExperiment from './pages/NewExperiment'
import ExperimentDetails from './pages/ExperimentDetails'
import ExperimentHistory from './pages/ExperimentHistory'
import LiveLogs from './pages/LiveLogs'
import Findings from './pages/Findings'
import ChainExplorer from './pages/ChainExplorer'
import Analytics from './pages/Analytics'
import Mitigation from './pages/Mitigation'
import MitigationResult from './pages/MitigationResult'
import Phase2Analytics from './pages/Phase2Analytics'

export default function App() {
  return (
    <div className="flex flex-col h-screen bg-base-950">
      <Header />
      <div className="flex-1 min-h-0 flex flex-col overflow-hidden">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/new-experiment" element={<NewExperiment />} />
          <Route path="/experiments" element={<ExperimentHistory />} />
          <Route path="/experiments/:id" element={<ExperimentDetails />} />
          <Route path="/logs" element={<LiveLogs />} />
          <Route path="/findings" element={<Findings />} />
          <Route path="/chains" element={<ChainExplorer />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/mitigation" element={<Mitigation />} />
          <Route path="/mitigation/:experimentId/:runId" element={<MitigationResult />} />
          <Route path="/phase2-analytics" element={<Phase2Analytics />} />
        </Routes>
      </div>
      <footer className="h-8 shrink-0 border-t border-base-700 flex items-center justify-center text-[11px] text-base-400 font-mono">
        Controlled sandbox only · No real-system targeting
      </footer>
    </div>
  )
}
