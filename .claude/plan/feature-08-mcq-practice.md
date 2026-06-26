# Feature 8 — MCQ Practice quiz type

> Implementation plan (approved). A second product quiz type alongside Classroom Quiz.

## Context

Today the app builds exactly one product quiz type: **Classroom Quiz** — one session is split
into **Set 1 / Set 2**, base MCQs are generated, scored by the rubric, then each approved base is
expanded into **typed variants** across **three** human gates. The specs reserve a second type in
§E: **MCQ Practice** — *full session, standalone questions, no variants*.

This implements MCQ Practice as a **separate, isolated workflow**:

1. **Whole session, no Set 1 / Set 2** — one flat question **pool** (the word "set" never appears
   in the practice path).
2. **No variants phase** — keep Plan + the two human gates (generation review + rubric review),
   skip Gate 3.
3. **All content types in the pool itself** — since there are no variants, the practice generator
   *directly* authors the mix (MCQ, match, fill-blank, T/F, statement-based, multi-select,
   all/none, + code-analysis & FIB **only when the session is code**, gated on `_detect_code`).
   Count is **agent-decided, rounded up to a multiple of 5**.

### Design principle — isolate terminology, share only the type-agnostic engine

MCQ Practice gets its **own nodes, own prompts, own `pool` label, own output folder/file names,
and its own UI rendering** — fully separate from the classroom "set" vocabulary. The only thing
shared is the genuinely type-agnostic middle of the graph: the **rubric scoring engine**
(`rubric_score` / `rubric_gate` / `finalize`) and `collect_accepted`, made **label-neutral** (they
already key off `qid`; the only coupling is three hardcoded `("set_a","set_b")` loops in
`rubric_score`, which become "iterate the labels present"). Zero terminology bleed, no duplication
of the 25-checkpoint critic loop.

### Terminology map (no confusion between the two)

| Concept            | Classroom Quiz                          | MCQ Practice                         |
|--------------------|-----------------------------------------|--------------------------------------|
| Grouping           | Set 1 / Set 2 (`set_a` / `set_b`)       | single **pool** (`pool`), no sets    |
| Gen nodes          | `split` → `process_set` ×2              | `generate_practice_pool`             |
| Generation gate    | `human_gate`                            | `practice_gate`                      |
| Plan prompt        | `02_plan_outcomes.md`                   | `16_mcq_practice_plan.md` (new)      |
| Generate prompt    | `03_generate_mcq.md`                    | `17_mcq_practice_generate.md` (new)  |
| Variants           | yes (Gate 3)                            | **none**                             |
| Export dir         | `classroom_quiz/set_01\|set_02/`        | `mcq_practice/` (single pool)        |
| Output files       | `classroom_quiz.{md,json}`              | `mcq_practice.{md,json}`             |
| Portal zip         | `{session}_{set_NN}_classroom_quiz.zip` | `{session}_mcq_practice.zip`         |
| UI                 | "Set 1 \| Set 2" columns                | "Practice questions" single list     |
| Human gates        | 3 (generation, rubric, variants)        | 2 (generation, rubric)               |

### Behaviors preserved — identical to classroom, by reusing the same nodes

MCQ Practice runs the **same full pipeline** as classroom (minus split, minus variants). Every
quality + learning behavior is inherited because practice reuses these nodes/helpers verbatim:

1. **Plan → generate** the whole session, **exactly a multiple of 5** questions (rounding guard).
2. **Concept-check ↔ refine loop** over outcomes + generated questions — **min 2, max 3 rounds**
   (`MIN_REFINE_ROUNDS=2`, `MAX_REFINE_ROUNDS=3`), reusing `_run_concept_check` / `_refine`.
3. **Generation human gate** — accept / edit / **drop (with reason)** / **improve** (Feature 6
   LLM rewrite). Reuses `collect_accepted` → `distill_and_persist` turns not-met + human reasons
   into generic feedback rules.
4. **Rubric scoring** against all 25 checkpoints, **evaluate ⟲ optimize up to 2 rounds**
   (`MAX_RUBRIC_ROUNDS=2`) — reuses `rubric_score` unchanged.
