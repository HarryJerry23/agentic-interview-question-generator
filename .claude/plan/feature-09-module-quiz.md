# Feature 9 — Module Quiz (merged-session assessment with variants)

> Implementation plan (approved + built). A third product quiz type alongside Classroom Quiz and
> MCQ Practice.

## Context

The app builds two product quiz types today: **Classroom Quiz** (one session **split** into Set 1 /
Set 2 → generate → rubric → variants → export, three gates) and **MCQ Practice** (a single **pool**,
no variants, two gates). **Module Quiz** is the assessment type at the **module** level: the reviewer
**manually selects several sessions**, their content is **merged** into one body, the LLM plans
**each session independently** and selects that session's **≥6 most important concepts** (no cap), and
one **assessment-level** base question is authored per concept (**APPLY / ANALYZE / EVALUATE — never
rote recall**), and the run then takes the **full classroom-style variants pipeline** and exports a
single merged quiz.

It is "merge" where classroom is "split", and it keeps variants where practice drops them.

### Locked decisions (from clarification Q&A)

- **Selection:** manual multi-select of ANY sessions in a course (unrestricted).
- **Identity/name:** reviewer **types a name** at run start, prefilled from the selected session
  titles (editable). Slugified → folder + History label. Does NOT use the (empty) `module` metadata.
- **Size:** **≥6 concepts selected per session** (the floor `MODULE_MIN_PER_SESSION = 6`), **no upper
  cap**; total bases = sum across sessions. Selection is **per session**, not a global dedupe.
- **Variants:** same as classroom — base → 8 typed variants per base + a separate variants gate.
- **Rubric:** reuse the existing rubric; **every** base is assessment-level (APPLY/ANALYZE/EVALUATE,
  scenario stems) — **no `BLOOM_LEVEL: REMEMBER`/`UNDERSTAND`**.
- **Code types:** auto-detect — if ANY selected session is coding, the variants phase adds code types.
- **Gates:** all three (generation → rubric → variants).
- **Merge:** concatenate sessions in selected order under per-session `##` headers.

### Design principle — reuse the (already) label-neutral engine

The rubric phase was made label-neutral in Feature 8 via `rubric.present_labels(state)`. Module Quiz
reuses the variants + rubric + export machinery by **finishing that job**: the five remaining
hardcoded `("set_a","set_b")` loops in `variants.py` now also call `present_labels(state)`. A module
run yields `present_labels → ["module"]`; classroom/practice are unchanged.

### Terminology map

| Concept          | Classroom Quiz                          | MCQ Practice                  | Module Quiz                              |
|------------------|-----------------------------------------|-------------------------------|------------------------------------------|
| Grouping         | Set 1 / Set 2 (`set_a`/`set_b`)         | single `pool`                 | single merged `module`                   |
| Input            | one session, **split**                  | one session                   | **several sessions, merged**             |
| Gen node         | `split` → `process_set` ×2              | `generate_practice_pool`      | `generate_module` (`backend/agent/module.py`) |
| Generation gate  | `human_gate`                            | `practice_gate`               | `human_gate` (module branch → flat list) |
| Plan prompt      | `02_plan_outcomes.md`                   | `16_mcq_practice_plan.md`     | `18_module_plan.md` (new, consolidates)  |
| Generate prompt  | `03_generate_mcq.md`                    | `17_mcq_practice_generate.md` | `19_module_generate.md` (new, mix)       |
| Variants         | yes (Gate 3)                            | none                          | **yes (Gate 3)** — reused               |
| Export dir       | `classroom_quiz/set_01\|set_02/`        | `mcq_practice/`               | `module_quiz/`                           |
| Output files     | `classroom_quiz.{md,json}`              | `mcq_practice.{md,json}`      | `module_quiz.{md,json}`                  |
| Portal zip       | `{session}_{set_NN}_classroom_quiz.zip` | `{session}_mcq_practice.zip`  | `{module_slug}_module_quiz.zip`          |
| UI               | "Set 1 \| Set 2" columns                | "Practice questions" list     | "Module questions" single column         |
| Human gates      | 3                                       | 2                             | 3                                        |

## Graph topology

`assemble` becomes a three-way fork; `module_quiz` joins the classroom variants tail at `finalize`.

