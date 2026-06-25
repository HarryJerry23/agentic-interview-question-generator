import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { api } from '../lib/api.js'
import QuestionCard from '../components/QuestionCard.jsx'
import CodingCard from '../components/CodingCard.jsx'

function QualityBar({ report }) {
  if (!report) return null
  const score = Math.round(report.composite_score * 100)
  const isPassing = report.pass_fail === 'pass'
  return (
    <div className={`quality-bar ${isPassing ? 'qb-pass' : 'qb-fail'}`}>
      <span className="qb-badge">{isPassing ? '✅ Pass' : '⚠️ Below threshold'}</span>
      <span className="qb-score">Score: {score}/100</span>
      <div className="qb-metrics">
        {Object.entries(report.metric_scores || {}).map(([k, v]) => (
          <span key={k} className="qb-metric">
            {k.replace(/_/g, ' ')}: {Math.round(v * 100)}
          </span>
        ))}
      </div>
      {report.loops_used > 0 && (
        <span className="qb-loops">{report.loops_used} revision round(s)</span>
      )}
    </div>
  )
}

export default function Review() {
  const { runId } = useParams()
  const navigate = useNavigate()
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [decisions, setDecisions] = useState({})
  const [submitting, setSubmitting] = useState(false)
  const [done, setDone] = useState(false)

  useEffect(() => {
    api.getResult(runId)
      .then(d => { setResult(d); setLoading(false) })
      .catch(e => { setError(e.message); setLoading(false) })
  }, [runId])

  function onDecide(qid, status, feedback = '') {
    setDecisions(cur => ({ ...cur, [qid]: { status, feedback } }))
  }

  async function handleApprove() {
    const acceptedIds = []
    const rejectedFeedback = {}
    const allIds = [
      ...(result.output?.question_details || []).map(q => q.question_id),
      ...(result.output?.coding_questions || []).map(q => q.id),
    ]
    for (const id of allIds) {
      const d = decisions[id]
      if (!d || d.status === 'accepted') {
        acceptedIds.push(id)
      } else {
        rejectedFeedback[id] = d.feedback || ''
      }
    }

    setSubmitting(true)
    try {
      await api.approve(runId, acceptedIds, rejectedFeedback, 'approve')
      setDone(true)
    } catch (e) {
      setError(e.message)
    } finally {
      setSubmitting(false)
    }
  }

  async function handleReject() {
    setSubmitting(true)
    try {
      const { run_id } = await api.approve(runId, [], {}, 'reject')
      navigate(`/progress/${run_id}`)
    } catch (e) {
      setError(e.message)
      setSubmitting(false)
    }
  }

  if (loading) return <div className="page"><p className="muted loading">Loading results…</p></div>
  if (error) return <div className="page"><div className="alert alert-error">{error}</div></div>
  if (!result) return null

  const questions = result.output?.question_details || []
  const codingQs = result.output?.coding_questions || []
  const snippets = result.output?.code_snippets || []
  const snippetMap = Object.fromEntries(snippets.map(s => [s.code_id, s]))
  const total = questions.length + codingQs.length

  if (done) {
    const accepted = Object.values(decisions).filter(d => d.status === 'accepted').length
    const approved = total - Object.values(decisions).filter(d => d.status === 'rejected').length
    return (
      <div className="page">
        <div className="done-banner">
          <h1>✅ Approved!</h1>
          <p>{approved} question{approved !== 1 ? 's' : ''} saved successfully.</p>
          <button className="btn btn-primary" onClick={() => navigate('/')}>
            ← Generate more
          </button>
        </div>
      </div>
    )
  }

  const rejectedCount = Object.values(decisions).filter(d => d.status === 'rejected').length

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Review Questions</h1>
          <p className="page-sub">
            {total} questions for <strong>{result.context?.session_name}</strong>
            {result.context?.session_type && ` (${result.context.session_type})`}
          </p>
        </div>
        <div className="review-actions">
          <button className="btn btn-reject-all" disabled={submitting} onClick={handleReject}>
            ↺ Reject &amp; Regenerate
          </button>
          <button className="btn btn-primary" disabled={submitting} onClick={handleApprove}>
            {submitting ? 'Saving…' : `✓ Approve (${total - rejectedCount} questions)`}
          </button>
        </div>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      <QualityBar report={result.report} />

      {result.context?.learning_outcomes?.length > 0 && (
        <details className="card outcomes-card">
          <summary>
            <strong>Learning Outcomes</strong> ({result.context.learning_outcomes.length})
          </summary>
          <ul className="outcome-list">
            {result.context.learning_outcomes.map((o, i) => <li key={i}>{o}</li>)}
          </ul>
        </details>
      )}

      {questions.length > 0 && (
        <section>
          <h2 className="section-title">Theory Questions ({questions.length})</h2>
          <div className="questions-grid">
            {questions.map(q => (
              <QuestionCard
                key={q.question_id}
                question={q}
                decision={decisions[q.question_id]?.status}
                onDecide={onDecide}
              />
            ))}
          </div>
        </section>
      )}

      {codingQs.length > 0 && (
        <section>
          <h2 className="section-title">Coding Questions ({codingQs.length})</h2>
          <div className="questions-grid">
            {codingQs.map(q => (
              <CodingCard
                key={q.id}
                question={q}
                snippet={snippetMap[q.code_id]}
                decision={decisions[q.id]?.status}
                onDecide={onDecide}
              />
            ))}
          </div>
        </section>
      )}

      <div className="review-footer">
        <button className="btn btn-reject-all" disabled={submitting} onClick={handleReject}>
          ↺ Reject &amp; Regenerate
        </button>
        <button className="btn btn-primary btn-lg" disabled={submitting} onClick={handleApprove}>
          {submitting ? 'Saving…' : `✓ Approve ${total - rejectedCount} Questions`}
        </button>
      </div>
    </div>
  )
}