5. **Rubric human gate** — approve / edit / **reject (mandatory reason)** / improve. Reuses
   `rubric_gate`.
6. **`finalize` self-evolving loop** — `_handle_rejection` → `promote_checkpoint_from_feedback`
   (auto-refines a checkpoint on recurrence), `persist_improve_feedback` (improve distillation).
   Reused unchanged.
7. **Learned feedback fed back in** — the new practice generate prompt injects
   `feedback_rules=rules_block()` (same as `nodes.py:317`); the rubric critic/optimize inject
   `_fb_block()`. The practice flow both *contributes to* and *consumes* the self-evolving memory.
8. **Export** — on confirmation, write/overwrite the `mcq_practice` JSON **and** zip.

The only differences from classroom remain: **no Set 1/Set 2 split** and **no variants phase /
Gate 3**.

---

## Graph topology

`assemble` becomes a fork; the two branches reconverge at `collect_accepted`; `finalize` forks
again to either variants (classroom) or practice export.

```
START → assemble → [ split | generate_practice_pool ]            (route on workflow)

  classroom:  split → process_set ×2 → human_gate ─┐
  practice:        generate_practice_pool → practice_gate ─┤
                                                            ▼
  shared:                              collect_accepted → rubric_score → rubric_gate → finalize
                                                                                          │
  finalize → [ variants_generate → variants_score → variants_gate → export_finalize → END   (classroom)
             | practice_export → END ]                                                       (practice)
```

- **`backend/agent/graph.py`** — replace `START→assemble→split` edge with a conditional
  `route_after_assemble(state)` → `"split"` | `"generate_practice_pool"`. Add nodes
  `generate_practice_pool`, `practice_gate`, `practice_export`. Add `route_after_finalize(state)`
  → `"variants_generate"` | `"practice_export"`, and `practice_export → END`.

---

## Backend changes

### 1. Workflow discriminator plumbing
- **`backend/domain/state.py`** — add `workflow: str` to `QuizState` (default `"classroom_quiz"`).
- **`backend/api/agent.py`** (`run()`) — read + validate
  `workflow ∈ {"classroom_quiz","mcq_practice"}` (400 otherwise); pass to `start_run`.
- **`backend/agent/run.py`** (`start_run`) — add `workflow="classroom_quiz"` arg; include in the
  `payload`; persist on the run record (`storage.record_run` — add a `workflow` field; default
  classroom for existing rows).

### 2. New isolated practice module — `backend/agent/practice.py`
Holds the three practice-only nodes, importing helpers from `nodes.py`/`rubric.py`/`variants.py`
so nothing is duplicated:

- **`generate_practice_pool(state)`** — practice analogue of `split`+`process_set`, over the whole
  session and with no "set" vocabulary:
  1. Whole-session text = concat of `state["sections"]` (reuse the section split from `assemble`).
  2. **Plan** via `16_mcq_practice_plan.md` → outcomes; deterministic guard rounds `len(outcomes)`
     **up to the nearest multiple of 5** (min 5).
  3. **Generate** via `17_mcq_practice_generate.md` → typed pool. Pass `question_count` (rounded
     target), `text_types` (always) and `code_types` (only when `state["is_coding"]`), reusing the
     catalogs + renderers in `variants.py` (`VARIANT_TYPES`, `CODE_VARIANT_TYPES`,
     `_render_variant_types()`, `_render_code_variant_types()`). Each block ends its `QUESTION_KEY`
     in the type suffix so we reuse `_detect_suffix()` to stamp `variant_type`, and carries the
     right `QUESTION_TYPE`. Inject `feedback_rules=rules_block()`.
  4. Validate each block with `structural_ok` **and** `validate_variant_type`; drop malformed ones.
  5. **Concept-check ↔ refine** reusing `nodes._run_concept_check` / `nodes._refine` with
     `label="pool"`. Re-stamp `variant_type`/`question_type` by `question_key` after refine.
  6. Emit a practice stream event (e.g. `pool_done`). Return
     `{questions, outcome_checks, iteration:{pool:n}, set_plan:{pool:{text, outcomes, …}}}`.

