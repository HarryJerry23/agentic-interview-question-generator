// Last-resort USD→INR rate used only if the API response omits `usd_to_inr` (the backend normally
// supplies a live rate). Single source of truth — don't hardcode this number in components.
export const FALLBACK_USD_INR = 83.5;

// One function per route. Relative /api → Vite proxy → Flask :5000.
async function j(res) {
  if (res.ok) return res.json();
  let body = {};
  try {
    body = await res.json();
  } catch {
    /* non-JSON error */
  }
  throw Object.assign(new Error(body.error || res.statusText), {
    code: body.code,
    status: res.status,
  });
}

export const api = {
  getCourses: () => fetch("/api/content/courses").then(j),
  getSessions: (course) =>
    fetch(`/api/content/sessions?course=${encodeURIComponent(course)}`).then(j),
  getSession: (course, session) =>
    fetch(
      `/api/content/session?course=${encodeURIComponent(course)}&session=${encodeURIComponent(session)}`
    ).then(j),
  uploadSession: (formData) =>
    fetch("/api/content/upload", { method: "POST", body: formData }).then(j),
  getRubric: () => fetch("/api/rubric").then(j),
  // What the system has learned from reviewer feedback → {feedback_rules: [...]} (transparency view).
  getFeedbackRules: () => fetch("/api/feedback-rules").then(j),

  // ── Agent (Feature 3) ──
  // workflow: "classroom_quiz" (default) | "mcq_practice" (Feature 8).
  startRun: (course, session, workflow = "classroom_quiz") =>
    fetch("/api/agent/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ course, session, workflow }),
    }).then(j),
  // Module Quiz (Feature 9): merge several selected sessions; `moduleName` is the run/export identity.
  startModuleQuiz: (course, sessions, moduleName) =>
    fetch("/api/agent/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ course, sessions, module_name: moduleName, workflow: "module_quiz" }),
    }).then(j),
  // Mock Interview (Feature 11): merge several sessions of a topic, harvest REAL interview questions;
  // `topicName` is the run/export identity.
  startMockInterview: (course, sessions, topicName) =>
    fetch("/api/agent/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ course, sessions, topic_name: topicName, workflow: "mock_interview" }),
    }).then(j),
  getRun: (runId) => fetch(`/api/agent/run/${runId}`).then(j),
  // Has this (course, session, workflow) already been generated? → {exists, run_id?, finished_at?, zips} (Feature 6).
  checkExists: (course, session, workflow = "classroom_quiz") =>
    fetch(`/api/agent/exists?course=${encodeURIComponent(course)}&session=${encodeURIComponent(session)}&workflow=${encodeURIComponent(workflow)}`).then(j),
  listRuns: ({ course, session, limit } = {}) => {
    const p = new URLSearchParams();
    if (course) p.set("course", course);
    if (session) p.set("session", session);
    if (limit) p.set("limit", limit);
    const qs = p.toString();
    return fetch(`/api/agent/runs${qs ? "?" + qs : ""}`).then(j);
  },
  resumeRun: (runId, decisions) =>
    fetch(`/api/agent/resume/${runId}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ decisions }),
    }).then(j),
  // Preview an LLM rewrite of one question from reviewer feedback (Feature 6). Returns { improved }.
  improveQuestion: (runId, { question, feedback, gate }) =>
    fetch(`/api/agent/improve/${runId}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, feedback, gate }),
    }).then(j),
  // Direct URL to download a finished run's portal zip for a set (Feature 6).
  downloadUrl: (runId, set) => `/api/agent/download/${runId}?set=${encodeURIComponent(set)}`,
  // Re-drive a stalled run from its last LangGraph checkpoint (Feature 4.1).
  recoverRun: (runId) => fetch(`/api/agent/recover/${runId}`, { method: "POST" }).then(j),
  // Mark a stalled run terminal so it leaves the active list (Feature 5.2).
  dismissRun: (runId) => fetch(`/api/agent/dismiss/${runId}`, { method: "POST" }).then(j),
  // Stop a live run at the next node boundary → status=paused, resumable via recoverRun (Feature 10).
  pauseRun: (runId) => fetch(`/api/agent/pause/${runId}`, { method: "POST" }).then(j),
  // Stop + abandon a run → dismissed (Feature 10); accepts a live run (unlike dismissRun).
  cancelRun: (runId) => fetch(`/api/agent/cancel/${runId}`, { method: "POST" }).then(j),
  // Live OpenRouter balance/usage for the header badge (server-side key; Feature 5.2).
  getCost: () => fetch("/api/agent/cost").then(j),
  // Live progress over Server-Sent Events. Returns the EventSource so the caller can close it.
  streamRun: (runId, onEvent) => {
    const es = new EventSource(`/api/agent/stream/${runId}`);
    es.onmessage = (e) => {
      try {
        onEvent(JSON.parse(e.data));
      } catch {
        /* keepalive / non-JSON */
      }
    };
    return es;
  },
};
