# 05 — Agent Nodes & Workflow (as-built)

> The `classroom_quiz` workflow end-to-end and each node's contract (state read → delta returned → prompt → SSE). Topology is in `01 §3`; data shapes in `02`; rubric in `04`; the full deep-dive (prompts, gates, learning demo) in `06`. The `mcq_practice` workflow is **built** (§2.5, Feature 8); the `module_quiz` workflow is **built** (§2.6, Feature 9).

## 1. The one built workflow — `classroom_quiz`

```
assemble → split → ⟨Send⟩ process_set ×2  (set_a, set_b)
        → 👤 human_gate (Gate 1) → collect_accepted
        → rubric_score ⟲ optimize → 👤 rubric_gate (Gate 2) → finalize
        → variants_generate → variants_score ⟲ optimize → 👤 variants_gate (Gate 3) → export_finalize → END
```
One session in → **Set 1 / Set 2** processed in parallel → each approved base question + its **typed variants** → portal files per set. Three mandatory human gates. All scored by the **one rubric** (35 checkpoints; `04`). **Feature 7:** in a coding session each base is classified — code-related bases get a **code variant set** (prompt 15, in the session's language), conceptual bases get the **text variant set** (prompt 11, 9 types incl. `match`); a non-coding session is unchanged.

## 2. The 15 prompts (`backend/agent/prompts/`)

Two models: **critic** (`get_critic_llm`, temp 0.0) for stable verdicts; **author** (`get_llm`, temp 0.4) for generation/rewrites. Both are `anthropic/claude-haiku-4-5` via OpenRouter.

| # | Prompt | Node / phase | Model | Inputs → Output |
|---|---|---|---|---|
| 01 | `split_session` | split | critic | `{session_title, sections, course_outcomes}` → `_SplitResult{seam_index, set_a{topics,outcomes}, set_b{…}}` |
| 02 | `plan_outcomes` | process_set | critic | `{set_label, set_content, set_topics, set_outcomes}` → `_PlanResult{outcomes[]}` (one per planned question) |
| 03 | `generate_mcq` | process_set | author | `{reading_material, learning_outcomes, question_count, feedback_rules}` → `Question[]` as `-END-` blocks (streamed live) |
| 04 | `concept_check` | process_set | critic | `{planned_outcomes, set_content, questions}` → `_CheckResult{checks:[{qid,met,reason}], confidence}` |
| 05 | `refine` | process_set | author | `{feedback_rules, set_content, not_met_questions}` → rewritten `Question[]` (same QUESTION_KEY); loop ≤ `MAX_REFINE_ROUNDS=3` |
| 06 | `feedback_distill` | collect_accepted (Gate 1) | critic | `{not_met_reasons, human_reasons}` → ≤5 generic authoring rules → `("feedback",)` |
| 07 | `rubric_critic` | rubric_score / variants_score | critic | `{set_content, checkpoints, feedback_rules, questions(≤8)}` → `_CriticBatch{scores:[{qid, problems:[{checkpoint, reason}]}]}` (failures only) |
| 08 | `rubric_optimize` | rubric_score | author | `{set_content, feedback_rules, failing_questions}` → rewritten `Question[]` (same key); loop ≤ `MAX_RUBRIC_ROUNDS=2` |
| 09 | `gate_briefing` | rubric_score (pre-gate) | critic | `{source_excerpt, flagged}` → `_BriefingBatch{cards:[{qid, summary, suggested_fix}]}` |
| 10 | `rubric_feedback_distill` | rubric_gate / variants_gate (on reject) | critic | `{category, rejection, existing_rules}` → `_DistillRule{rule, checkpoint_ref, promote}` |
| 11 | `variant_generate` | variants_generate (text bases) | author | `{reading_material, base_question, variant_types, feedback_rules}` → 9 typed `Question[]` (one per text type, incl. `match`) |
| 12 | `variant_optimize` | variants_score | author | `{reading_material, feedback_rules, failing_variants}` → rewritten variants (same key + type); loop ≤ `MAX_VARIANT_ROUNDS=2` |
| 13 | `variant_briefing` | variants_score (pre-gate) | critic | `{flagged}` → `_BriefingBatch{cards:[{qid, summary, suggested_fix}]}` |
| 14 | `improve_question` | any gate · **Improve** (Feature 6) | author | `{question, feedback, set_content, feedback_rules}` → one rewritten `Question` (`-END-`; QUESTION_KEY / variant_type preserved, re-validated; code fields preserved for code types) |
| 15 | `code_variant_generate` | variants_generate (code bases · Feature 7) | author | `{reading_material, base_question, variant_types, feedback_rules, language}` → code variants (`CODE_ANALYSIS_MULTIPLE_CHOICE` / `CODE_ANALYSIS_TEXTUAL` / `FIB_CODING`) as `-END-` blocks |

## 3. Node contracts

> Nodes return **delta-only** dicts (`02 §2`). The two `process_set` branches own disjoint `qid`s and merge via `merge_questions_by_qid`.

### assemble (`nodes.py`)
- **Does:** loads the session's exact full Markdown + ordered sections + outcomes from `("source"/"outcomes", course, session)` (full text — never sampled). Sets `content_ref`. **Feature 7:** detects whether the session is a coding session and in which language(s) via `_detect_code` (fenced code blocks; one LLM classify fallback when code is present but untagged).
- **Delta:** `{content_ref, sections, course_outcomes, session_title, is_coding, code_languages, primary_language}`. **SSE:** `assemble`.

### split (`nodes.py`) — prompt 01
- **Does:** chooses the **seam** between Set 1 and Set 2 (which sections + outcomes belong to each), full-text.
- **Delta:** `{set_plan: {set_a:{…}, set_b:{…}}}`. **SSE:** `split`.

### split_fanout → process_set ×2 (`nodes.py`) — prompts 02 → 03 → 04 ⟲ 05
- **`split_fanout`** returns `[Send("process_set", {set_label:"set_a", …}), Send("process_set", {set_label:"set_b", …})]`.
- **`process_set`** (per set, internal loop): **plan** (02) the learning outcomes → **generate** (03) one MCQ per outcome (emit `question` SSE per `-END-` block, streamed) → **concept_check** (04): each question MET/NOT-MET vs its outcome → NOT-MET routes to **refine** (05) → re-check, loop until all MET or `MAX_REFINE_ROUNDS=3` (with `MIN_REFINE_ROUNDS`). Concept-check batches run via `pmap`.
- **Delta:** `{set_plan:{label:…}, questions:[…], outcome_checks:{…}, iteration:{label:n}}`. **SSE:** `set_plan`, `question`, `concept_check`/`refine`.

### human_gate (`nodes.py`) — GATE 1
- **Does:** after both sets finish (barrier), `interrupt({gate:"generation", set_a:[…], set_b:[…]})` with each question + its concept-check → `awaiting_human`. On resume applies `{qid:{action:"accept"|"improve"|"drop", edited?, reason, feedback_text}}`. **Delete requires a reason; "improve" (Feature 6) carries the accepted LLM rewrite in `edited` + the `feedback_text` that drove it.**
- **Delta:** `{human_decisions}`. **SSE:** `awaiting_human` (carries cards).

### collect_accepted (`nodes.py`) — prompt 06
- **Does:** applies Gate-1 decisions (incl. an `improve` rewrite); distills generic authoring rules from this run's not-met + human reasons (drop reasons **and** improve feedback) (`feedback.distill_and_persist`, prompt 06) into `("feedback",)`.
- **Delta:** `{accepted, dropped, feedback_written, rubric_questions}`. **SSE:** `collect`.

### rubric_score (`rubric.py`) — prompts 07 ⟲ 08, then 09
- **Does:** per-question critic (07) over `critic_batch_size` batches via `pmap` → `score_question` → band; **RED/failing** route to **optimize** (08), then round 2 **re-scores only the changed subset** and merges (≤ `MAX_RUBRIC_ROUNDS=2`); **briefings** (09) computed for non-green before the gate.
- **Delta:** `{critic_scores, briefings, rubric_iteration, flagged_for_human}`. **SSE:** `rubric_critic`.

### rubric_gate (`rubric.py`) — GATE 2
- **Does:** `interrupt({gate:"rubric", cards:[{qid, band, failed_checkpoints, briefing, …}], flagged})`. On resume applies `{qid:{action:"approve"|"improve"|"reject", edited?, rejection_reasons, feedback_text}}`. **Reject requires a reason** → `_handle_rejection` (prompt 10) distills a category-tagged rule (`put_feedback_rule`) and may `promote_checkpoint_from_feedback`. **Improve** (Feature 6) applies the rewrite, then `improve.persist_improve_feedback` distills the feedback the same way.
- **Delta:** `{rubric_decisions, rubric_approved, rubric_rejected, rubric_summary, promoted_checkpoints}`. **SSE:** `awaiting_human`.

### finalize (`rubric.py`)
- **Does:** parks the rubric-approved survivors (grouped by set) for the variants phase. **SSE:** `finalize`.

### variants_generate (`variants.py`) — prompt 11 (text) / prompt 15 (code, Feature 7)
- **Does:** for each approved base, ONE call emits the typed variants (`-END-` blocks) with the exact portal keys, `BASE_QUESTION_KEYS=<base>`, `QUESTION_KEY=<base>_<suffix>`, inheriting topic/concept/outcome/Bloom. **Per-base dispatch (Feature 7):** in a coding session `_classify_code_bases` (one batched LLM call) labels each base; code-related bases → **prompt 15** code variant set in the session's `primary_language`, conceptual bases → **prompt 11** text set (9 types). Runs across bases via `pmap`. **Type-format auto-repair:** any freshly-generated variant that fails `validate_variant_type` (e.g. a `cotf` code True/False that came back as a 4-option MC) is retried **once** via `_repair_invalid_variants` (reuses the optimizer prompt 12, preserving its type) before it is emitted; if still invalid, it is kept and the gate flags it. Emits `variant_bases` (+ `variant_mode`) + `variant` SSE (live reveal under each base).
- **Delta:** `{variants}`. **SSE:** `variant_mode`, `variant_bases`, `variant`.

### variants_score (`variants.py`) — prompts 07 ⟲ 12, type validator, per-set, 13
- **Does:** per-variant critic (07, batched `pmap`) → `score_question`, then `apply_format_dimension` folds the deterministic **`validate_variant_type`** in as a real **+1 scored dimension** (every variant's `max_points` +1; the point is awarded only when the type-format is valid, else it's not-met → band RED). So a format-broken variant reads e.g. `28/29` red — the missing point explains the red — instead of "full points but red"; **RED/wrong-format** route to **optimize** (12, preserves key + type), round 2 re-scores the changed subset (≤ `MAX_VARIANT_ROUNDS=2`); **per-set** `score_variant_set` (4.1 ≥3 distinct types; 4.2 both T/F present; 4.3 code shown; 4.4 match; 1.4 redundancy) → `set_variant_scores`; **briefings** (13) for flagged. `score_improved` re-scores a single just-improved variant through this same path for the gate's band refresh (see `07`).
- **Delta:** `{variant_scores, set_variant_scores, variant_briefings, variant_iteration}`. **SSE:** `variant_critic`.

### variants_gate (`variants.py`) — GATE 3
- **Does:** `interrupt({gate:"variants", bases:[…], cards:[grouped by base], set_scores})`. On resume applies `{qid:{action:"approve"|"improve"|"reject", …}}`; reject → `_handle_rejection` (prompt 10), same learning loop; improve → rewrite (type preserved) + `persist_improve_feedback`. **SSE:** `awaiting_human`.

### export_finalize (`variants.py`)
- **Does:** applies Gate-3 decisions (improve re-runs `structural_ok` + type validator, then `persist_improve_feedback`); assembles per set = approved base + approved variants; writes `set_01/`+`set_02/` (md+json+reading) + the portal zips (`export.export_set`/`write_portal_zip`); `flush_events()`. **No per-session HTML file** is written (dropped in `feature-05.4`; the manager view is the architecture doc + LangSmith). Downloadable via `GET /api/agent/download/<run_id>?set=` (Feature 6).
- **Delta:** `{variants_approved, variants_rejected, variant_summary, exported, status:"done"}`. **SSE:** `export`, `complete`.

## 4. The variant types — text (`VARIANT_TYPES`) + code (`CODE_VARIANT_TYPES`, Feature 7)
**Text (9, `variants.py::VARIANT_TYPES`):** `v2` standard MCQ · `tf_true` / `tf_false` True/False (one correct each) · `sb_two` statement-based (Only I / Only II / Both / Neither) · `fill` fill-in-the-blank (escaped `\_\_\_\_\_\_\_`) · `multi` multiple-correct (`MORE_THAN_ONE_MULTIPLE_CHOICE`, comma `CORRECT_OPTION`) · `all` all-of-the-given (sentinel last option, correct = last) · `none` none-of-the-given · `match` match-the-following (List I / List II, options are mapping permutations, one correct — a single-correct `MULTIPLE_CHOICE`).

**Code (8, `variants.py::CODE_VARIANT_TYPES`) — used per-base in a coding session:** `co` output-prediction (MC) · `cotf` output-prediction (True/False) · `cerr` error-identification · `cfix` identify-and-fix · `cfun` functionality · `clogic` logic (all `CODE_ANALYSIS_MULTIPLE_CHOICE`) · `ctxt` free-text output (`CODE_ANALYSIS_TEXTUAL`, no options, INPUT/OUTPUT) · `cfib` fill-in-the-blank coding (`FIB_CODING`, one `<InlineBlank>`, OUTPUT_1).

`validate_variant_type(q)` deterministically checks each type's format (text + code + match). `apply_format_dimension` adds it to every variant's score as a real **+1 dimension** (a synthetic `"type"` checkpoint): the point is awarded when the format is valid and withheld (→ band RED) when it isn't, so the denominator reflects the requirement (e.g. `28/29` red, not `28/28` red). The `cotf` code True/False is constrained to **exactly two options** (True/False); a malformed one is auto-repaired once at generation (see `variants_generate`).

## 5. Memory & learning
Generation/optimization prompts (03, 05, 08, 11, 12) are injected with feedback rules; the critic (07) additionally receives the **rubric checkpoints** (`load_rubric`). Rule selection is controlled by `feedback_retrieval_mode`: `"frequency"` (default) = top-k by `hit_count`; `"semantic"`/`"hybrid"` = rules **most relevant to the current failure reasons** (generation stays frequency — no failure exists yet). Rules dedup non-destructively (paraphrases evolve an existing rule in place via `hit_count`+`aliases`; nothing deleted). **Nothing generated is stored.** Reject → category-tagged rule → injected next run → recurring rule promotes a checkpoint (`03 §3`, `04 §7`). What the system learned is visible at `/learned` (`GET /api/feedback-rules`). Full demo in `06 §7`.

## 2.5 The `mcq_practice` workflow (Feature 8 — built)

A `workflow` discriminator (`"classroom_quiz"` | `"mcq_practice"` | `"module_quiz"`) on the run
request forks the graph and otherwise reuses the classroom node set. Practice nodes live in
`backend/agent/practice.py`:

- **Fork after `assemble`** (`_route_after_assemble`): practice → **`generate_practice_pool`** (no `split`,
  no `process_set` fan-out). It plans the **whole session** (prompt `16_mcq_practice_plan`, count forced
  to a **multiple of 5**), generates one question per outcome **spread across all content types** (prompt
  `17_mcq_practice_generate`, reusing the variants type catalog + `validate_variant_type`; code types only
  when `is_coding`), then runs the same concept-check ↔ refine loop. Label is **`pool`** (never `set_*`).
- **`practice_gate`** — the generation gate, one flat list (no Set 1/Set 2). Feeds the shared
  `collect_accepted` → `rubric_score` → `rubric_gate` → `finalize` (all reused; `rubric_score` made
  label-neutral via `rubric.present_labels`).
- **Fork after `finalize`** (`_route_after_finalize`): practice → **`practice_export`** (writes one
  `mcq_practice/` pool: md + json + reading_material + a single portal zip) → END. The variants phase /
  Gate 3 is skipped, so a practice run has **2 gates**.

Self-evolving behaviour is identical to classroom: reject-reason distillation, improve, checkpoint
promotion, and learned-feedback injection (the pool generator gets `rules_block()`) all apply.

## 2.6 The `module_quiz` workflow (Feature 9 — built)

A third `workflow` value (`"module_quiz"`) forks the graph a third way and reuses the classroom
**variants** tail. Nodes live in `backend/agent/module.py`; the reviewer **manually multi-selects**
several sessions and **types a name** (the run/export identity; `session = slugify(module_name)`).

- **`assemble`** (merge mode) — when `workflow=="module_quiz"`, `_load_module_content` loads each
  selected session via `get_source`, concatenates them in selected order under per-session `##`
  headers, unions their outcomes (order-preserving dedupe), and **also returns a per-session list
  `module_sessions=[{title,text,outcomes}]`** (kept in state for per-session planning). Detects code
  over the merged body.
- **Fork after `assemble`** (`_route_after_assemble`): module → **`generate_module`** (no `split`).
  It plans **each session independently** (prompt `18_module_plan`, run once per session via `pmap`),
  selecting that session's **≥6 most important, assessment-worthy concepts** (floor
  `MODULE_MIN_PER_SESSION=6`, **no upper cap**); the per-session results concatenate (exact-dupes
  dropped) into the `module` outcome set. It then generates **one assessment-level base per concept**
  — **`BLOOM_LEVEL` APPLY/ANALYZE/EVALUATE with scenario stems, never REMEMBER/UNDERSTAND** (prompt
  `19_module_generate`) — and runs the same concept-check ↔ refine loop. Label is **`module`** (never
  `set_*`). `human_gate` emits a flat list for the module workflow.
