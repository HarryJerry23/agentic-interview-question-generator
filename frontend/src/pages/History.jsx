import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../lib/api.js'

function formatDate(ts) {
  if (!ts) return '—'
  try {
    const d = new Date(ts.includes('T') ? ts : ts + 'Z')
    return d.toLocaleDateString('en-IN', {
      day: '2-digit', month: 'short', year: 'numeric',
      hour: '2-digit', minute: '2-digit',
    })
  } catch {
    return ts
  }
}

function ScoreBadge({ score }) {
  if (score == null) return <span style={{ color: '#6b7280' }}>—</span>
  const pct = Math.round(score * 100)
  const cls = pct >= 70 ? 'score-pass' : pct >= 50 ? 'score-mid' : 'score-fail'
  return <span className={`hist-score ${cls}`}>{pct}%</span>
}

function UsageCell({ usage }) {
  if (!usage || !usage.llm_calls) return <span style={{ color: '#6b7280' }}>—</span>
  const tokens = ((usage.prompt_tokens || 0) + (usage.completion_tokens || 0))
  const tokenStr = tokens >= 1000 ? `${(tokens / 1000).toFixed(1)}K` : tokens
  return (
    <span className="hist-usage">
      {usage.llm_calls} LLM · {tokenStr} tok
      {usage.tavily_calls > 0 && ` · ${usage.tavily_calls} Tavily`}
    </span>
  )
}

export default function History() {
  const navigate = useNavigate()
  const [runs, setRuns] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.getHistory()
      .then(d => setRuns(d.runs || []))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const approvedCount = runs.filter(r => r.approved).length

  return (
    <>
      <header className="topbar">
        <div className="topbar-title-group">
          <span className="topbar-title">Run History</span>
          <span className="topbar-sub">
            {runs.length} run{runs.length !== 1 ? 's' : ''}
            {approvedCount > 0 && ` · ${approvedCount} approved`}
          </span>
        </div>
        <button className="btn btn-ghost btn-sm" onClick={() => navigate('/')}>← Home</button>
      </header>

      <div className="page-content">
        <section className="card">
          {loading ? (
            <p className="muted">Loading history…</p>
          ) : runs.length === 0 ? (
            <div className="hist-empty">
              No runs yet — generate your first question set from the sidebar.
            </div>
          ) : (
            <div className="hist-table-wrap">
              <table className="hist-table">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Topic</th>
                    <th>Sessions</th>
                    <th style={{ textAlign: 'right' }}>Questions</th>
                    <th>Score</th>
                    <th>API Usage</th>
                    <th>Status</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {runs.map(run => (
                    <tr
                      key={run.run_id}
                      className="hist-row"
                      onClick={() => navigate(`/review/${run.run_id}`)}
                    >
                      <td className="hist-date">{formatDate(run.created_at)}</td>
                      <td className="hist-session" title={run.topic || ''}>{run.topic || '—'}</td>
                      <td className="hist-session" title={run.session_name}>{run.session_name}</td>
                      <td className="hist-count">{run.question_count ?? '—'}</td>
                      <td><ScoreBadge score={run.composite_score} /></td>
                      <td><UsageCell usage={run.api_usage} /></td>
                      <td>
                        <span className={`hist-status ${run.approved ? 'hist-approved' : 'hist-pending'}`}>
                          {run.approved ? 'Approved' : 'In Memory'}
                        </span>
                      </td>
                      <td>
                        <button
                          className="btn btn-ghost btn-sm"
                          onClick={e => { e.stopPropagation(); navigate(`/review/${run.run_id}`) }}
                        >
                          View ▸
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </div>
    </>
  )
}
