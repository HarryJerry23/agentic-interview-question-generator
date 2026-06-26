import { useState } from 'react'

export default function CodingCard({ question, snippet, decision, onDecide }) {
  const qid = question.id
  const isAccepted = decision === 'accepted'
  const isRejected = decision === 'rejected'

  return (
    <div className={`q-card q-coding-card ${isAccepted ? 'q-accepted' : isRejected ? 'q-rejected' : ''}`}>
      <div className="q-meta">
        <span className="q-badge q-coding-tag">💻 Coding</span>
        <span className="q-badge q-diff">{question.difficulty || 'Medium'}</span>
        <span className="q-badge q-lang">{question.language}</span>
        {question.topic && <span className="q-badge q-topic">{question.topic}</span>}
      </div>
      <h3 className="q-title">{question.title}</h3>
      <p className="q-content">{question.content}</p>
      {snippet?.code_content && (
        <details className="q-code" open>
          <summary>Starter code ({snippet.language})</summary>
          <pre><code>{snippet.code_content}</code></pre>
        </details>
      )}
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
          onClick={() => onDecide(qid, 'rejected')}
        >
          ✕ Reject
        </button>
      </div>
    </div>
  )
}