- **Shared rubric + variants tail** — feeds `collect_accepted` → `rubric_score` → `rubric_gate` →
  `finalize`, then **takes the classroom variants phase** (`variants_generate` → `variants_score` →
  `variants_gate` → `export_finalize`). The 5 previously-hardcoded `("set_a","set_b")` loops in
  `variants.py` now use `rubric.present_labels(state)`, so a module run (one `module` label) flows
  through unchanged; code question types are added by the variants phase when the merge is coding.
- **Export** — `export_finalize` writes one `module_quiz/` quiz (md + json + reading_material + a
  single `{module_slug}_module_quiz.zip`). A module run has **3 gates**.

Self-evolving behaviour is identical to classroom (reject distillation, improve, promotion, learned
feedback) since the rubric + variants engine is reused verbatim.

## Definition of Done
- [ ] Every node implements its read/delta/prompt/SSE contract in §3; plan + refine live inside `process_set`.
- [ ] The `classroom_quiz` workflow runs end-to-end: assemble → split → process_set ×2 → 3 gates → export, with the §2 prompts.
- [x] The `mcq_practice` workflow (§2.5) runs end-to-end: assemble → generate_practice_pool → 2 gates → practice_export, count a multiple of 5, all content types, no variants.
- [x] The `module_quiz` workflow (§2.6) runs end-to-end: assemble (merge N sessions) → generate_module (consolidated outcomes, easy/medium/hard mix) → 3 gates → variants → export under `module_quiz/`.
- [ ] Rubric/variant loops re-score only the changed subset (≤2 rounds); concept-check⟲refine ≤3; the type validator runs on variants.
- [ ] All 3 gates fire (mandatory review); reject (mandatory reason) writes a category-tagged rule and may promote a checkpoint; export writes set folders + zips, no per-session HTML.