- **`practice_gate(state)`** — practice analogue of `human_gate`: emit
  `{gate:"generation", workflow:"mcq_practice", questions:[…]}` (flat), `interrupt(...)`, return
  `{"human_decisions": {…}}`. Then **`collect_accepted` is reused unchanged**.

- **`practice_export(state)`** — practice analogue of `export_finalize`: take `rubric_approved`
  (label `pool`) + the pool reading text, write the single-pool folder, emit a `practice_summary`
  (`approved`, per-type counts), set `status="done"`.

### 3. Make the shared rubric engine label-neutral (only coupling to remove)
- **`backend/agent/rubric.py` `rubric_score`** — replace the three hardcoded
  `for label in ("set_a","set_b")` / `set_text("set_a")+set_text("set_b")` with a helper
  `present_labels(state)` returning the labels actually in `set_plan`. Classroom behaviour
  identical; practice gets one group.
- `rubric_gate`, `finalize`, `collect_accepted` need no change.

### 4. Export — single-pool writer
- **`backend/agent/export.py`** — generalize `export_set` / `write_portal_zip` to take the workflow
  + a quiz label so practice writes:
  ```
  generated_quizzes/{course}/{session}/mcq_practice/
      reading_material.md
      mcq_practice.md
      mcq_practice.json
      {session}_mcq_practice.zip      (member Default_new/{session}_mcq_practice.json)
  ```
  `build_set_files` is reused unchanged (already type-aware).

### 5. New isolated prompts
- **`backend/agent/prompts/16_mcq_practice_plan.md`** — plan outcomes for the **whole session**;
  instruct a **multiple-of-5** outcome count.
- **`backend/agent/prompts/17_mcq_practice_generate.md`** — author exactly `{{question_count}}`
  portal `-END-` blocks **distributed across all allowed content types** (`{{text_types}}` always;
  `{{code_types}}` only for coding sessions), one per outcome, each tagged with its type suffix and
  correct `QUESTION_TYPE`. No "set" language; no variant/base linkage.

---

## Frontend changes (dedicated practice rendering)

- **`frontend/src/lib/api.js`** — `startRun(course, session, workflow="classroom_quiz")` sends
  `workflow`.
- **`frontend/src/pages/Generate.jsx`** — add a **Classroom Quiz | MCQ Practice** segmented control
  by the Generate button; pass the choice to `startRun`. Swap the "How generation works" intro for
  practice.
- **`frontend/src/hooks/useAgentRun.js`** — surface the run's `workflow`; expose the flat `pool`
  questions + `practice_summary`.
- **Run view** — when `workflow === "mcq_practice"`, render a **dedicated single "Practice
  questions" list** (not `SetsLayout`), reusing `QuestionCard` / `RubricCard`. Generation + rubric
  gates work as-is; variants blocks never fire. Final summary shows `practice_summary` + the single
  `mcq_practice` zip download.
- `api.checkExists` — check the `mcq_practice/` dir when workflow is practice.

---

## Process — order of work (docs, HTML, skills)

1. Implement the backend, then the frontend.
2. **Update the architecture HTML** — extend `.claude/plan/06-classroom-quiz-flow.html` to also
   cover MCQ Practice (workflow toggle/section), via `/frontend-design`.
3. **Run skills after implementation**: `/frontend-design` → `/checking-correctness` →
   `/code-review` → `/reconciling-specs`.

---

## Verification (end-to-end)

1. Backend up: `. .venv/bin/activate && export PYTHONPATH=. && python -m backend.api.app`.
2. Practice run via API (non-coding session) — event log shows `generate_practice_pool` (no split),
   count a multiple of 5, varied `variant_type`s.
3. Exactly **two** interrupts (generation, rubric), no variants gate; resume to completion.
4. Coding session also includes `CODE_ANALYSIS_*` / `FIB_CODING`; theory session includes none.
5. `generated_quizzes/.../mcq_practice/{mcq_practice.md,.json,reading_material.md}` +
   `{session}_mcq_practice.zip` exist; count multiple of 5; all pass `validate_variant_type`; no
   `set_*` folders for the practice run.
6. Frontend: single "Practice questions" list, two gates, no variants UI, summary + zip download.
7. Regression: classroom run still shows the 3-gate + variants flow with Set 1 / Set 2.