```
START → assemble → [ split | generate_practice_pool | generate_module ]     (route on workflow)

  classroom: split → process_set ×2 → human_gate ─┐
  practice:        generate_practice_pool → practice_gate ─┤
  module:          generate_module ───────────────→ human_gate ─┤   (merged "module" body)
                                                                ▼
  shared:                       collect_accepted → rubric_score → rubric_gate → finalize
                                                                                   │
  finalize → [ variants_generate → … → export_finalize → END   (classroom AND module)
             | practice_export → END ]                          (practice)
```

- `backend/agent/graph.py` — `_route_after_assemble` adds `"module_quiz" → "generate_module"`;
  the node is registered and edged `generate_module → human_gate`. `_route_after_finalize` already
  routes the non-practice case to `variants_generate`, so module gets the variants tail unchanged.

## Backend changes

1. **Workflow + state** — `WORKFLOWS` adds `"module_quiz"` (`api/agent.py`). `QuizState` gains
   `sessions: List[str]` and `module_name: str` (`domain/state.py`); `session` carries the slugified
   module name as the run/export identity.
2. **`/run`, `/exists`, `start_run`** — for module_quiz accept `{course, sessions[], module_name}`;
   `session = slugify(module_name)`; validate non-empty. `/exists` maps `sub="module_quiz"`.
3. **`assemble`** (`nodes.py`) — `_load_module_content()` loads each selected session via
   `get_source`, concatenates in selected order under `## {title}` headers, unions outcomes
   (order-preserving dedupe), **and returns a per-session list `module_sessions=[{title,text,outcomes}]`**
   (stored in state) so planning can pick concepts from each session independently. Runs `_detect_code`
   over the merged body.
4. **`generate_module`** (new `backend/agent/module.py`, modeled on `process_set`) — PLAN **per session**
   via `18_module_plan` (each session → its ≥6 most important assessment-worthy concepts, `pmap`-parallel,
   no cap; results concatenated, exact-dupes dropped), GENERATE via `19_module_generate` (one
   **assessment-level** base per concept — APPLY/ANALYZE/EVALUATE, no rote recall), CONCEPT-CHECK ↔ REFINE
   reused from `nodes.py`. Single label `"module"`. `human_gate` emits a flat list for the module workflow
   (like `practice_gate`).
5. **Variants label-neutrality** (`variants.py`) — the 5 hardcoded `("set_a","set_b")` loops
   (`_score_variants`, optimize groups, per-set scoring, briefing excerpt, `export_finalize` export)
   now use `present_labels(state)`; `export_finalize` threads `workflow` into the export calls.
6. **Export** (`export.py`) — `export_set`/`write_portal_zip` add a `module_quiz` branch →
   `generated_quizzes/{course}/{module_slug}/module_quiz/` + `{module_slug}_module_quiz.zip`.
7. **Prompts** — `18_module_plan.md` (consolidate/dedupe outcomes across merged sessions);
   `19_module_generate.md` (base MCQs, easy/medium/hard mix). Reuse 05/06/07/08/09/10/11/12/13/15.

## Frontend changes

- `lib/api.js` — `startModuleQuiz(course, sessions, moduleName)`; `checkExists` keyed by the name.
- `pages/Generate.jsx` — a **Module Quiz** workflow option; a pre-run **multi-session checklist** +
  a **name input prefilled from the ticked session titles** (editable). A module run is "flat" (one
  `module` column) at every gate: generation, rubric, scoring, and **variants** all render a single
  column (the variants gate cannot use the set_a/set_b `SetsLayout`). Final summary + zip download.
- `context/Workspace.jsx` — `sessions` already carry `{session, session_title, module}`; module
  selection state lives locally in Generate.

## Verification (end-to-end)

1. Backend compile/import OK; `python -m backend.domain.scoring` self-checks pass.
2. `present_labels` returns `["module"]` for a module run, `["set_a","set_b"]` by default.
3. App run: pick a course, choose **Module Quiz**, tick 2–3 sessions (incl. a coding session), confirm
   the prefilled name, generate → merged assemble, consolidated outcomes, base-per-outcome with the
   difficulty mix, all three gates, variants per base (code variants for coding bases), export to
   `generated_quizzes/{course}/{module_slug}/module_quiz/` (md+json+zip).
4. Regression: a classroom run still shows Set 1 / Set 2 + variants; a practice run still exports a
   single pool — both byte-for-byte unchanged by the `present_labels` generalization.
5. `cd frontend && npm run build`.
