import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../lib/api.js'

function TopicRow({ topic, sessions, selectedSessions, onToggleTopic, onToggleSession, expanded, onToggleExpand }) {
  const total = sessions.length
  const selectedCount = sessions.filter(s => selectedSessions.has(s)).length
  const allSelected = selectedCount === total
  const someSelected = selectedCount > 0 && !allSelected

  const checkRef = useRef(null)
  useEffect(() => {
    if (checkRef.current) checkRef.current.indeterminate = someSelected
  }, [someSelected])

  return (
    <li className="topic-group">
      <div className="topic-row">
        <input
          type="checkbox"
          ref={checkRef}
          checked={allSelected}
          onChange={() => onToggleTopic(topic, sessions, allSelected)}
        />
        <button className="topic-expand-btn" onClick={() => onToggleExpand(topic)}>
          <span className={`expand-arrow ${expanded ? 'expanded' : ''}`}>▶</span>
          <span className="topic-name">{topic}</span>
          <span className="topic-badge">{selectedCount > 0 ? `${selectedCount}/` : ''}{total} session{total !== 1 ? 's' : ''}</span>
        </button>
      </div>
      {expanded && (
        <ul className="session-sublist">
          {sessions.map(name => (
            <li key={name}>
              <label className="session-row session-sub-row">
                <input
                  type="checkbox"
                  checked={selectedSessions.has(name)}
                  onChange={() => onToggleSession(name)}
                />
                <span className="session-name">{name}</span>
              </label>
            </li>
          ))}
        </ul>
      )}
    </li>
  )
}

export default function SessionSelector() {
  const navigate = useNavigate()
  const [topics, setTopics] = useState({})
  const [selectedSessions, setSelectedSessions] = useState(new Set())
  const [expandedTopics, setExpandedTopics] = useState(new Set())
  const [customTopic, setCustomTopic] = useState('')
  const [maxQuestions, setMaxQuestions] = useState(12)
  const [loading, setLoading] = useState(true)
  const [starting, setStarting] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    api.getTopics()
      .then(d => { setTopics(d.topics || {}); setLoading(false) })
      .catch(() =>
        // fallback to flat session list
        api.getSessions()
          .then(d => {
            const flat = { 'All Sessions': d.sessions || [] }
            setTopics(flat)
            setLoading(false)
          })
          .catch(e => { setError(e.message); setLoading(false) })
      )
  }, [])

  function toggleSession(name) {
    setSelectedSessions(cur => {
      const next = new Set(cur)
      next.has(name) ? next.delete(name) : next.add(name)
      return next
    })
  }

  function toggleTopic(topic, sessions, allSelected) {
    setSelectedSessions(cur => {
      const next = new Set(cur)
      if (allSelected) {
        sessions.forEach(s => next.delete(s))
      } else {
        sessions.forEach(s => next.add(s))
      }
      return next
    })
  }

  function toggleExpand(topic) {
    setExpandedTopics(cur => {
      const next = new Set(cur)
      next.has(topic) ? next.delete(topic) : next.add(topic)
      return next
    })
  }

  async function handleStart() {
    const names = [...selectedSessions]
    if (customTopic.trim()) names.push(customTopic.trim())
    if (!names.length) return
    setStarting(true)
    setError(null)
    try {
      const { run_id } = await api.generate(names, maxQuestions)
      navigate(`/progress/${run_id}`)
    } catch (e) {
      setError(e.message)
      setStarting(false)
    }
  }

  const totalSelected = selectedSessions.size + (customTopic.trim() ? 1 : 0)
  const canStart = totalSelected > 0 && !starting

  return (
    <div className="page">
      <div className="hero">
        <h1 className="hero-title">
          Generate <span className="accent">interview questions</span><br />
          from your sessions
        </h1>
        <p className="hero-sub">
          Select a topic or individual sessions. The 4-agent pipeline retrieves real company
          interview questions, validates relevance, and prepares a curated set for your review.
        </p>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      <div className="selector-grid">
        <section className="card selector-card">
          <h2 className="card-title">Select by Topic</h2>
          {loading ? (
            <p className="muted">Loading…</p>
          ) : Object.keys(topics).length === 0 ? (
            <p className="muted">No topics found.</p>
          ) : (
            <ul className="topic-list">
              {Object.entries(topics).map(([topic, sessions]) => (
                <TopicRow
                  key={topic}
                  topic={topic}
                  sessions={sessions}
                  selectedSessions={selectedSessions}
                  onToggleTopic={toggleTopic}
                  onToggleSession={toggleSession}
                  expanded={expandedTopics.has(topic)}
                  onToggleExpand={toggleExpand}
                />
              ))}
            </ul>
          )}
          <div className="custom-topic">
            <label className="field-label">Or enter a custom topic</label>
            <input
              type="text"
              className="text-input"
              placeholder="e.g., Retrieval-Augmented Generation"
              value={customTopic}
              onChange={e => setCustomTopic(e.target.value)}
            />
          </div>
        </section>

        <section className="card config-card">
          <h2 className="card-title">Configuration</h2>
          <div className="config-field">
            <label className="field-label">Max Questions: <strong>{maxQuestions}</strong></label>
            <input
              type="range" min={5} max={15} value={maxQuestions}
              onChange={e => setMaxQuestions(parseInt(e.target.value))}
              className="range-input"
            />
            <div className="range-labels"><span>5</span><span>15</span></div>
          </div>

          <div className="selected-preview">
            <p className="field-label">Selected ({totalSelected})</p>
            {totalSelected === 0 ? (
              <p className="muted">No sessions selected</p>
            ) : (
              <ul className="selected-list">
                {[...selectedSessions].map(s => (
                  <li key={s}>
                    <span className="chip" title={s}>{s}</span>
                  </li>
                ))}
                {customTopic.trim() && (
                  <li><span className="chip chip-custom">{customTopic.trim()}</span></li>
                )}
              </ul>
            )}
          </div>

          <div className="pipeline-info">
            <h3 className="info-title">Pipeline (4 agents)</h3>
            <ol className="pipeline-steps">
              <li>🔍 <strong>Understanding</strong> — KP mapping + search queries</li>
              <li>📚 <strong>Retrieval</strong> — Bank + GitHub + Tavily</li>
              <li>✅ <strong>Validation</strong> — Relevance filter + dedup</li>
              <li>⚖️ <strong>Evaluation</strong> — Balance + coverage + submit</li>
            </ol>
          </div>

          <button
            className="btn btn-primary btn-full"
            disabled={!canStart}
            onClick={handleStart}
          >
            {starting ? 'Starting pipeline…' : 'Generate Interview Questions ▸'}
          </button>
        </section>
      </div>
    </div>
  )
}
