import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { api } from '../lib/api.js'
import PipelineStepper from '../components/PipelineStepper.jsx'

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

function CompactQuestion({
  id, content, title, difficulty,
  company, role, topic, subTopic, language, source, sourceUrl,
  snippet, decision, onDecide, index,
}) {
  const [open, setOpen] = useState(false)
  const isCoding = !!title
  const diff = difficulty || 'Medium'
  const diffClass = diff === 'Easy' ? 'd-easy' : diff === 'Hard' ? 'd-hard' : 'd-medium'

  return (
    <div className={`cq-row${decision === 'accepted' ? ' cq-row-accepted' : decision === 'rejected' ? ' cq-row-rejected' : ''}`}>
      <div className="cq-main" onClick={() => setOpen(o => !o)}>
        <span className="cq-num">Q{index + 1}</span>
        <span className="cq-text">{isCoding ? title : content}</span>
        <div className="cq-tags">
          {company && <span className="cq-company" title={company}>{company}</span>}
          <span className={`cq-diff ${diffClass}`}>{diff}</span>
        </div>
        <div className="cq-btns" onClick={e => e.stopPropagation()}>
          <button
            className={`cq-btn cq-accept${decision === 'accepted' ? ' active' : ''}`}
            onClick={() => onDecide(id, 'accepted')}
          >✓</button>
          <button
            className={`cq-btn cq-reject${decision === 'rejected' ? ' active' : ''}`}
            onClick={() => onDecide(id, 'rejected')}
          >✕</button>
        </div>
      </div>

      {open && (
        <div className="cq-detail">
          {isCoding && content && (
            <p style={{ fontSize: '0.82rem', color: '#c9d1d9', marginBottom: '0.5rem' }}>{content}</p>
          )}
          {snippet?.code_content && (
            <pre className="q-code-pre">{snippet.code_content}</pre>
          )}
          {sourceUrl && (
            <a
              href={sourceUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="cq-resource-link"
              onClick={e => e.stopPropagation()}
            >
              ↗ Verify source
            </a>
          )}
          <div className="cq-meta-tags">
            {company  && <span className="cq-tag cq-tag-company">{company}</span>}
            {role     && <span className="cq-tag cq-tag-role">{role}</span>}
            {topic    && <span className="cq-tag cq-tag-topic">{topic}</span>}
            {subTopic && <span className="cq-tag cq-tag-subtopic">{subTopic}</span>}
            {language && <span className="cq-tag cq-tag-lang">{language}</span>}
            {source   && <span className="cq-tag cq-tag-source">{source}</span>}
          </div>
        </div>
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
  const [sheetUrl, setSheetUrl] = useState(null)
  const [sheetError, setSheetError] = useState(null)

  useEffect(() => {
    api.getResult(runId)
      .then(d => { setResult(d); setLoading(false) })
      .catch(e => { setError(e.message); setLoading(false) })
  }, [runId])

  function onDecide(qid, status) {
    setDecisions(cur => ({ ...cur, [qid]: { status } }))
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
      if (!d || d.status === 'accepted') acceptedIds.push(id)
      else rejectedFeedback[id] = ''
    }
    setSubmitting(true)
    try {
      const resp = await api.approve(runId, acceptedIds, rejectedFeedback, 'approve')
      if (resp.sheet_url) setSheetUrl(resp.sheet_url)
      if (resp.sheet_error) setSheetError(resp.sheet_error)
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

  if (loading) return (
    <>
      <header className="topbar">
        <div className="topbar-title-group">
          <span className="topbar-title">Review Questions</span>
        </div>
        <PipelineStepper completedUntil="gate" activeStage="review" />
      </header>
      <div className="page-content"><p className="muted loading">Loading results…</p></div>
    </>
  )

  if (error && !result) return (
    <>
      <header className="topbar">
        <div className="topbar-title-group"><span className="topbar-title">Review Questions</span></div>
      </header>
      <div className="page-content"><div className="alert alert-error">{error}</div></div>
    </>
  )

  if (!result) return null

  const questions = result.output?.question_details || []
  const codingQs = result.output?.coding_questions || []
  const snippets = result.output?.code_snippets || []
  const snippetMap = Object.fromEntries(snippets.map(s => [s.code_id, s]))
  const total = questions.length + codingQs.length
  const rejectedCount = Object.values(decisions).filter(d => d.status === 'rejected').length
  const approvedCount = total - rejectedCount

  if (done) {
    return (
      <>
        <header className="topbar">
          <div className="topbar-title-group"><span className="topbar-title">Export Complete</span></div>
          <PipelineStepper completedUntil="export" />
        </header>
        <div className="page-content">
          <div className="done-banner">
            <h1>Approved!</h1>
            {sheetUrl ? (
              <>
                <p>{approvedCount} question{approvedCount !== 1 ? 's' : ''} exported to Google Sheets.</p>
                <a href={sheetUrl} target="_blank" rel="noopener noreferrer" className="btn btn-primary" style={{ marginBottom: '0.75rem', display: 'inline-block' }}>
                  Open Google Sheet
                </a>
              </>
            ) : sheetError ? (
              <>
                <p>{approvedCount} question{approvedCount !== 1 ? 's' : ''} approved (saved locally).</p>
                <p style={{ color: '#f85149', fontSize: '0.85rem' }}>Sheets export failed: {sheetError}</p>
              </>
            ) : (
              <p>{approvedCount} question{approvedCount !== 1 ? 's' : ''} approved and saved.</p>
            )}
            <button className="btn btn-primary" onClick={() => navigate('/')}>Generate more</button>
          </div>
        </div>
      </>
    )
  }

  const sessionName = result.context?.session_name || 'Session'
  const sessionType = result.context?.session_type

  return (
    <>
      <header className="topbar">
        <div className="topbar-title-group">
          <span className="topbar-title">Review Questions</span>
          <span className="topbar-sub">{sessionName}{sessionType ? ` · ${sessionType}` : ''}</span>
        </div>
        <PipelineStepper completedUntil="gate" activeStage="review" />
      </header>

      {/* Action banner */}
      <div className="action-banner">
        <div className="ab-text">
          <span className="ab-title">Action needed — Review before publishing to portal</span>
          <span className="ab-sub">
            {total} questions for <strong style={{ color: '#c9d1d9' }}>{sessionName}</strong>
            {' · '}{questions.length} theory · {codingQs.length} coding
            {result.report && ` · Quality ${Math.round(result.report.composite_score * 100)}/100`}
            {result.report?.loops_used > 0 && ` · ${result.report.loops_used} revision(s)`}
          </span>
        </div>
        <div className="ab-btns">
          <button className="btn btn-reject-all" disabled={submitting} onClick={handleReject}>
            ↺ Reject &amp; Regenerate
          </button>
          <button className="btn btn-primary" disabled={submitting} onClick={handleApprove}>
            {submitting ? 'Exporting…' : `↑ Export to Sheets (${approvedCount})`}
          </button>
        </div>
      </div>

      {error && <div className="alert alert-error" style={{ margin: '0 1.25rem' }}>{error}</div>}

      {/* Quality bar */}
      <div style={{ padding: '0.75rem 1.25rem 0' }}>
        <QualityBar report={result.report} />
      </div>

      {/* Learning outcomes */}
      {result.context?.learning_outcomes?.length > 0 && (
        <details className="card outcomes-card" style={{ margin: '0.75rem 1.25rem 0' }}>
          <summary>
            <strong>Learning Outcomes</strong> ({result.context.learning_outcomes.length})
          </summary>
          <ul className="outcome-list">
            {result.context.learning_outcomes.map((o, i) => <li key={i}>{o}</li>)}
          </ul>
        </details>
      )}

      {/* 2-column compact question sets */}
      <div className="q-sets-grid">
        <div className="q-set-panel">
          <div className="q-set-head">
            <span className="q-set-title">Theory Questions</span>
            <span className="q-set-badge">{questions.length}</span>
          </div>
          <div className="q-set-body">
            {questions.length === 0 ? (
              <p className="muted" style={{ padding: '1rem' }}>No theory questions.</p>
            ) : (
              questions.map((q, i) => (
                <CompactQuestion
                  key={q.question_id}
                  id={q.question_id}
                  content={q.question || q.content}
                  difficulty={q.difficulty_level || q.difficulty}
                  company={q.asked_in_company}
                  role={q.role}
                  topic={q.topic}
                  subTopic={q.sub_topic}
                  source={q.source}
                  sourceUrl={q.source_url}
                  decision={decisions[q.question_id]?.status}
                  onDecide={onDecide}
                  index={i}
                />
              ))
            )}
          </div>
        </div>

        <div className="q-set-panel">
          <div className="q-set-head">
            <span className="q-set-title">Coding Questions</span>
            <span className="q-set-badge">{codingQs.length}</span>
          </div>
          <div className="q-set-body">
            {codingQs.length === 0 ? (
              <p className="muted" style={{ padding: '1rem' }}>No coding questions.</p>
            ) : (
              codingQs.map((q, i) => (
                <CompactQuestion
                  key={q.id}
                  id={q.id}
                  title={q.title}
                  content={q.problem_statement || q.content}
                  difficulty={q.difficulty}
                  company={q.asked_in_company}
                  topic={q.topic}
                  subTopic={q.sub_topic}
                  language={q.language}
                  source={q.source}
                  sourceUrl={q.source_url}
                  snippet={snippetMap[q.code_id]}
                  decision={decisions[q.id]?.status}
                  onDecide={onDecide}
                  index={i}
                />
              ))
            )}
          </div>
        </div>
      </div>
    </>
  )
}
