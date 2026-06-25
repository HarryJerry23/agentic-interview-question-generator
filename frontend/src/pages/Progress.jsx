import { useParams, useNavigate } from 'react-router-dom'
import { useAgentRun } from '../hooks/useAgentRun.js'
import PipelineStepper from '../components/PipelineStepper.jsx'

const TOOL_ICONS = {
  understand_session: '🔍',
  search_question_bank: '📖',
  search_github_questions: '🐙',
  search_web_questions: '🌐',
  validate_relevance: '🎯',
  deduplicate_questions: '🔄',
  check_difficulty_balance: '⚖️',
  check_outcome_coverage: '📊',
  generate_expected_answers: '💡',
  generate_coding_questions: '💻',
  remove_question: '🗑️',
  submit_question_set: '📤',
  critique: '🔬',
}

function ToolEvent({ ev }) {
  const icon = TOOL_ICONS[ev.step] || '🔧'
  const isError = ev.status === 'error' || ev.status === 'warning'
  const isDone = ev.status === 'done'
  return (
    <div className={`tool-event ${isDone ? 'te-done' : isError ? 'te-error' : 'te-running'}`}>
      <span className="te-icon">{icon}</span>
      <span className="te-name">{ev.step}</span>
      {ev.status === 'running' && <span className="te-spinner">…</span>}
      {isDone && <span className="te-check">✓</span>}
      {isError && <span className="te-warn">⚠</span>}
      {ev.detail && <span className="te-detail">{ev.detail}</span>}
    </div>
  )
}

export default function Progress() {
  const { runId } = useParams()
  const navigate = useNavigate()
  const { phaseStatus, toolEvents, status, questionCount } = useAgentRun(runId)

  const isDone = status === 'done'
  const isError = status === 'error'

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">
          {isDone ? '✅ Pipeline Complete' : isError ? '❌ Pipeline Error' : '⚙️ Generating Questions…'}
        </h1>
        <p className="page-sub">Run: <code>{runId?.slice(0, 8)}…</code></p>
      </div>

      <PipelineStepper phaseStatus={phaseStatus} />

      {isDone && (
        <div className="alert alert-success">
          {questionCount > 0
            ? `${questionCount} questions ready for review.`
            : 'Pipeline completed — review your questions below.'}
          {' '}
          <button className="btn btn-primary" onClick={() => navigate(`/review/${runId}`)}>
            Review Questions ▸
          </button>
        </div>
      )}

      {isError && (
        <div className="alert alert-error">
          Pipeline encountered an error. Check the log below.
          {' '}
          <button className="btn btn-ghost" onClick={() => navigate('/')}>
            ← Start over
          </button>
        </div>
      )}

      <section className="card log-card">
        <h2 className="card-title">Tool Call Log</h2>
        {toolEvents.length === 0 ? (
          <p className="muted">Waiting for pipeline to start…</p>
        ) : (
          <div className="tool-log">
            {toolEvents.map((ev, i) => (
              <ToolEvent key={i} ev={ev} />
            ))}
          </div>
        )}
      </section>
    </div>
  )
}
