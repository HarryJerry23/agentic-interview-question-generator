import { useState, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { api } from '../lib/api.js'

export default function Sidebar() {
  const navigate = useNavigate()
  const location = useLocation()

  const [topics, setTopics] = useState({})
  const [selectedTopic, setSelectedTopic] = useState('')
  const [maxQuestions, setMaxQuestions] = useState(12)
  const [starting, setStarting] = useState(false)
  const [history, setHistory] = useState([])

  useEffect(() => {
    api.getTopics().then(d => setTopics(d.topics || {})).catch(() => {})
    api.getHistory().then(d => setHistory(d.runs || [])).catch(() => {})
  }, [])

  useEffect(() => {
    api.getHistory().then(d => setHistory(d.runs || [])).catch(() => {})
  }, [location.pathname])

  async function handleGenerate() {
    if (!selectedTopic || starting) return
    setStarting(true)
    try {
      const sessionNames = topics[selectedTopic] || []
      const { run_id } = await api.generate(sessionNames, maxQuestions)
      navigate(`/progress/${run_id}`)
    } catch {
      // stay on page
    } finally {
      setStarting(false)
    }
  }

  const sessions = selectedTopic ? (topics[selectedTopic] || []) : []

  return (
    <aside className="sidebar">
      {/* Logo */}
      <div className="sidebar-logo" onClick={() => navigate('/')}>
        <span className="sidebar-logo-main">NxtMock</span>
        <span className="sidebar-logo-sub">Interview Generator</span>
      </div>

      {/* Topic dropdown */}
      <div className="sidebar-picker">
        <span className="sidebar-section-label">Topic</span>
        <div className="sidebar-select-wrap">
          <select
            className="sidebar-topic-select"
            value={selectedTopic}
            onChange={e => setSelectedTopic(e.target.value)}
          >
            <option value="">Select a topic…</option>
            {Object.keys(topics).map(t => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
        </div>

        {/* Sessions included in this topic — info only */}
        {sessions.length > 0 && (
          <>
            <span className="sidebar-section-label" style={{ marginTop: '0.5rem' }}>
              Sessions included ({sessions.length})
            </span>
            <div className="sidebar-session-list">
              {sessions.map(s => (
                <div key={s} className="sidebar-session-info" title={s}>
                  · {s}
                </div>
              ))}
            </div>
          </>
        )}
      </div>

      {/* Generate area */}
      <div className="sidebar-generate-area">
        <div className="sidebar-maxq-label">
          Max questions: <strong>{maxQuestions}</strong>
        </div>
        <input
          type="range" min={5} max={15} value={maxQuestions}
          onChange={e => setMaxQuestions(+e.target.value)}
          className="sidebar-range"
        />
        <button
          className="sidebar-gen-btn"
          disabled={!selectedTopic || starting}
          onClick={handleGenerate}
        >
          {starting ? 'Starting…' : selectedTopic ? 'Generate Questions ▸' : 'Select a topic first'}
        </button>
      </div>

      {/* Recent Runs */}
      <div className="sidebar-history">
        <div className="sidebar-history-header">
          <span className="sidebar-history-label">Recent Runs</span>
          {history.length > 0 && (
            <span className="sidebar-view-all" onClick={() => navigate('/history')}>View all</span>
          )}
        </div>
        {history.length === 0 ? (
          <div className="sidebar-empty-hist">No runs yet</div>
        ) : (
          history.slice(0, 6).map(run => (
            <div
              key={run.run_id}
              className="sidebar-run-item"
              onClick={() => navigate(`/review/${run.run_id}`)}
            >
              <span className="sidebar-run-name">{run.session_name}</span>
              <span className="sidebar-run-meta">{run.question_count}q · {run.run_id.slice(0, 7)}</span>
            </div>
          ))
        )}
      </div>

      {/* Footer */}
      <div className="sidebar-footer">
        <div className="sidebar-model-label">Model</div>
        <span className="sidebar-model-chip">claude-haiku-4-5</span>
        <div className="sidebar-model-via">via OpenRouter</div>
      </div>
    </aside>
  )
}
