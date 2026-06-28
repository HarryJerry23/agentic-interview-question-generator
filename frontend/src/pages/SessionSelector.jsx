import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../lib/api.js'

export default function WelcomePage() {
  const navigate = useNavigate()
  const [topicCount, setTopicCount] = useState(null)
  const [runs, setRuns] = useState([])

  useEffect(() => {
    api.getTopics()
      .then(d => setTopicCount(Object.keys(d.topics || {}).length))
      .catch(() => {})
    api.getHistory()
      .then(d => setRuns(d.runs || []))
      .catch(() => {})
  }, [])

  const recentRuns = runs.slice(0, 4)

  return (
    <>
      <header className="topbar">
        <div className="topbar-title-group">
          <span className="topbar-title">NxtMock Interview Generator</span>
          <span className="topbar-sub">Topic-specific company interview questions for student mock prep</span>
        </div>
      </header>

      <div className="page-content">
        {/* Stats row */}
        <div className="home-stats">
          <div className="home-stat-card">
            <span className="home-stat-num">{topicCount ?? '—'}</span>
            <span className="home-stat-label">Topics available</span>
          </div>
          <div className="home-stat-card">
            <span className="home-stat-num">3,133</span>
            <span className="home-stat-label">Questions indexed</span>
          </div>
          <div className="home-stat-card">
            <span className="home-stat-num">{runs.length}</span>
            <span className="home-stat-label">Runs generated</span>
          </div>
        </div>

        {/* Recent runs */}
        {recentRuns.length > 0 && (
          <section className="card">
            <div className="card-title-row">
              <h2 className="card-title" style={{ marginBottom: 0 }}>Recent Runs</h2>
              <button className="btn btn-ghost btn-sm" onClick={() => navigate('/history')}>
                View all ▸
              </button>
            </div>
            <div className="recent-runs-list">
              {recentRuns.map(run => (
                <div
                  key={run.run_id}
                  className="recent-run-row"
                  onClick={() => navigate(`/review/${run.run_id}`)}
                >
                  <div className="rrr-info">
                    <span className="rrr-name">{run.session_name}</span>
                    <span className="rrr-meta">
                      {run.question_count != null ? `${run.question_count} questions` : '—'}
                      {run.composite_score != null && ` · ${Math.round(run.composite_score * 100)}% score`}
                      {run.approved ? ' · Approved' : ' · In-memory'}
                    </span>
                  </div>
                  <button
                    className="btn btn-ghost btn-sm"
                    onClick={e => { e.stopPropagation(); navigate(`/review/${run.run_id}`) }}
                  >
                    Review ▸
                  </button>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Getting started hint */}
        <div className="home-hint">
          <span className="home-hint-step">1</span>
          Select a topic from the sidebar dropdown
          <span className="home-hint-sep">·</span>
          <span className="home-hint-step">2</span>
          Adjust question count
          <span className="home-hint-sep">·</span>
          <span className="home-hint-step">3</span>
          Click Generate Questions
        </div>
      </div>
    </>
  )
}
