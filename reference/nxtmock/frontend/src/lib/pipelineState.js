// Single source of truth for "where is this run, and what's happening right now", derived from the
// SSE event stream. Used by the stepper, the status line, the graph's auto-focus, and Generate's
// stale-state gating — so they never disagree.
//
// Phases: "generation" (assemble→split→sets→accept gate) → "rubric" (evaluate⟲optimize→review gate)
//         → "variants" (generate→score⟲optimize→variant gate→export) → "done".
// `inRubric` flips when the rubric phase starts; `inVariants` flips when the variants phase starts.

const STAGES = [
  { key: "assemble", label: "Assemble" },
  { key: "split", label: "Split" },
  { key: "generate", label: "Generate" },
  { key: "review", label: "Review" },        // generation human gate
  { key: "evaluate", label: "Evaluate" },
  { key: "optimize", label: "Optimize" },
  { key: "rubric_review", label: "Rubric review" },
  { key: "variants", label: "Variants" },     // generate + score variants
  { key: "variant_review", label: "Variant review" },
  { key: "done", label: "Done" },
];

// Mock Interview (Feature 11): a different lane — harvest+verify real questions, no split/variants.
const INTERVIEW_STAGES = [
  { key: "assemble", label: "Assemble" },
  { key: "outcomes", label: "Outcomes" },
  { key: "harvest", label: "Harvest" },
  { key: "verify", label: "Verify" },
  { key: "review", label: "Review" },        // exception-only interview gate
  { key: "done", label: "Done" },
];

