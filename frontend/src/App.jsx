import { Routes, Route } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import Dashboard from './pages/Dashboard'
import NewExperiment from './pages/NewExperiment'
import ExperimentDetails from './pages/ExperimentDetails'
import ExperimentHistory from './pages/ExperimentHistory'
import LiveLogs from './pages/LiveLogs'
import Findings from './pages/Findings'
import ChainExplorer from './pages/ChainExplorer'
import Analytics from './pages/Analytics'

export default function App() {
  return (
    <div className="flex h-screen bg-base-950">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/new-experiment" element={<NewExperiment />} />
          <Route path="/experiments" element={<ExperimentHistory />} />
          <Route path="/experiments/:id" element={<ExperimentDetails />} />
          <Route path="/logs" element={<LiveLogs />} />
          <Route path="/findings" element={<Findings />} />
          <Route path="/chains" element={<ChainExplorer />} />
          <Route path="/analytics" element={<Analytics />} />
        </Routes>
      </div>
    </div>
  )
}
