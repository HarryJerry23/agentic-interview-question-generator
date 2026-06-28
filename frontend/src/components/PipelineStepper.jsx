const STAGE_DEFS = [
  { key: 'select',        label: 'Select',       phaseKey: null },
  { key: 'understanding', label: 'Understand',   phaseKey: 'understanding' },
  { key: 'retrieval',     label: 'Retrieve',     phaseKey: 'retrieval' },
  { key: 'validation',    label: 'Validate',     phaseKey: 'validation' },
  { key: 'evaluation',    label: 'Evaluate',     phaseKey: 'evaluation' },
  { key: 'gate',          label: 'Quality Gate', phaseKey: null },
  { key: 'review',        label: 'Review',       phaseKey: null },
  { key: 'export',        label: 'Export',       phaseKey: null },
]

// phaseStatus: { understanding: 'running'|'done', ... } from SSE
// critiqueStatus: 'running'|'done'|null for the quality gate step
// completedUntil: stage key — everything up to+including this key is 'done'
// activeStage: stage key shown as 'active' (used alongside completedUntil)
export default function PipelineStepper({
  phaseStatus = {},
  critiqueStatus = null,
  activeStage = null,
  completedUntil = null,
}) {
  const completedIdx = completedUntil
    ? STAGE_DEFS.findIndex(s => s.key === completedUntil)
    : -1

  function getStatus(stage, i) {
    if (completedUntil) {
      if (i <= completedIdx) return 'done'
      if (stage.key === activeStage) return 'active'
      return 'pending'
    }
    // Progress page: 'select' always done once we're here
    if (stage.key === 'select') return 'done'
    if (stage.phaseKey) {
      const ps = phaseStatus[stage.phaseKey]
      if (ps === 'done') return 'done'
      if (ps === 'running') return 'active'
    }
    if (stage.key === 'gate') {
      if (critiqueStatus === 'done') return 'done'
      if (critiqueStatus === 'running') return 'active'
      return 'pending'
    }
    return 'pending'
  }

  return (
    <div className="topbar-stepper">
      {STAGE_DEFS.map((stage, i) => {
        const status = getStatus(stage, i)
        const gateActive = stage.key === 'gate' && status === 'active'
        return (
          <div key={stage.key} className="ts-wrap">
            <div className={`ts-step ts-${status}${gateActive ? ' ts-gate-active' : ''}`}>
              <div className="ts-circle">
                {status === 'done' ? '✓' : status === 'active' ? '▶' : String(i + 1)}
              </div>
              <span className="ts-label">{stage.label}</span>
            </div>
            {i < STAGE_DEFS.length - 1 && <div className="ts-connector" />}
          </div>
        )
      })}
    </div>
  )
}
