import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Sidebar from './components/Sidebar.jsx'
import SessionSelector from './pages/SessionSelector.jsx'
import Progress from './pages/Progress.jsx'
import Review from './pages/Review.jsx'
import History from './pages/History.jsx'

export default function App() {
  return (
    <BrowserRouter>
      <div className="shell">
        <Sidebar />
        <div className="shell-main">
          <Routes>
            <Route path="/" element={<SessionSelector />} />
            <Route path="/progress/:runId" element={<Progress />} />
            <Route path="/review/:runId" element={<Review />} />
            <Route path="/history" element={<History />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </div>
      </div>
    </BrowserRouter>
  )
}
