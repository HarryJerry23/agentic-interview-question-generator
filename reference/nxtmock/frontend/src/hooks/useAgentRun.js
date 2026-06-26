import { useEffect, useRef, useState, useCallback } from "react";
import { api } from "../lib/api.js";
import { derivePipeline } from "../lib/pipelineState.js";

// Subscribes to a run's SSE stream and accumulates state for the run view:
//   events[]            — raw node events (pipeline graph + stepper)
//   sets {set_a,set_b}  — generation questions (from `question` + `set_done`)
//   gate                — "generation" | "rubric" (which gate is open)
//   rubricCards[]       — scored cards for the rubric gate (from `awaiting_human`)
//   phase/inRubric/now  — derived pipeline state (shared with the stepper/graph)
//   live                — a driver thread is attached on the server (else the run is stalled)
//   status              — running | awaiting_human | done | error
//   resume(decisions)   — apply gate decisions; recover() — re-drive a stalled run from its checkpoint
export function useAgentRun(runId) {
  const [events, setEvents] = useState([]);
  const [sets, setSets] = useState({});
  const [gate, setGate] = useState("generation");
  const [rubricCards, setRubricCards] = useState([]);
  const [criticScores, setCriticScores] = useState({}); // {qid: {band, points, max_points}} — live during scoring
  const [scoringQuestions, setScoringQuestions] = useState([]); // accepted set being scored (from `collected`)
  const [variantCards, setVariantCards] = useState([]);         // variants gate cards (from `awaiting_human`)
  const [variantScores, setVariantScores] = useState({});       // {variant_qid: {band, points, max_points}} live
  const [variantsByBase, setVariantsByBase] = useState({});     // {base_key: [variant, ...]} — live during generation
  const [perSetVariantScores, setPerSetVariantScores] = useState({}); // {set_label: {band, ...}}
  const [variantBases, setVariantBases] = useState([]);         // [{key, question_text, concept, set_label}]
  const [result, setResult] = useState(null);                   // terminal snapshot for the done summary
  const [awaitingHuman, setAwaitingHuman] = useState(false);
  const [status, setStatus] = useState("running");
  const [workflow, setWorkflow] = useState("");                 // "" until resolved → avoids a classroom-lane flash on reload of an interview run
  const [interviewMd, setInterviewMd] = useState("");           // Mock Interview md table (Feature 11)
  const [interviewCount, setInterviewCount] = useState(0);
  const [interviewQueue, setInterviewQueue] = useState([]);     // under-evidenced rows for the review gate (P3)
  const [interviewPublished, setInterviewPublished] = useState([]);  // auto-published rows (with companies), shown read-only at the gate
  const [interviewOutcomes, setInterviewOutcomes] = useState([]);    // extracted outcomes (transparency panel, P7)
  const [interviewPerSession, setInterviewPerSession] = useState([]);  // [{title, n}] per-session outcome coverage
  const [live, setLive] = useState(true);
  const [stopping, setStopping] = useState(false);              // reviewer pause/cancel in flight (Feature 10)
  const esRef = useRef(null);
  const recoveredRef = useRef(false);

  const openStream = useCallback((rid) => {
    return api.streamRun(rid, (ev) => {
      if (ev.node === "stream") return; // keepalive / done sentinel
      setEvents((cur) => [...cur, ev]);
      if (ev.node === "split") {
        // Seed both columns the moment the split lands → topics are visible immediately (no gap).
        const p = ev.payload || {};
        setSets((cur) => ({
          set_a: cur.set_a || { set: "set_a", topics: p.set_a_topics || [], questions: [] },
          set_b: cur.set_b || { set: "set_b", topics: p.set_b_topics || [], questions: [] },
        }));
      } else if (ev.node === "plan") {
        const { set, outcomes } = ev.payload;
        setSets((cur) => ({ ...cur, [set]: { ...(cur[set] || { set, questions: [] }), outcomes } }));
      } else if (ev.node === "question") {
        const { set, question } = ev.payload;
        setSets((cur) => {
          const prev = cur[set] || { set, questions: [] };
          if (prev.done) return cur;
          return { ...cur, [set]: { ...prev, questions: [...prev.questions, question] } };
        });
      } else if (ev.node === "set_done" || ev.node === "pool_done") {
        // pool_done is the practice (Feature 8) analogue of set_done — same shape, keyed "pool".
        setSets((cur) => ({ ...cur, [ev.payload.set]: { ...ev.payload, done: true } }));
      } else if (ev.node === "collected") {
        if (Array.isArray(ev.payload.questions)) setScoringQuestions(ev.payload.questions);
      } else if (ev.node === "critic") {
        const { qid, band, points, max_points } = ev.payload;
        if (qid) setCriticScores((cur) => ({ ...cur, [qid]: { band, points, max_points } }));
      } else if (ev.node === "variant_bases") {
        if (Array.isArray(ev.payload.bases)) setVariantBases(ev.payload.bases);
      } else if (ev.node === "variant") {
        // Slot each streamed variant under its base question → live base→variants grouping.
        const { base, variant } = ev.payload;
        setVariantsByBase((cur) => {
          const prev = cur[base] || [];
          if (prev.some((v) => v.qid === variant.qid)) return cur;
          return { ...cur, [base]: [...prev, variant] };
        });
      } else if (ev.node === "outcomes") {
        // Mock Interview (Feature 11/P7): extracted outcomes + per-session coverage (transparency panel).
        if (Array.isArray(ev.payload.outcomes)) setInterviewOutcomes(ev.payload.outcomes);
        if (Array.isArray(ev.payload.per_session)) setInterviewPerSession(ev.payload.per_session);
      } else if (ev.node === "interview_export") {
        // Mock Interview (Feature 11): the harvested md table is carried on the export event.
        if (typeof ev.payload.md === "string") setInterviewMd(ev.payload.md);
        if (typeof ev.payload.count === "number") setInterviewCount(ev.payload.count);
      } else if (ev.node === "variant_critic") {
        const { qid, band, points, max_points } = ev.payload;
        if (qid) setVariantScores((cur) => ({ ...cur, [qid]: { band, points, max_points } }));
      } else if (ev.node === "awaiting_human") {
        const g = ev.payload.gate || "generation";
        setGate(g);
        if (ev.payload.workflow) setWorkflow(ev.payload.workflow);
        if (g === "interview" && Array.isArray(ev.payload.cards)) setInterviewQueue(ev.payload.cards);
        if (g === "interview" && Array.isArray(ev.payload.published)) setInterviewPublished(ev.payload.published);
        if (g === "rubric" && Array.isArray(ev.payload.cards)) setRubricCards(ev.payload.cards);
        if (g === "variants") {
          if (Array.isArray(ev.payload.cards)) setVariantCards(ev.payload.cards);
          if (Array.isArray(ev.payload.bases)) setVariantBases(ev.payload.bases);
          if (ev.payload.set_scores) setPerSetVariantScores(ev.payload.set_scores);
        }
        setAwaitingHuman(true);
        setStatus("awaiting_human");
        setLive(true);
      } else if (ev.node === "finalize" || ev.node === "export") {
        setAwaitingHuman(false);   // a phase resumed past its gate → no action pending
      } else if (ev.node === "complete") {
        setStatus("done");
        setAwaitingHuman(false);   // the run is finished — never leave a gate banner up (item 1 fix)
        setStopping(false);
        api.getRun(rid).then(setResult).catch(() => {});   // fetch the final snapshot (cost, summary)
      } else if (ev.node === "paused") {         // reviewer pause landed (Feature 10) — resumable
        setStatus("paused"); setLive(false); setAwaitingHuman(false); setStopping(false);
      } else if (ev.node === "cancelled") {      // reviewer cancel landed (Feature 10) — abandoned
        setStatus("dismissed"); setLive(false); setAwaitingHuman(false); setStopping(false);
      } else if (ev.node === "error") {
        setStatus("error");
        setAwaitingHuman(false);
        setStopping(false);
      }
    });
  }, []);

  useEffect(() => {
    if (!runId) return;
    setEvents([]); setSets({}); setGate("generation"); setRubricCards([]);
    setCriticScores({}); setScoringQuestions([]);
    setVariantCards([]); setVariantScores({}); setVariantsByBase({}); setPerSetVariantScores({}); setVariantBases([]);
    setResult(null); setAwaitingHuman(false); setStatus("running"); setWorkflow(""); setLive(true);
    setStopping(false); setInterviewMd(""); setInterviewCount(0); setInterviewQueue([]); setInterviewPublished([]);
    setInterviewOutcomes([]); setInterviewPerSession([]);
    recoveredRef.current = false;

    // Check the run's server-side state first: a stalled run (running but no live driver) is
    // auto-recovered from the LangGraph checkpoint before we attach the stream.
    api.getRun(runId).then((d) => {
      const terminal = d.status === "done" || d.status === "error";
      if (d.status) setStatus(d.status);
      if (d.workflow) setWorkflow(d.workflow);
      setLive(!!d.live);
      if (terminal) setResult(d);   // authoritative snapshot for the done summary (no live-status race)
      // Auto-recover ONLY genuinely orphaned runs — status still `running`/`stalled` but no live
      // driver (e.g. a server restart killed the thread). Explicitly NOT auto-recovered:
      //   • `awaiting_human` — parked at a gate; its gate renders from the durable SSE replay, and
      //     re-driving would race the reviewer's submit and break the review→export flow.
      //   • `paused` / `dismissed` — the reviewer intentionally stopped (Feature 10); auto-resuming
      //     would undo their pause/cancel. A paused run only resumes via the explicit Resume button.
      const recoverable = d.status === "running" || d.status === "stalled";
      if (recoverable && d.live === false && !recoveredRef.current) {
        recoveredRef.current = true;
        api.recoverRun(runId).then(() => setLive(true)).catch(() => {});
      }
    }).catch(() => {});

    const es = openStream(runId);
    esRef.current = es;
    return () => es.close();
  }, [runId, openStream]);

  const resume = useCallback(async (decisions) => {
    await api.resumeRun(runId, decisions);
    setAwaitingHuman(false);
    setStatus("running");
    setLive(true);
  }, [runId]);

  const recover = useCallback(async () => {
    await api.recoverRun(runId);
    setStatus("running");
    setLive(true);
    setStopping(false);
  }, [runId]);

  // Feature 10 — reviewer stop. The driver stops at the next node boundary and emits `paused`/
  // `cancelled`, which flips status above; we set `stopping` for the transient "Pausing…" affordance.
  const pause = useCallback(async () => {
    setStopping(true);
    try { await api.pauseRun(runId); } catch { setStopping(false); }
  }, [runId]);
  const cancel = useCallback(async () => {
    setStopping(true);
    try {
      const r = await api.cancelRun(runId);
      // A live run is signalled → the driver emits `cancelled` (handled above). A parked/paused run
      // is dismissed directly with no driver to emit, so reflect it here.
      if (!r.stopping) { setStatus("dismissed"); setLive(false); setStopping(false); }
    } catch { setStopping(false); }
  }, [runId]);

  const { phase, inRubric, inVariants, now, singleSet, emptySet, isPractice, isInterview, variantGate, rubricGate } = derivePipeline(events, workflow);
  return {
    events, sets, gate, rubricCards, criticScores, scoringQuestions,
    variantCards, variantScores, variantsByBase, perSetVariantScores, variantBases, result,
    awaitingHuman, status, workflow, live, stopping, phase, inRubric, inVariants, now, singleSet, emptySet,
    isPractice, isInterview, variantGate, rubricGate, pool: sets.pool, interviewMd, interviewCount, interviewQueue, interviewPublished,
    interviewOutcomes, interviewPerSession,
    resume, recover, pause, cancel,
  };
}