export function derivePipeline(events, workflow) {
  // Until the workflow resolves (reload) AND no events have arrived yet, show a neutral loading state —
  // never flash the classroom Split lane on a mock_interview run.
  if (!workflow && (!events || events.length === 0)) {
    return { phase: "loading", inRubric: false, inVariants: false, now: "Loading…", stages: [],
             scored: 0, flagged: 0, vflagged: 0, singleSet: false, emptySet: null,
             isPractice: false, isModule: false, isInterview: false, variantGate: false, rubricGate: false };
  }
  const seen = new Set();
  let genGate = false, rubricGate = false, collected = false;
  let sawCritic = false, sawOptimizer = false, rubricDone = false, rubricFinalized = false;
  let sawVariant = false, sawVariantCritic = false, sawVariantOpt = false, variantsScored = false;
  let variantGate = false, exported = false, completed = false, errored = false, interviewGate = false;
  let criticRound = 0, variantRound = 0, scored = 0, flagged = 0, vflagged = 0;
  let genQ = 0;
  let splitAChars = null, splitBChars = null;   // single-set detection (Feature 6)

  for (const ev of events) {
    seen.add(ev.node);
    const p = ev.payload || {};
    switch (ev.node) {
      case "split": splitAChars = p.set_a_chars ?? splitAChars; splitBChars = p.set_b_chars ?? splitBChars; break;
      case "question": genQ += 1; break;
      case "collected": collected = true; break;
      case "critic": sawCritic = true; criticRound = Math.max(criticRound, p.round || 0); break;
      case "optimizer": sawOptimizer = true; break;
      case "rubric_done": rubricDone = true; scored = p.scored ?? scored; flagged = p.flagged ?? flagged; break;
      case "finalize": rubricFinalized = true; break;
      case "variant": case "variant_generator": case "variants_generated": sawVariant = true; break;
      case "variant_critic": sawVariantCritic = true; variantRound = Math.max(variantRound, p.round || 0); break;
      case "variant_optimizer": sawVariantOpt = true; break;
      case "variants_scored": variantsScored = true; vflagged = p.flagged ?? vflagged; break;
      case "export": exported = true; break;
      case "complete": completed = true; break;
      case "awaiting_human": {
        const g = p.gate || "generation";
        if (g === "rubric") { rubricGate = true; flagged = p.flagged ?? flagged; }
        else if (g === "variants") { variantGate = true; vflagged = p.flagged ?? vflagged; }
        else if (g === "interview") { interviewGate = true; }
        else genGate = true;
        break;
      }
      case "error": errored = true; break;
      default: break;
    }
  }

  // MCQ Practice (Feature 8): no split, no variants — detect it as early as the first pooled event
  // (plan/question carry set:"pool") so the stepper/now-line never flash the classroom "Split" stage.
  const isPractice = seen.has("pool_done")
    || events.some((e) => { const p = e.payload || {}; return p.workflow === "mcq_practice" || p.set === "pool"; });
  // Module Quiz (Feature 9): no split (one merged "module" body) but KEEPS the variants phase.
  const isModule = events.some((e) => { const p = e.payload || {}; return p.workflow === "module_quiz" || p.set === "module"; });
  // Mock Interview (Feature 11): detect from the run's workflow OR its distinctive event nodes, so the
  // stepper/graph switch to the interview lane immediately (never flashing the classroom "Split").
  const isInterview = workflow === "mock_interview"
    || events.some((e) => (e.payload || {}).workflow === "mock_interview")
    || seen.has("outcomes") || seen.has("harvest") || seen.has("verify") || seen.has("interview_export");
  const noSplit = isPractice || isModule;

  const done = exported || completed || seen.has("interview_export");
  const inRubric = !isInterview && (collected || sawCritic || rubricDone || rubricGate || rubricFinalized);
  // Practice has no variants phase, so finalize/export must NOT be read as "in variants" (module does);
  // interview has no rubric/variants phase at all.
  const inVariants = !isPractice && !isInterview && (rubricFinalized || sawVariant || sawVariantCritic || variantGate || done);

  // ── Mock Interview lane: a self-contained stepper/now, returned early (no classroom stage logic). ──
  if (isInterview) {
    const iGate = interviewGate;
    // Merge coverage from the `outcomes` event ("N sessions merged · M outcomes") — confirms every
    // selected session was used. Available from the Outcomes stage onward.
    const oc = events.map((e) => (e.node === "outcomes" ? e.payload || {} : null))
      .reverse().find((p) => p && typeof p.count === "number");
    const coverage = oc
      ? `${oc.session_count ?? "?"} session${oc.session_count === 1 ? "" : "s"} merged · ${oc.count} outcome${oc.count === 1 ? "" : "s"}`
      : "";
    const ist = {
      assemble: seen.has("assemble") ? "done" : "active",
      outcomes: (seen.has("harvest") || seen.has("verify") || iGate || done) ? "done"
        : (seen.has("assemble") ? "active" : "pending"),
      harvest: (seen.has("verify") || iGate || done) ? "done" : (seen.has("harvest") ? "active" : "pending"),
      verify: (iGate || done) ? "done" : (seen.has("verify") ? "active" : "pending"),
      review: (done && !iGate) ? "skip" : done ? "done" : iGate ? "active" : "pending",
      done: done ? "done" : "pending",
    };
    const sfx = coverage ? ` · ${coverage}` : "";
    // Richer step detail from the harvest/verify event payloads (counts, not just stage names).
    const hp = events.map((e) => (e.node === "harvest" ? e.payload || {} : null))
      .reverse().find((p) => p && typeof p.kept === "number");
    const vp = events.map((e) => (e.node === "verify" ? e.payload || {} : null))
      .reverse().find((p) => p && typeof p.published_this_run === "number");
    const vc = events.map((e) => (e.node === "verify" ? e.payload || {} : null))
      .reverse().find((p) => p && typeof p.clusters === "number");
    const tally = vp ? `${vp.published_this_run} published · ${vp.queued ?? 0} queued · ${vp.dropped ?? 0} dropped` : "";
    let inow;
    if (errored) inow = "⚠ The run hit an error.";
    else if (done) inow = `✓ Done — mock_interview.md written${tally ? ` (${tally})` : " (real, evidenced questions)"}${sfx}.`;
    else if (iGate) inow = `✋ Review the queued interview questions${tally ? ` — ${tally}` : ""}${sfx}.`;
    else if (seen.has("verify")) inow = `🔎 Verifying evidence${vc ? ` — ${vc.clusters} question clusters, corroborating sources & companies` : " — corroborating sources & companies"}…${sfx}`;
    else if (seen.has("harvest")) inow = `🌐 Harvesting real interview questions${hp ? ` — ${hp.kept} genuine candidates from the sources` : " from the sources"}…${sfx}`;
    else if (seen.has("outcomes")) inow = `🧭 Extracted the topic's key skills${sfx}.`;
    else if (seen.has("assemble")) inow = "📖 Merging the selected sessions…";
    else inow = "Starting…";
    return {
      phase: done ? "done" : "interview", inRubric: false, inVariants: false, now: inow,
      stages: INTERVIEW_STAGES.map((s) => ({ ...s, status: ist[s.key] || "pending" })),
      scored, flagged, vflagged, singleSet: false, emptySet: null,
      isPractice: false, isModule: false, isInterview: true, variantGate: false, rubricGate: false,
    };
  }
  const phase = done ? "done" : inVariants ? "variants" : inRubric ? "rubric" : "generation";

  // Single-set runs: the splitter put all content in one half (small/single-section session). The
  // empty half is skipped by design — surface it so the UI doesn't show a stuck/empty second set.
  const emptySet = splitBChars === 0 ? "set_b" : splitAChars === 0 ? "set_a" : null;
  const singleSet = emptySet !== null;

  // Per-stage status.
  const st = {};
  st.assemble = seen.has("assemble") ? "done" : "active";
  st.split = seen.has("split") ? "done" : seen.has("assemble") ? "active" : "pending";
  // Practice/module have no split: generation becomes active straight after assemble.
  const genReady = noSplit ? seen.has("assemble") : seen.has("split");
  st.generate = inRubric || genGate ? "done" : genReady ? "active" : "pending";
  st.review = inRubric ? "done" : genGate ? "active" : "pending";
  st.evaluate = (rubricDone || rubricGate || rubricFinalized) ? "done" : sawCritic ? "active" : "pending";
  st.optimize = sawOptimizer ? ((rubricDone || rubricGate || rubricFinalized) ? "done" : "active")
    : ((rubricDone || rubricGate || rubricFinalized) ? "skip" : "pending");
  st.rubric_review = rubricFinalized ? "done" : rubricGate ? "active" : "pending";
  st.variants = done || variantGate ? "done" : (sawVariant || sawVariantCritic) ? "active" : "pending";
  st.variant_review = done ? "done" : variantGate ? "active" : "pending";
  st.done = done ? "done" : "pending";

  // Practice drops Split + Variants + Variant review; module drops only Split (it keeps variants).
  const stageDefs = isPractice
    ? STAGES.filter((s) => !["split", "variants", "variant_review"].includes(s.key))
    : isModule
    ? STAGES.filter((s) => s.key !== "split")
    : STAGES;
  const stages = stageDefs.map((s) => ({ ...s, status: st[s.key] || "pending" }));

  // Plain-language "now" line.
  let now;
  if (errored) now = "⚠ The run hit an error.";
  else if (done) now = isPractice
    ? "✓ Exported — mcq_practice quiz files + portal zip written."
    : isModule
    ? "✓ Exported — module_quiz files + portal zip written."
    : "✓ Exported — set_01/set_02 files + portal zips + manager_review.html written.";
  else if (variantGate) now = vflagged > 0
    ? `✋ Variant review — ${vflagged} variant(s) flagged for your decision.`
    : "✋ Variant review — every variant passed; approve to export.";
  else if (sawVariantOpt && !variantsScored) now = `⚙ Auto-fixing variants that failed the rubric (round ${variantRound || 1})…`;
  else if (sawVariantCritic && !variantsScored) now = `⚙ Rubric-checking the variants (round ${variantRound || 1})…`;
  else if (sawVariant && !variantsScored) now = "⚙ Generating typed variants for each approved question…";
  else if (rubricFinalized && !sawVariant) now = "⚙ Handing approved questions to variant generation…";
  else if (rubricGate) now = flagged > 0
    ? `✋ Rubric review — ${flagged} question(s) flagged for your decision.`
    : "✋ Rubric review — every question passed; approve to continue.";
  else if (sawOptimizer && !rubricDone) now = `⚙ Auto-fixing questions that failed the rubric (round ${criticRound || 1})…`;
  else if (sawCritic && !rubricDone) now = `⚙ Scoring questions against the 25 rubric checkpoints (round ${criticRound || 1})…`;
  else if (collected && !sawCritic) now = "⚙ Moving approved questions into rubric scoring…";
  else if (genGate) now = "✋ Review the generated questions — accept, edit, or delete.";
  else if (seen.has("split") || (noSplit && genReady)) now = `✍ Generating questions…${genQ ? ` (${genQ} so far)` : ""}`;
  else if (seen.has("assemble")) now = isPractice
    ? "🧭 Planning the practice quiz outcomes…"
    : isModule
    ? "🧭 Consolidating the module outcomes…"
    : "🔪 Splitting the session into two halves…";
  else if (seen.size > 0) now = "📖 Assembling the session…";
  else now = "Starting…";

  // `variantGate`/`rubricGate` = those gates have been reached. Combined with the component's `atGate`,
  // they let the UI tell "still generating/scoring" (pre-gate) apart from "exporting" (post-submit) so
  // the export step isn't mislabelled — for practice (exports after the rubric gate, no variants) as well
  // as classroom/module (export after the variants gate).
  return { phase, inRubric, inVariants, now, stages, scored, flagged, vflagged, singleSet, emptySet, isPractice, isModule, isInterview: false, variantGate, rubricGate };
}
