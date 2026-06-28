# Feature 6 — Improve action · Download button · graph fix · single-set tidy

Four refinements on top of the as-built `classroom_quiz` workflow. Builds on
`[[feature-05-variants-generation]]`.

- **6.1** — "Improve" replaces "Edit" at all three gates (feedback → LLM rewrite → memory; self-evolving)
- **6.2** — Download button for the result zip(s) on the done screen
- **6.3** — Fix the blank pipeline graph (visibility-aware fit)
- **6.4** — Single-set runs: explain + tidy the UI (no code change to the splitter)
- **6.5** — "Already generated" warning before regenerating (open existing vs. update)

> Out of scope across the whole feature: the splitter's split logic, scoring math, export/zip format,
> the module/MCQ workflows, the fixed variant types.

---

## 6.1 — "Improve" replaces "Edit" (preview → confirm → learn)

### Context
Manual "Edit" let a reviewer change a question's text directly, but the change taught the system
nothing. **Improve** turns every change into a learning signal: the reviewer types feedback, the
author LLM rewrites *that* question per the feedback (grounded in the set source), the reviewer
previews **Original vs Improved** and accepts, and on submit the feedback is distilled into the
`("feedback",)` memory — so the next run benefits and a recurring theme can promote a rubric
checkpoint. Applies at **all three gates** (generation, rubric, variants). Edit is fully removed.

### Backend
- **`backend/agent/prompts/14_improve_question.md`** (new) — author-LLM rewrite of ONE question from
  the reviewer's feedback. Preserves `QUESTION_KEY` and (for a variant) its type/format via a
  `{{type_constraint}}` slot; emits a single portal `-END-` block. Modeled on `05_refine.md`.
