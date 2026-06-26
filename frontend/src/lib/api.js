async function j(res) {
  if (res.ok) return res.json()
  let body = {}
  try { body = await res.json() } catch {}
  throw Object.assign(new Error(body.error || res.statusText), { status: res.status })
}

export const api = {
  getSessions: () => fetch('/api/sessions').then(j),
  getTopics: () => fetch('/api/topics').then(j),
  getHistory: () => fetch('/api/history').then(j),

  generate: (sessionNames, maxQuestions) =>
    fetch('/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_names: sessionNames, max_questions: maxQuestions }),
    }).then(j),

  getResult: (runId) => fetch(`/api/result/${runId}`).then(j),

  approve: (runId, acceptedIds, rejectedFeedback, action) =>
    fetch(`/api/approve/${runId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ accepted_ids: acceptedIds, rejected_feedback: rejectedFeedback, action }),
    }).then(j),

  stream: (runId, onEvent) => {
    const es = new EventSource(`/api/stream/${runId}`)
    es.onmessage = (e) => {
      try { onEvent(JSON.parse(e.data)) } catch {}
    }
    es.onerror = () => onEvent({ step: 'stream_error', status: 'error', detail: 'Stream disconnected' })
    return es
  },
}
