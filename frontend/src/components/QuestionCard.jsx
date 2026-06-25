import { useState } from 'react'

export default function QuestionCard({ question, decision, onDecide }) {
  const [feedbackOpen, setFeedbackOpen] = useState(false)
  const [feedback, setFeedback] = useState('')
  const qid = question.question_id
  const isAccepted = decision === 'accepted'
  const isRejected = decision === 'rejected'

  return (
    <div className={`q-card ${isAccepted ? 'q-accepted' : isRejected ? 'q-rejected' : ''}`}>
      <div className="q-meta">
        <span className="q-badge q-diff">{question.difficulty || 'Medium'}</span>
        {question.asked_in_company && (
          <span className="q-badge q-company">🏢 {question.asked_in_company}</span>
        )}
        <span className="q-badge q-source">{question.source}</span>
        {question.topic && <span className="q-badge q-topic">{question.topic}</span>}
      </div>
      <p className="q-content">{question.content}</p>
      {question.expected_answer && (
        <details className="q-answer">
          <summary>Expected answer</summary>
          <pre>{question.expected_answer}</pre>
        </details>
      )}
      <div className="q-actions">
        <button
          className={`btn btn-sm ${isAccepted ? 'btn-accept active' : 'btn-accept'}`}
          onClick={() => onDecide(qid, 'accepted')}
        >
          ✓ Accept
        </button>
        <button
          className={`btn btn-sm ${isRejected ? 'btn-reject active' : 'btn-reject'}`}
          onClick={() => { onDecide(qid, 'rejected'); setFeedbackOpen(true) }}
        >
          ✕ Reject
        </button>
        {isRejected && (
          <button className="btn btn-sm btn-ghost" onClick={() => setFeedbackOpen(f => !f)}>
            + Feedback
          </button>
        )}
      </div>
      {isRejected && feedbackOpen && (
        <textarea
          className="q-feedback"
          placeholder="Why reject? (optional)"
          value={feedback}
          onChange={(e) => { setFeedback(e.target.value); onDecide(qid, 'rejected', e.target.value) }}
        />
      )}
    </div>
  )
}