- **`backend/agent/improve.py`** (new):
  - `improve_question(run_id, question, feedback, set_text) -> Question | None` — fill prompt 14, call
    `get_llm()` via `provenance.traced`, parse the first block, **merge onto the original** (preserve
    `qid`, `set_label`, `variant_type`, `base_question_keys`, `question_key`, `covers_concept`),
    validate with `mcq_parser.structural_ok` (+ `variants.validate_variant_type` when it's a variant).
    Returns `None` if it doesn't parse/validate. Reuses `rubric._fb_block()` for the learned rules.
  - `persist_improve_feedback(run_id, store, q, score, feedback, *, category="")` — distill the
    feedback into a generic, category-tagged rule (reusing `rubric._distill_rejection` /
    `_primary_failed_category` / `_first_not_met_in_category`) and `put_feedback_rule(...,
    source="human_improve")`; `promote_checkpoint_from_feedback` on recurrence. Falls back to storing
    the raw feedback as a rule if distillation yields nothing.
- **`backend/api/agent.py`**: `POST /api/agent/improve/<run_id>` `{question, feedback, gate}` — the
  **preview** endpoint. Synchronous and read-only on the run (safe while parked at a gate); resolves
  the set source from `get_result(run_id)["set_plan"][set_label]["text"]` (fallback: whole session
  text), calls `improve_question`, returns `{improved}` or `422 {error}`. **No memory write here.**
- **`backend/domain/models.py`**: the three decision models' `action` becomes
  `accept|improve|drop` (generation) / `approve|improve|reject` (rubric, variants); add
  `feedback_text` to `HumanDecision`.
- **Gate handlers** apply `improve` (apply the accepted rewrite, preserve qid/set/type) **and** learn:
  - `nodes.collect_accepted` (Gate 1) — apply `edited`, append `feedback_text` to `human_reasons`
    (already → `distill_and_persist` → memory).
  - `rubric.finalize` (Gate 2) & `variants.export_finalize` (Gate 3) — apply `edited` (re-validate;
    variants also `validate_variant_type`), then `persist_improve_feedback(...)`; fold any promoted
    checkpoint into `promoted_checkpoints`.

### Frontend
- **`lib/api.js`**: `improveQuestion(runId, {question, feedback, gate})` → POST `/improve`; (download
  helper in 6.2).
- **`components/ImproveBox.jsx`** (new, mirrors `RejectBox`): feedback textarea + **Improve** →
  `onImprove(feedback)` (spinner) → **Original vs Improved** side-by-side → **Use this** /
  **Try again** / **Discard**; inline 422 handling.
- **`QuestionCard` / `RubricCard` / `VariantCard`**: drop the inline textarea + Edit/Save; add an
  **Improve** button that opens `ImproveBox`; on confirm record
  `{qid, action:"improve", edited:<improved>, feedback_text}`. Approve/Accept + Reject/Delete
  unchanged (Reject still uses `RejectBox`).
- **`Generate.jsx`**: one `onImprove = (q, fb) => api.improveQuestion(runId, {question:q, feedback:fb,
  gate}).then(r => r.improved)` passed down through `SetColumn` / `BaseVariantGroup` to the cards.

---

## 6.2 — Download the result zip(s)

### Context
Exported zips were written to disk and only their *filename* was printed — no way to download from the
UI. Add a per-set download.

- **`backend/api/agent.py`**: `GET /api/agent/download/<run_id>?set=set_01` — resolve the path from
  `get_result(run_id)["exported"]` (so only a produced artifact is served — no path traversal) and
  `send_file(zip, as_attachment=True)`; `404` if not found.
- **`lib/api.js`**: `downloadUrl(runId, set)`.
- **`Generate.jsx`** done summary: a **⬇ Download zip** link per exported set, beside the filename.

---

## 6.3 — Fix the blank pipeline graph

### Context
The `@xyflow/react` graph lived in a **collapsed** `<details>`; React Flow can't measure a hidden
container, and `fitView` only re-ran on a phase change — so the canvas rendered blank.

- **`Generate.jsx`**: open the panel by default (`<details className="graph-details" open>`).
- **`PipelineGraph.jsx`**: a `ResizeObserver` on the `.flow-wrap` ref calls `fitView` on the active
  cluster the moment the wrapper gains width (0 → visible), covering both initial mount and a later
  expand. The existing phase-change `fitView` effect stays. Cluster selection lifted into a small
  `clusterIds(phase)` helper shared by both.

---

## 6.4 — Single-set runs: explain + tidy UI (no splitter change)

### Context
A small/single-section session ("practical software engineer") produced **one set** — expected: the
splitter skips an empty half by design (`split_fanout`). The UI showed an empty Set 2 / a
perpetually-pending Set B. We tidy the UI only.

- **`lib/pipelineState.js`**: from the `split` event's `set_a_chars`/`set_b_chars`, derive
  `singleSet` + `emptySet` (the empty half).
- **`Generate.jsx`**: when `singleSet`, show a *"Small session — generated a single set"* note and
  render only the populated column. `SetsLayout` gains an `only` prop → one full-width column for the
  rubric/variant phases.
- **`PipelineGraph.jsx`**: mark the empty set's nodes `"skip"` (muted) instead of leaving them stuck
  `"pending"`.

---

## 6.5 — "Already generated" warning before regenerating

### Context
Re-running a session silently replaced its exports. Warn first so the user chooses to **update** or
**open the existing** run. (A separate "pause the workflow" request was **dropped** by the user.)

- **`backend/api/agent.py`**: `GET /api/agent/exists?course=&session=` → `{exists, run_id?, finished_at?, zips}`.
  `exists` = a portal zip is on disk under `quizzes_dir/{course}/{session}/classroom_quiz/` **or** a
  prior **done** run exists (from `list_runs(course, session)`); `run_id` is that done run (so the UI
  can open it).
- **`lib/api.js`**: `checkExists(course, session)`.
- **`Generate.jsx`**: `start()` calls `checkExists` first; if `exists`, show a `Modal` —
  **Update — regenerate** (`reallyStart()`, replaces the files) · **Open existing run** (navigate to
  `run_id`) · **Cancel**. Otherwise start immediately as before. (+ `.modal-actions` style.)

---

## Files

- **Backend new:** `agent/prompts/14_improve_question.md`, `agent/improve.py`
- **Backend edit:** `api/agent.py` (improve + download), `domain/models.py`, `agent/nodes.py`,
  `agent/rubric.py`, `agent/variants.py`
- **Frontend new:** `components/ImproveBox.jsx`
- **Frontend edit:** `lib/api.js`, `lib/pipelineState.js`, `hooks/useAgentRun.js`, `pages/Generate.jsx`,
  `components/PipelineGraph.jsx`, `QuestionCard.jsx`, `RubricCard.jsx`, `VariantCard.jsx`,
  `SetColumn.jsx`, `BaseVariantGroup.jsx`, `SetsLayout.jsx`, `styles/theme.css`
- **Docs:** this plan, `.claude/plan/06-classroom-quiz-flow.html` (gates → approve·improve·reject; 13
  → 14 prompts; download note; single-set note), and the `.claude/specs/` via the reconciling-specs skill.

Reused (unchanged): `mcq_parser.structural_ok`, `variants.validate_variant_type`,
`memory.put_feedback_rule`/`promote_checkpoint_from_feedback`/`get_source`,
`feedback.distill_and_persist`, `rubric._distill_rejection`/`_primary_failed_category`,
`provenance.traced`, `RejectBox.jsx`, `SetsLayout.jsx`.

---

## Verification

Backend `python -m flask --app backend.api.app run --port 5001` + `cd frontend && npm run dev`:
1. **Graph** — the "Detailed pipeline view" renders (not blank), fits on screen, follows the active
   stage; collapse/expand → re-fits.
2. **Improve** — at each gate, Improve → feedback → preview rewrite → Use this → submit; the improved
   question flows downstream and the `("feedback",)` rule count grows (checkpoint may promote). No Edit
   box remains.
3. **Download** — on completion, ⬇ Download zip per set downloads
   `{session}_set_NN_classroom_quiz.zip`; `GET /api/agent/download/<run_id>?set=set_01` → 200, bad set → 404.
4. **Single set** — a small session shows the single-set note, one column, and Set B marked skipped in
   the graph (not stuck).
5. `cd frontend && npm run build` clean; backend modules import with no cycle.
