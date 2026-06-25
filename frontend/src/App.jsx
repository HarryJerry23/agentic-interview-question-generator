import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import SessionSelector from './pages/SessionSelector.jsx'
import Progress from './pages/Progress.jsx'
import Review from './pages/Review.jsx'

export default function App() {
  return (
    <BrowserRouter>
      <div className="app">
        <header className="app-header">
          <span className="app-logo">🎯</span>
          <span className="app-title">Interview Question Generator</span>
        </header>
        <main className="app-main">
          <Routes>
            <Route path="/" element={<SessionSelector />} />
            <Route path="/progress/:runId" element={<Progress />} />
            <Route path="/review/:runId" element={<Review />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
