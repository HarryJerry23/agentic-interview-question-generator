import { useEffect, useState, useRef } from 'react'
import { api } from '../lib/api.js'

const PHASES = ['understanding', 'retrieval', 'validation', 'evaluation']

// Derive per-phase status from the event stream
function derivePhaseStatus(events) {
  const status = {}
  for (const ev of events) {
    if (ev.step?.startsWith('phase:')) {
      const phase = ev.step.slice(6)
      status[phase] = ev.status  // 'running' | 'done' | 'error'
    }
  }
  return status
}

// Derive the active phase (the last one that's 'running')
function deriveCurrentPhase(phaseStatus) {
  for (let i = PHASES.length - 1; i >= 0; i--) {
    if (phaseStatus[PHASES[i]] === 'running') return PHASES[i]
  }
  return null
}

export function useAgentRun(runId) {
  const [events, setEvents] = useState([])
  const [status, setStatus] = useState('running')  // running | done | error
  const [questionCount, setQuestionCount] = useState(0)
  const esRef = useRef(null)

  useEffect(() => {
    if (!runId) return
    setEvents([])
    setStatus('running')
    setQuestionCount(0)

    const es = api.stream(runId, (ev) => {
      setEvents((cur) => [...cur, ev])

      if (ev.step === 'complete') {
        setStatus('done')
        // Extract question count from the detail string
        const m = ev.detail?.match(/(\d+) questions/)
        if (m) setQuestionCount(parseInt(m[1]))
      }
      if (ev.step === 'error' || ev.step === 'stream_error') {
        setStatus('error')
      }
    })

    esRef.current = es
    return () => es.close()
  }, [runId])

  const phaseStatus = derivePhaseStatus(events)
  const currentPhase = deriveCurrentPhase(phaseStatus)

  // Tool-level events (not phase markers)
  const toolEvents = events.filter((ev) => ev.step && !ev.step.startsWith('phase:'))

  return {
    events,
    toolEvents,
    phaseStatus,
    currentPhase,
    status,
    questionCount,
  }
}
