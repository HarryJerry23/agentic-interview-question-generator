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

const FLOW_NODES = [
  { key: 'understanding', cls: 'fn-ac-1',     num: 'AGENT 01', label: 'Understanding', phase: 'understanding', tools: ['understand_session'] },
  { key: 'retrieval',     cls: 'fn-ac-2',     num: 'AGENT 02', label: 'Retrieval',     phase: 'retrieval',     tools: ['search_bank', 'search_github', 'search_web'] },
  { key: 'validation',    cls: 'fn-ac-3',     num: 'AGENT 03', label: 'Validation',    phase: 'validation',    tools: ['validate_relevance', 'deduplicate'] },
  { key: 'evaluation',    cls: 'fn-ac-4',     num: 'AGENT 04', label: 'Evaluation',    phase: 'evaluation',    tools: ['check_balance', 'gen_answers', 'submit'] },
  { key: 'gate',          cls: 'fn-ac-gate',  num: 'GATE',     label: 'Quality Gate',  phase: 'critique',      tools: ['critique', 'remove_q'], isGate: true },
  { key: 'review',        cls: 'fn-ac-review', num: 'HUMAN',   label: 'Review',        phase: null,            tools: ['Accept', 'Reject'] },
]

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
  const { phaseStatus, toolEvents, events, status, questionCount, errorDetail, apiUsage } = useAgentRun(runId)

  const isDone = status === 'done'
  const isError = status === 'error'

  // Derive critique status from raw events
  const critiqueEvents = events.filter(e => e.step === 'critique')
  const lastCritique = critiqueEvents[critiqueEvents.length - 1]
  const critiqueStatus = lastCritique
    ? (lastCritique.status === 'done' ? 'done' : 'running')
    : null

  function getNodeStatus(node) {
    if (node.phase === 'critique') return critiqueStatus
    if (!node.phase) return null
    return phaseStatus[node.phase] || null
  }

  // Count critique rounds
  const revisionCount = critiqueEvents.filter(e => e.status === 'done').length

  return (
    <>
      <header className="topbar">
        <div className="topbar-title-group">
          <span className="topbar-title">
            {isDone ? 'Pipeline Complete' : isError ? 'Pipeline Error' : 'Generating Questions…'}
          </span>
          <span className="topbar-sub">Run {runId?.slice(0, 8)}</span>
        </div>
        <PipelineStepper phaseStatus={phaseStatus} critiqueStatus={critiqueStatus} />
      </header>

      {/* Pipeline flowchart */}
      <div className="pipeline-detail">
        <div className="pd-header">
          <span className="pd-title">Pipeline</span>
          <span className="pd-sub">
            1,509 questions indexed
            {apiUsage && ` · ${apiUsage.llm_calls} LLM calls · ${((apiUsage.prompt_tokens + apiUsage.completion_tokens) / 1000).toFixed(1)}K tokens`}
            {apiUsage?.tavily_calls > 0 && ` · ${apiUsage.tavily_calls} Tavily searches`}
          </span>
        </div>
        <div className="pipeline-flow">
          {FLOW_NODES.map((node, i) => {
            const nodeStatus = getNodeStatus(node)
            const isActive = nodeStatus === 'running'
            const isDoneNode = nodeStatus === 'done'
            return (
              <div key={node.key} style={{ display: 'flex', alignItems: 'center', flexShrink: 0 }}>
                <div className={`flow-node ${node.cls}${isActive ? ' flow-node-active' : ''}${isDoneNode ? ' flow-node-done' : ''}`}>
                  <div className="fn-num">{node.num}</div>
                  <div className="fn-name">{node.label}</div>
                  <div className="fn-chips">
                    {node.tools.map(t => <span key={t} className="fn-chip">{t}</span>)}
                  </div>
                  {node.isGate && revisionCount > 0 && (
                    <div className="flow-loop-note">↺ {revisionCount} revision{revisionCount > 1 ? 's' : ''}</div>
                  )}
                </div>
                {i < FLOW_NODES.length - 1 && <span className="flow-arrow">→</span>}
              </div>
            )
          })}
        </div>
      </div>

      {/* Alerts */}
      {isDone && (
        <div className="alert alert-success" style={{ margin: '0 1.25rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
            <span>{questionCount > 0 ? `${questionCount} questions ready for review.` : 'Pipeline completed.'}</span>
            {apiUsage && (
              <span className="muted" style={{ fontSize: '0.78rem' }}>
                {apiUsage.llm_calls} LLM calls · {((apiUsage.prompt_tokens + apiUsage.completion_tokens) / 1000).toFixed(1)}K tokens
                {apiUsage.tavily_calls > 0 && ` · ${apiUsage.tavily_calls} Tavily searches`}
              </span>
            )}
            <button className="btn btn-primary" onClick={() => navigate(`/review/${runId}`)}>
              Review Questions ▸
            </button>
          </div>
        </div>
      )}
      {isError && (
        <div className="alert alert-error" style={{ margin: '0 1.25rem' }}>
          <div>Pipeline encountered an error.{' '}
            <button className="btn btn-ghost" onClick={() => navigate('/')}>← Start over</button>
          </div>
          {errorDetail && (
            <div style={{ marginTop: '0.4rem', fontSize: '0.78rem', opacity: 0.75, fontFamily: 'monospace', wordBreak: 'break-word' }}>
              {errorDetail}
            </div>
          )}
        </div>
      )}

      {/* Tool log */}
      <div className="page-content">
        <section className="card log-card">
          <h2 className="card-title">Tool Call Log</h2>
          {toolEvents.length === 0 ? (
            <p className="muted">Waiting for pipeline to start…</p>
          ) : (
            <div className="tool-log">
              {toolEvents.map((ev, i) => <ToolEvent key={i} ev={ev} />)}
            </div>
          )}
        </section>
      </div>
    </>
  )
}
