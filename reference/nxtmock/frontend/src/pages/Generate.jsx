import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useWorkspace } from "../context/Workspace.jsx";
import { api, FALLBACK_USD_INR } from "../lib/api.js";
import { useAgentRun } from "../hooks/useAgentRun.js";
import ErrorState from "../components/ErrorState.jsx";
import PipelineStepper from "../components/PipelineStepper.jsx";
import PipelineGraph from "../components/PipelineGraph.jsx";
import SetColumn from "../components/SetColumn.jsx";
import SetsLayout from "../components/SetsLayout.jsx";
import RubricCard from "../components/RubricCard.jsx";
import ScoringCard from "../components/ScoringCard.jsx";
import BaseVariantGroup from "../components/BaseVariantGroup.jsx";
import GateBanner from "../components/GateBanner.jsx";
import ProgressNote from "../components/ProgressNote.jsx";
import Modal from "../components/Modal.jsx";
import Markdown from "../components/Markdown.jsx";
import InterviewTable from "../components/InterviewTable.jsx";

// Generate view: uses the shared sidebar selection. Start a run → it renders the live pipeline
// graph + question columns + review gate inline. Mounted at /generate and /run/:runId.
export default function Generate() {
  const { runId } = useParams();
  const navigate = useNavigate();
  const { course, session, sessions } = useWorkspace();

  const [starting, setStarting] = useState(false);
  const [error, setError] = useState(null);
  const [existing, setExisting] = useState(null);   // prior generation for this session (Feature 6 warning)
  // Module Quiz (Feature 9): which sessions to merge + the reviewer-typed name (prefilled from titles).
  const [selectedSessions, setSelectedSessions] = useState([]);
  const [moduleName, setModuleName] = useState("");
  const [moduleNameTouched, setModuleNameTouched] = useState(false);

  const { events, sets, gate, rubricCards, criticScores, scoringQuestions,
    variantCards, variantScores, variantsByBase, perSetVariantScores, variantBases, result,
    awaitingHuman, status, workflow, live, stopping, inRubric, inVariants, singleSet, emptySet,
    isPractice, isInterview, variantGate, rubricGate, pool, interviewMd, interviewCount, interviewQueue, interviewPublished,
    interviewOutcomes, interviewPerSession,
    resume, recover, pause, cancel } = useAgentRun(runId);
  const [decisions, setDecisions] = useState({});
  const [submitting, setSubmitting] = useState(false);
  // Which product workflow to start (chosen before a run begins). Feature 8/9.
  const [selectedWorkflow, setSelectedWorkflow] = useState("classroom_quiz");
  // A run is "practice"/"module" once we know its workflow (from run meta/events), else the pre-run choice.
  const practice = runId ? (workflow === "mcq_practice" || isPractice) : selectedWorkflow === "mcq_practice";
  const moduleRun = runId ? workflow === "module_quiz" : selectedWorkflow === "module_quiz";
  // Mock Interview (Feature 11). For a live run, trust EITHER the run's workflow OR the event-derived
  // `isInterview` (set the moment outcomes/harvest/verify events arrive) so the view never flashes the
  // classroom lane before getRun resolves.
  const interviewRun = runId ? (workflow === "mock_interview" || isInterview) : selectedWorkflow === "mock_interview";
  // Both module + interview merge several selected sessions → reuse the multi-session picker.
  const mergeRun = moduleRun || interviewRun;
  // "flat" = a single merged column (practice's pool or the module body) rather than Set 1 | Set 2.
  const flat = practice || moduleRun;
  const flatSet = practice ? pool : sets.module;   // the single column's questions, live

  // Reset only on a genuinely new run. NOT on every `gate` change: the SSE stream replays the full
  // event history on reconnect (backend/api/agent.py), which re-fires the prior `awaiting_human`
  // events and flaps `gate` backward→forward — clearing here would wipe the reviewer's in-progress
  // decisions (incl. an accepted "improve" rewrite) mid-gate. We clear after a successful submit
  // instead, so each gate still starts fresh while a replay can never discard accepted work.
  useEffect(() => { setDecisions({}); }, [runId]);

  // Before generating, warn if this session was already generated (Feature 6). On confirm the user
  // can Update (regenerate — replaces the files) or Open the existing run instead.
  async function start() {
    setStarting(true); setError(null);
    try {
      // Module quiz / mock interview are keyed by their (typed) name; classroom/practice by the session.
      const key = mergeRun ? moduleName : session;
      const info = await api.checkExists(course, key, selectedWorkflow);
      if (info.exists) { setExisting(info); return; }
      await reallyStart();
    } catch (e) { setError(e); }
    finally { setStarting(false); }
  }

  async function reallyStart() {
    setExisting(null); setStarting(true); setError(null);
    try {
      const { run_id } = interviewRun
        ? await api.startMockInterview(course, selectedSessions, moduleName.trim())
        : moduleRun
        ? await api.startModuleQuiz(course, selectedSessions, moduleName.trim())
        : await api.startRun(course, session, selectedWorkflow);
      navigate(`/run/${run_id}`);
    } catch (e) { setError(e); }
    finally { setStarting(false); }
  }

  // Toggle a session in/out of the module selection; keep the name prefilled from titles until edited.
  function toggleSession(sid) {
    setSelectedSessions((cur) => {
      const next = cur.includes(sid) ? cur.filter((s) => s !== sid) : [...cur, sid];
      if (!moduleNameTouched) {
        const titles = next
          .map((id) => (sessions.find((s) => s.session === id) || {}).session_title || id)
          .join(" + ");
        setModuleName(titles);
      }
      return next;
    });
  }

  const onDecide = (d) => setDecisions((cur) => ({ ...cur, [d.qid]: d }));
  // Release a card's locked decision so the reviewer can re-check and pick again ("Change ↺").
  const onReset = (qid) => setDecisions((cur) => {
    const next = { ...cur };
    delete next[qid];
    return next;
  });
  // Feature 6: feedback → LLM rewrite (preview). The card shows the result and, on "Use this",
  // records an "improve" decision; the backend distills the feedback into memory on submit.
  // Returns { improved, score? } — the score (rubric/variants gates) lets the card refresh its band
  // right after an accepted improve (Item 4). `question` is the CURRENT view (chains improve-on-improve).
  const onImprove = (question, feedback) =>
    api.improveQuestion(runId, { question, feedback, gate });
  // Single-set run → render only the non-empty column in the shared Set 1 | Set 2 layouts.
  const onlySet = singleSet ? (emptySet === "set_a" ? "set_b" : "set_a") : undefined;

  async function submitReview() {
    setSubmitting(true);
    let list;
    if (gate === "variants") {
      list = variantCards.map((c) => decisions[c.qid] || { qid: c.qid, action: "approve" });
    } else if (gate === "rubric") {
      list = rubricCards.map((c) => decisions[c.qid] || { qid: c.qid, action: "approve" });
    } else if (gate === "interview") {
      // Mock Interview queue (Feature 11) — untouched rows are approved (published) on submit.
      list = interviewQueue.map((c) => decisions[c.qid] || { qid: c.qid, action: "approve" });
    } else {
      // Generation gate: classroom reads Set 1/Set 2; practice/module read the single flat column.
      const allQ = flat
        ? (flatSet?.questions || [])
        : [...(sets.set_a?.questions || []), ...(sets.set_b?.questions || [])];
      list = allQ.map((q) => decisions[q.qid] || { qid: q.qid, action: "accept" });
    }
    await resume(list);
    setDecisions({});   // advance to the next gate fresh (replay-safe: only cleared on a real submit)
    setSubmitting(false);
  }

  const flaggedCount = rubricCards.filter((c) => !c.pass).length;
  const vFlaggedCount = variantCards.filter((c) => !c.pass).length;
  // A gate is only "open" while the run is genuinely paused — never on a finished run (item 1 fix).
  const atGate = awaitingHuman && status !== "done";
  // After the LAST gate is submitted, the graph runs the export node (writes JSON + zip) → done. That
  // step reuses the prior phase's progress view, so flag it explicitly to label it "Exporting…" rather
  // than mislabelling it as a re-generation (variants gate) or re-scoring (practice's rubric gate).
  // Classroom/module export after the variants gate; practice exports after the rubric gate (no variants).
  const exporting = ((practice ? rubricGate : variantGate) && !atGate && status !== "done");

  // Build base→variants groups (live: from streamed variants; gate: from scored cards).
  const liveGroups = {};
  for (const [base, vs] of Object.entries(variantsByBase)) {
    liveGroups[base] = vs.map((v) => ({ q: v, vtypeLabel: v.variant_type, score: variantScores[v.qid] }));
  }
  const gateGroups = {};
  for (const c of variantCards) {
    (gateGroups[c.base_question_keys] ||= []).push({
      q: c.question, vtypeLabel: c.variant_label || c.variant_type, card: c,
      score: { band: c.band, points: c.points, max_points: c.max_points },
    });
  }

  // What actually shipped to the JSON/MD/ZIP (Item 8): approved bases + approved variants grouped
  // under their base, with the improved ones marked. Rejected questions are absent by construction.
  const exportedBases = result?.rubric_approved || result?.accepted || [];
  const exportedVariants = result?.variants_approved || [];
  const exportedEdited = new Set([
    ...(result?.rubric_summary?.edited_qids || []),
    ...(result?.variant_summary?.edited_qids || []),
  ]);
  const exportedVarsByBase = {};
  for (const v of exportedVariants) (exportedVarsByBase[v.base_question_keys] ||= []).push(v);
  const exportedTotal = exportedBases.length + exportedVariants.length;

  return (
    <div className="view">
      <header className="view-head view-head-row">
        <div>
          <h1 className="view-title">Generate quiz</h1>
          <p className="view-sub">
            {session ? <>Session: <strong>{session}</strong></> : "Select a session in the sidebar to begin."}
          </p>
        </div>
        <div className="view-head-actions">
          {/* Workflow picker (Feature 8) — only before a run; a run is locked to its workflow. */}
          {!runId && (
            <div className="workflow-toggle" role="group" aria-label="Quiz type">
              <button type="button"
                className={"btn btn-sm" + (selectedWorkflow === "classroom_quiz" ? " btn-primary" : " btn-ghost")}
                onClick={() => setSelectedWorkflow("classroom_quiz")}>Classroom Quiz</button>
              <button type="button"
                className={"btn btn-sm" + (selectedWorkflow === "mcq_practice" ? " btn-primary" : " btn-ghost")}
                onClick={() => setSelectedWorkflow("mcq_practice")}>MCQ Practice</button>
              <button type="button"
                className={"btn btn-sm" + (selectedWorkflow === "module_quiz" ? " btn-primary" : " btn-ghost")}
                onClick={() => setSelectedWorkflow("module_quiz")}>Module Quiz</button>
              <button type="button"
                className={"btn btn-sm" + (selectedWorkflow === "mock_interview" ? " btn-primary" : " btn-ghost")}
                onClick={() => setSelectedWorkflow("mock_interview")}>Mock Interview</button>
            </div>
          )}
          {runId && <span className={"status-pill status-" + status}>{status.replace("_", " ")}</span>}
          {runId && <span className="workflow-pill">{interviewRun ? "Mock Interview" : moduleRun ? "Module Quiz" : practice ? "MCQ Practice" : "Classroom Quiz"}</span>}
          <button className="btn btn-primary" disabled={starting ||
            (runId ? false : mergeRun ? (!course || selectedSessions.length === 0 || !moduleName.trim()) : (!course || !session))}
            onClick={runId ? () => navigate("/generate") : start}>
            {starting ? "Starting…" : runId ? "New run ▸" : interviewRun ? "Harvest interview questions ▸" : moduleRun ? "Generate module quiz ▸" : practice ? "Generate practice ▸" : "Generate quiz ▸"}
          </button>
        </div>
      </header>

      {error && <div className="card"><ErrorState error={error} /></div>}

      {existing && (
        <Modal title="This session is already generated" onClose={() => { setExisting(null); setStarting(false); }}>
          <p>
            A quiz for <strong>{session}</strong> was already generated
            {existing.finished_at ? <> on <strong>{new Date(existing.finished_at).toLocaleString()}</strong></> : null}.
            {existing.zips?.length > 0 && <> {existing.zips.length} portal zip{existing.zips.length === 1 ? "" : "s"} on disk.</>}
          </p>
          <p className="muted">Update regenerates it (replacing the existing files), or you can open the previous run.</p>
          <div className="modal-actions">
            <button className="btn btn-primary" onClick={reallyStart}>Update — regenerate ▸</button>
            {existing.run_id && (
              <button className="btn" onClick={() => { setExisting(null); navigate(`/run/${existing.run_id}`); }}>
                Open existing run ▸
              </button>
            )}
            <button className="btn btn-ghost" onClick={() => { setExisting(null); setStarting(false); }}>Cancel</button>
          </div>
        </Modal>
      )}

      {/* Module Quiz (Feature 9) + Mock Interview (Feature 11): pick several sessions to merge, then
          name the assessment / topic. Styled as a hero; the form sits on a frosted panel. */}
      {!runId && !error && mergeRun && (
        <section className="hero hero-module" aria-label={interviewRun ? "Build a mock interview" : "Build a module quiz"}>
          <div className="hero-orbs" aria-hidden="true"><span></span><span></span><span></span></div>
          <div className="hero-inner hero-inner-module">
            <span className="hero-eyebrow">{interviewRun ? "Mock Interview · harvested from real interviews" : "Module Quiz · AI-generated"}</span>
            {interviewRun ? (
              <h1 className="hero-title">
                Harvest <span className="hero-hl">real interview questions</span><br />
                for a topic's sessions.
              </h1>
            ) : (
              <h1 className="hero-title">
                Build a <span className="hero-hl">module assessment</span><br />
                from several sessions.
              </h1>
            )}
            <p className="hero-sub">
              {interviewRun
                ? "Pick the sessions of a topic. We extract their key skills and harvest REAL questions actually asked in interviews — with the companies and source links as proof. Nothing is AI-generated."
                : "At least 6 robust, assessment-level questions per session — drawn from each session's most important concepts (no rote recall), with variants — exported under one name."}
            </p>

            <div className="module-panel">
              {!course ? (
                <p className="module-empty">Select a course in the sidebar to list its sessions.</p>
              ) : sessions.length === 0 ? (
                <p className="module-empty">No sessions found for this course.</p>
              ) : (
                <ul className="module-session-list">
                  {sessions.map((s) => (
                    <li key={s.session}>
                      <label className="module-session-row">
                        <input type="checkbox"
                          checked={selectedSessions.includes(s.session)}
                          onChange={() => toggleSession(s.session)} />
                        <span className="module-session-title">{s.session_title || s.session}</span>
                        {s.module && <span className="chip chip-soft">{s.module}</span>}
                      </label>
                    </li>
                  ))}
                </ul>
              )}
              <label className="module-name-field">
                <span className="module-field-label">{interviewRun ? "Topic name" : "Module quiz name"}</span>
                <input type="text" className="module-name-input"
                  placeholder={interviewRun ? "e.g. Generative AI for Finance" : "e.g. Module 1 — LangChain Basics"}
                  value={moduleName}
                  onChange={(e) => { setModuleName(e.target.value); setModuleNameTouched(true); }} />
              </label>
              <div className="module-setup-actions">
                <span className="muted">{selectedSessions.length} session{selectedSessions.length === 1 ? "" : "s"} selected</span>
                <button className="hero-cta hero-cta-sm"
                  disabled={starting || !course || selectedSessions.length === 0 || !moduleName.trim()}
                  onClick={start}>
                  {starting ? "Starting…" : interviewRun ? "Harvest interview questions" : "Generate module quiz"}
                  <span className="hero-cta-arrow" aria-hidden="true">→</span>
                </button>
              </div>
            </div>
          </div>
        </section>
      )}

      {!runId && !error && !mergeRun && (
        <section className={"hero" + (practice ? " hero-practice" : "")} aria-label="Get started">
          <div className="hero-orbs" aria-hidden="true"><span></span><span></span><span></span></div>
          <div className="hero-inner">
            <span className="hero-eyebrow">{practice ? "MCQ Practice" : "Classroom Quiz"} · AI-generated</span>
            {practice ? (
              <h1 className="hero-title">
                Create <span className="hero-hl">MCQ practice sets</span><br />
                from any session using AI.
              </h1>
            ) : (
              <h1 className="hero-title">
                Create <span className="hero-hl">classroom quizzes</span><br />
                from any session using AI.
              </h1>
            )}
            <p className="hero-sub">
              {practice
                ? "Turn a whole session into a varied, rubric-checked MCQ pool — every question type, count in multiples of 5, no variants."
                : "Split a session into Set 1 / Set 2, auto-generate and rubric-check the questions, then export portal-ready files."}
            </p>
            <button className="hero-cta" disabled={!course || !session || starting} onClick={start}>
              {starting ? "Starting…" : practice ? "Generate practice set" : "Generate quiz"}
              <span className="hero-cta-arrow" aria-hidden="true">→</span>
            </button>
            {!(course && session) && (
              <p className="hero-hint">Select a course &amp; session in the sidebar to begin.</p>
            )}
          </div>
        </section>
      )}

      {runId && (
        <>
          <PipelineStepper events={events} workflow={workflow} />

          {/* Mock Interview transparency (P7): the extracted outcomes, grouped per session. */}
          {interviewRun && interviewOutcomes.length > 0 && (
            <details className="card interview-outcomes-card" open>
              <summary><strong>Outcomes extracted</strong> — {interviewOutcomes.length} skills{interviewPerSession.length ? ` across ${interviewPerSession.length} session${interviewPerSession.length === 1 ? "" : "s"}` : ""}</summary>
              {interviewPerSession.length > 0 && (
                <p className="muted" style={{ margin: "0.4rem 0" }}>
                  {interviewPerSession.map((s) => `${s.title} (${s.n})`).join(" · ")}
                </p>
              )}
              <div className="outcome-chips" style={{ display: "flex", flexWrap: "wrap", gap: "0.35rem" }}>
                {interviewOutcomes.map((o, i) => (
                  <code key={i} className="outcome-chip"
                    style={{ background: "#eef", padding: "0.15rem 0.45rem", borderRadius: "0.4rem", fontSize: "0.85em" }}>{o}</code>
                ))}
              </div>
            </details>
          )}

          {/* Active automated work — offer to pause or cancel (Feature 10). Hidden at a gate. */}
          {status === "running" && live && !awaitingHuman && (
            <div className="card run-controls-bar">
              <span className="muted">The agent is working — you can stop it without losing progress.</span>
              <div className="spacer" />
              <button className="btn" onClick={pause} disabled={stopping}>
                {stopping ? "Pausing…" : "⏸ Pause"}
              </button>
              <button className="btn btn-ghost" disabled={stopping}
                onClick={() => { if (window.confirm("Cancel this run? It will be discarded.")) cancel(); }}>
                ✕ Cancel run
              </button>
            </div>
          )}

          {/* Reviewer-paused (Feature 10) or stalled (driver died) — offer to resume or discard.
              Not shown at a gate (parked ≠ paused/stalled). */}
          {(status === "paused" || (status === "running" && !live)) && !awaitingHuman && (
            <div className="card stalled-bar">
              <strong>⏸ This run is paused.</strong>
              <span className="muted">Its progress is saved — resume it from where it left off.</span>
              <div className="spacer" />
              <button className="btn btn-primary" onClick={recover}>Resume run ▸</button>
              <button className="btn btn-ghost" onClick={cancel}>Discard</button>
            </div>
          )}

          {/* The detailed graph is the classroom/practice/module topology — hidden for mock_interview
              (its lane is shown by the stepper above) and until the workflow resolves on reload, so the
              classroom Split SVG never flashes on a mock_interview run. */}
          {workflow && !interviewRun && (
            <details className="graph-details" open>
              <summary>Detailed pipeline view</summary>
              <PipelineGraph events={events} />
            </details>
          )}

          {/* Mock Interview (Feature 11) — harvest progress → exception-only review queue → table. */}
          {interviewRun && status !== "done" && !interviewMd && !atGate && (
            <ProgressNote title="Harvesting & verifying real interview questions…"
              hint="Extracting the topic's key skills, harvesting genuine questions, then corroborating each across sources (companies + proof links). Well-evidenced ones auto-publish." />
          )}

          {/* Interview review gate — only the under-evidenced rows reach a human (Part 3). */}
          {atGate && gate === "interview" && (
            <>
              {/* Already auto-published (passed the strict bar: ≥1 named company + corroborating links) —
                  shown read-only so the reviewer sees the evidenced results, not just the "—" remainder. */}
              {interviewPublished.length > 0 && (
                <div className="interview-published-block">
                  <h2 className="section-title">Auto-published — {interviewPublished.length} evidenced with companies ✓</h2>
                  <p className="muted" style={{ marginTop: "-0.4rem" }}>
                    These cleared the strict bar (named company + corroborating sources) and are already in the table — no review needed.
                  </p>
                  <InterviewTable rows={interviewPublished} readOnly />
                </div>
              )}
              <GateBanner title="Review queued interview questions" flagged={interviewQueue.length}
                hint={interviewQueue.length === 0
                  ? "Nothing needs review — submit to publish."
                  : `${interviewPublished.length} company-backed question${interviewPublished.length === 1 ? "" : "s"} were auto-published above. The rows below are the under-evidenced remainder (1 source, or no company tied yet — that's why Companies shows "—"). Approve to publish anyway, or reject with a reason (it teaches the verifier). Untouched rows are approved.`}
                cta="Submit & publish ▸" busy={submitting} onSubmit={submitReview} />
              <InterviewTable rows={interviewQueue} decisions={decisions} onDecide={onDecide} onReset={onReset} />
            </>
          )}
          {interviewRun && interviewMd && (
            <div className="card">
              <h2 className="section-title">Mock interview questions — {interviewCount} published ✓</h2>
              <p className="muted">
                Real questions harvested from legitimate sources, corroborated across sites and verified —
                never generated. Each row carries its companies + proof links.
              </p>
              {(result?.cost_usd != null || result?.cost_estimate != null) && (
                <div className="cost-line">
                  💰 {result.cost_usd != null
                    ? <>This run cost <strong>₹{(result.cost_inr ?? result.cost_usd * (result.usd_to_inr || FALLBACK_USD_INR)).toFixed(2)}</strong>{" "}
                       <span className="muted">(≈${result.cost_usd.toFixed(3)}, {result.cost_exact ? "exact" : "approx"} · OpenRouter; Tavily credits separate)</span></>
                    : <>Estimated cost <strong>~₹{(result.cost_estimate_inr ?? result.cost_estimate * (result.usd_to_inr || FALLBACK_USD_INR)).toFixed(2)}</strong>{" "}
                       <span className="muted">(≈${result.cost_estimate?.toFixed(3)} · Tavily credits separate)</span></>}
                </div>
              )}
              {result?.exported?.[0]?.md_path && (
                <p className="muted">📄 Written to <code>{result.exported[0].md_path.split("/").slice(-4).join("/")}</code></p>
              )}
              <Markdown>{interviewMd}</Markdown>
            </div>
          )}

          {/* Generation gate — accept / edit / delete the generated questions */}
          {atGate && gate === "generation" && (
            <GateBanner title="Review the generated questions"
              hint="Accept, edit, or delete each question. Anything you don't touch is accepted."
              cta="Submit & score ▸" busy={submitting} onSubmit={submitReview} />
          )}

          {/* Rubric gate — approve / edit / reject the scored questions */}
          {atGate && gate === "rubric" && (
            <>
              <GateBanner title="Rubric review" flagged={flaggedCount}
                hint={rubricCards.length === 0
                  ? "No questions reached the rubric — submit to finish."
                  : flaggedCount > 0
                  ? "Flagged questions are highlighted below — approve, edit, or reject. Untouched questions are approved."
                  : practice
                  ? "Every question passed the rubric — approve to export the practice quiz."
                  : "Every question passed the rubric — approve to continue to variants."}
                cta={practice ? "Submit & export ▸" : "Submit rubric review ▸"} busy={submitting} onSubmit={submitReview} />
              {flat ? (
                <div className="practice-list">
                  {rubricCards.map((c) => (
                    <RubricCard key={c.qid} card={c} decision={decisions[c.qid]} onDecide={onDecide} onReset={onReset} onImprove={onImprove} />
                  ))}
                </div>
              ) : (
                <SetsLayout only={onlySet} renderItems={(label) => (
                  rubricCards.filter((c) => c.set_label === label).map((c) => (
                    <RubricCard key={c.qid} card={c} decision={decisions[c.qid]} onDecide={onDecide} onReset={onReset} onImprove={onImprove} />
                  ))
                )} />
              )}
            </>
          )}

          {/* Scoring in progress (after accept, before the rubric gate) — live bands. */}
          {inRubric && !inVariants && !(atGate && gate === "rubric") && !exporting && status !== "done" && (
            <>
              <ProgressNote title="Scoring against the rubric…"
                hint="Each question is checked against the 25 quality checkpoints; bands fill in live." />
              {flat ? (
                <div className="practice-list">
                  {(scoringQuestions.length ? scoringQuestions : (flatSet?.questions || []))
                    .map((q) => <ScoringCard key={q.qid} q={q} score={criticScores[q.qid]} />)}
                </div>
              ) : (
                <SetsLayout only={onlySet} renderItems={(label) => {
                  const all = scoringQuestions.length
                    ? scoringQuestions
                    : [...(sets.set_a?.questions || []), ...(sets.set_b?.questions || [])];
                  return all.filter((q) => q.set_label === label)
                    .map((q) => <ScoringCard key={q.qid} q={q} score={criticScores[q.qid]} />);
                }} />
              )}
            </>
          )}

          {/* Exporting — after the variants gate submit, files + zip are written, then the run finishes. */}
          {exporting && (
            <ProgressNote title="Exporting the quiz files & portal zip…"
              hint="Writing the per-set JSON (Default_new + Code Analysis MCQs) and the portal zip — the download appears here when it's done." />
          )}

          {/* Variants generating / scoring — Set 1 | Set 2, each base with its variants beneath. */}
          {inVariants && !(atGate && gate === "variants") && !exporting && status !== "done" && (
            <>
              <ProgressNote title="Generating & scoring variants…"
                hint="Each approved question gets 8 typed variants — they appear under their base with live bands." />
              {variantBases.length === 0 ? (
                <div className="card muted">Preparing variants…</div>
              ) : moduleRun ? (
                <div className="sets-row sets-row-single">
                  <div className="set-col card">
                    {variantBases.map((b) => (
                      <BaseVariantGroup key={b.key} base={b} items={liveGroups[b.key] || []} />
                    ))}
                  </div>
                </div>
              ) : (
                <SetsLayout only={onlySet} renderItems={(label) => (
                  variantBases.filter((b) => b.set_label === label).map((b) => (
                    <BaseVariantGroup key={b.key} base={b} items={liveGroups[b.key] || []} />
                  ))
                )} />
              )}
            </>
          )}

          {/* Variants gate — approve / edit / reject each variant (Set 1 | Set 2, grouped under base). */}
          {atGate && gate === "variants" && (
            <>
              <GateBanner title="Variant review" flagged={vFlaggedCount}
                hint={variantCards.length === 0
                  ? "No variants were generated — submit to finish."
                  : vFlaggedCount > 0
                  ? "Flagged variants are highlighted below — approve, edit, or reject. Untouched are approved."
                  : "Every variant passed — approve to export the quiz files, portal zips & report."}
                cta="Submit & export ▸" busy={submitting} onSubmit={submitReview} />
              {Object.keys(perSetVariantScores).length > 0 && (
                <div className="setband-bar">
                  <span className="muted">{moduleRun ? "Variety verdict:" : "Per-set variety verdict:"}</span>{" "}
                  {Object.entries(perSetVariantScores).map(([s, sc]) => (
                    <span key={s} className={"band-chip band-" + (sc.band || "red")}>
                      {s === "set_a" ? "Set 1" : s === "set_b" ? "Set 2" : "Module"} {(sc.band || "").toUpperCase()}
                    </span>
                  ))}
                </div>
              )}
              {moduleRun ? (
                <div className="sets-row sets-row-single">
                  <div className="set-col card">
                    {variantBases.map((b) => (
                      <BaseVariantGroup key={b.key} base={b} items={gateGroups[b.key] || []}
                        decisions={decisions} onDecide={onDecide} onReset={onReset} onImprove={onImprove} />
                    ))}
                  </div>
                </div>
              ) : (
                <SetsLayout only={onlySet} renderItems={(label) => (
                  variantBases.filter((b) => b.set_label === label).map((b) => (
                    <BaseVariantGroup key={b.key} base={b} items={gateGroups[b.key] || []}
                      decisions={decisions} onDecide={onDecide} onReset={onReset} onImprove={onImprove} />
                  ))
                )} />
              )}
            </>
          )}

          {/* Final summary — files exported, run complete (quiz workflows; interview has its own below) */}
          {!interviewRun && result && (result.status === "done" || status === "done") && (
            <div className="card summary-bar">
              {practice ? (
                <>
                  <h2 className="section-title">Practice quiz exported ✓</h2>
                  <div className="summary-badges">
                    <span className="badge badge-ok">{result.practice_summary?.approved ?? result.rubric_summary?.approved ?? 0} questions</span>
                    {Object.entries(result.practice_summary?.types || {}).map(([t, n]) => (
                      <span key={t} className="badge">{n}× {t.toLowerCase().replace(/_/g, " ")}</span>
                    ))}
                  </div>
                </>
              ) : (
                <>
                  <h2 className="section-title">{moduleRun ? "Module quiz exported ✓" : "Variants exported ✓"}</h2>
                  <div className="summary-badges">
                    <span className="badge badge-ok">{result.variant_summary?.approved ?? 0} variants approved</span>
                    <span className="badge">{result.variant_summary?.total ?? 0} generated</span>
                    {result.variant_summary?.rejected > 0 &&
                      <span className="badge badge-warn">{result.variant_summary.rejected} rejected</span>}
                    {result.rubric_summary?.approved != null &&
                      <span className="badge">{result.rubric_summary.approved} base questions</span>}
                  </div>
                  <div className="band-counts">
                    <span className="band-chip band-green">{result.variant_summary?.green || 0} green</span>
                    <span className="band-chip band-red">{result.variant_summary?.red || 0} red</span>
                  </div>
                </>
              )}
              {(result.cost_usd != null || result.cost_estimate != null) && (
                <div className="cost-line">
                  💰 {result.cost_usd != null
                    ? <>This run cost <strong>₹{(result.cost_inr ?? result.cost_usd * (result.usd_to_inr || FALLBACK_USD_INR)).toFixed(2)}</strong>{" "}
                       <span className="muted">(≈${result.cost_usd.toFixed(3)}, {result.cost_exact ? "exact" : "approx"} · OpenRouter)</span></>
                    : <>Estimated cost <strong>~₹{(result.cost_estimate_inr ?? result.cost_estimate * (result.usd_to_inr || FALLBACK_USD_INR)).toFixed(2)}</strong>{" "}
                       <span className="muted">(≈${result.cost_estimate?.toFixed(3)})</span></>}
                </div>
              )}
              {result.promoted_checkpoints?.length > 0 && (
                <p className="muted">🧠 The rubric learned — refined checkpoint(s) {result.promoted_checkpoints.join(", ")}.</p>
              )}
              {result.exported?.length > 0 && (
                <div className="exported-list">
                  <strong>Written to the repo:</strong>
                  <ul>
                    {result.exported.map((e, i) => (
                      <li key={i}>
                        {e.report
                          ? <>📄 manager review · <code>{e.report}</code></>
                          : (
                            <>
                              <code>{e.set}</code> — {e.count} questions · 📦 <code>{e.zip ? e.zip.split("/").pop() : ""}</code>
                              {e.zip && (
                                <a className="btn btn-sm dl-btn" href={api.downloadUrl(runId, e.set)} download>
                                  ⬇ Download zip
                                </a>
                              )}
                            </>
                          )}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* The exact accepted/improved questions that went into the JSON/MD/ZIP (Item 8). */}
              {exportedTotal > 0 && (
                <details className="exported-questions">
                  <summary>What was exported — {exportedTotal} question{exportedTotal === 1 ? "" : "s"} (accepted; rejected excluded)</summary>
                  <ul className="exported-q-list">
                    {exportedBases.map((b) => {
                      const vs = exportedVarsByBase[b.question_key] || [];
                      return (
                        <li key={b.qid} className="exported-q-base">
                          <span className="exp-tag exp-accepted">✓ accepted</span>
                          {exportedEdited.has(b.qid) && <span className="exp-tag exp-improved">✎ improved</span>}
                          <span className="exp-q-text">{b.question_text}</span>
                          {vs.length > 0 && (
                            <ul className="exported-q-variants">
                              {vs.map((v) => (
                                <li key={v.qid}>
                                  <span className="chip chip-type">{v.variant_type}</span>
                                  {exportedEdited.has(v.qid) && <span className="exp-tag exp-improved">✎ improved</span>}
                                  <span className="exp-q-text">{v.question_text}</span>
                                </li>
                              ))}
                            </ul>
                          )}
                        </li>
                      );
                    })}
                  </ul>
                </details>
              )}
            </div>
          )}

          {/* Flat single column — practice's pool (Feature 8) or the merged module body (Feature 9). */}
          {!inRubric && flat && (
            <div className="sets-row sets-row-single">
              <SetColumn title={moduleRun ? "Module questions" : "Practice questions"}
                set={flatSet} gate={atGate && gate === "generation"}
                decisions={decisions} onDecide={onDecide} onReset={onReset} onImprove={onImprove} />
            </div>
          )}

          {/* Generation columns — shown only during generation; cleared once the rubric phase starts.
              A small/single-section session yields a single set (the empty half is skipped by
              design) — show just that column with a note instead of an empty Set 2.
              Suppressed for mock_interview (it has no Set 1/Set 2 — it renders a table below). */}
          {!interviewRun && !inRubric && !flat && (
            singleSet ? (
              <>
                <div className="card single-set-note">
                  ℹ Small session — generated a <strong>single set</strong> (not enough content to split into two).
                </div>
                <div className="sets-row">
                  <SetColumn title="Set 1" set={emptySet === "set_a" ? sets.set_b : sets.set_a}
                    gate={atGate && gate === "generation"}
                    decisions={decisions} onDecide={onDecide} onReset={onReset} onImprove={onImprove} />
                </div>
              </>
            ) : (
              <div className="sets-row">
                <SetColumn title="Set 1" set={sets.set_a} gate={atGate && gate === "generation"}
                  decisions={decisions} onDecide={onDecide} onReset={onReset} onImprove={onImprove} />
                <SetColumn title="Set 2" set={sets.set_b} gate={atGate && gate === "generation"}
                  decisions={decisions} onDecide={onDecide} onReset={onReset} onImprove={onImprove} />
              </div>
            )
          )}
        </>
      )}
    </div>
  );
}
