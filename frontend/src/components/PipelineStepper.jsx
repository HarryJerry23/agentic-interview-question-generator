const STAGES = [
  { key: 'understanding', label: 'Understanding Session', icon: '🔍' },
  { key: 'retrieval',     label: 'Retrieving Questions', icon: '📚' },
  { key: 'validation',    label: 'Validating Questions', icon: '✅' },
  { key: 'evaluation',    label: 'Evaluating & Finalizing', icon: '⚖️' },
]

export default function PipelineStepper({ phaseStatus }) {
  return (
    <div className="stepper">
      {STAGES.map((stage, i) => {
        const s = phaseStatus[stage.key]
        const cls = s === 'done' ? 'step-done' : s === 'running' ? 'step-running' : 'step-pending'
        return (
          <div key={stage.key} className={`step ${cls}`}>
            <div className="step-dot">
              {s === 'done' ? '✓' : s === 'running' ? '…' : i + 1}
            </div>
            <div className="step-body">
              <span className="step-icon">{stage.icon}</span>
              <span className="step-label">{stage.label}</span>
            </div>
          </div>
        )
      })}
    </div>
  )
}
