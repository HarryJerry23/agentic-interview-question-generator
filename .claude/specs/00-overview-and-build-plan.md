# 00 — Overview & Build Status

> **Read this first — it's the whole picture.** What the app does, the **as-built end-to-end flow and how each stage is checked**, then **what shipped vs. what is future**. The other docs (`01`–`09`) are the detailed contracts. This document reflects the system **as actually built** (two workflows: `classroom_quiz` and `mcq_practice`). Module quizzes are **future scope** (§E), not yet implemented.

---

## A. What we're building

Quizzes used to be produced by hand (chunk a session, prompt an LLM, hand-write variants, review, convert to JSON) — slow and inconsistent. This system lets you **ingest course content once, pick a course + session, click Generate**, and have an agent split the session, write questions, **self-evaluate them against one self-evolving rubric** (35 checkpoints; the code-specific ones apply only to code questions), refine weak ones, **pause for a human reviewer at three gates**, generate typed variants per approved question — **code-analysis & fill-in-the-blank variants when the session contains code** — and emit **portal-ready files** — **learning from every rejection** (a reject distills a generic authoring rule that, on recurrence, sharpens the rubric itself).

**Product quiz types → internal workflows:**

| Product quiz type | Status | Scope | Output |
|---|---|---|---|
| **Classroom Quiz** | ✅ **Built** | 1 session → split into **Set 1 / Set 2** | each approved base question + its **typed variants** (9 text types incl. match; **8 code-analysis/FIB types** for code-related bases in a coding session); portal md + json + zip per set |
| **Module Quiz** | 🔭 **Future** (§E) | **2–3 sessions** | larger pooled set + variants |
| **MCQ Practice** | ✅ **Built** (Feature 8) | full session (one **pool**, no Set 1/Set 2) | standalone questions across **all content types** (authored directly — no variants phase); count a **multiple of 5**; portal md + json + single zip |

**Locked tech (as-built):** LangGraph (`StateGraph` + `PostgresSaver` checkpointer + `interrupt`/resume) · OpenRouter → `anthropic/claude-haiku-4-5` · embeddings `openai/text-embedding-3-small` (1536-d, via OpenRouter) · **LangGraph `PostgresStore`** as the memory layer (Neon Postgres) · Flask + SSE · React (Vite). Backend root `backend/`.

**One evaluator:** every question is scored against the **rubric** (`04`) — 35 checkpoints (30 base + 5 code-scoped that apply only to code questions) — which **lives in memory** (`PostgresStore`, seeded from `backend/domain/rubric_seed.py`). The LLM critic returns only which checkpoints **failed**; the score (category points → 🟢/🔴 band) is computed in deterministic Python (`backend/domain/scoring.py`). Human rejections distill generic, category-tagged rules that steer future generation and can **promote a rubric checkpoint**.

## B. The as-built end-to-end flow (and how each stage is checked)

One continuous LangGraph run, checkpointed to Postgres, so it can pause at a gate for hours and resume exactly where it left off. The session is **split into two sets** processed in parallel; there are **three human gates**.

```
assemble → split → ⟨Send⟩ process_set ×2  (each: plan → generate → concept-check ⟲ refine)
        → 👤 GATE 1 (generation) → collect_accepted
        → rubric_score ⟲ optimize → 👤 GATE 2 (rubric) → finalize
        → variants_generate → variants_score ⟲ optimize → 👤 GATE 3 (variants) → export_finalize → END
```

| Stage | What it does | Touches | How it's checked |
|---|---|---|---|
| **ingest** *(setup, once)* | `reading_materials/<course>/<file>.md` → heading-aware chunks → memory, keyed by `(course, session)` + title; derives outcomes | `("content",…)`, `("source",…)`, `("outcomes",…)` | the session appears in `/api/content/sessions`; selecting it loads its source |
| **assemble** | load the session's exact full Markdown + ordered sections + outcomes | `("source",…)`, `("outcomes",…)` | section list non-empty; full text loaded (never sampled) |
| **split** | partition the sections into **Set 1 / Set 2** (a seam index) | — (prompt 01) | each set has topics + outcomes |
| **process_set ×2** | per set, in parallel via `Send`: **plan** outcomes (02) → **generate** one MCQ per outcome (03, streamed) → **concept-check** (04) ⟲ **refine** (05) until each question covers its outcome (≤3 rounds) | `questions`, `outcome_checks` | each outcome has a covering question |
| **GATE 1 · generation** | reviewer sees the generated questions + concept-check; **accept / edit / delete** (delete requires a reason) | `interrupt()` + resume | resume applies decisions; reject reasons → learning |
| **collect_accepted** | apply gate-1 decisions; distill generic authoring rules from the run's reasons (06) | `("feedback",)` | accepted set carried forward; rules written |
| **rubric_score** | per-question rubric critic (07, batched) → deterministic `score_question` → band; **optimize** (08) the failures, re-score the changed subset only (≤2 rounds); briefings (09) for non-green | `critic_scores` | every checkpoint met → green, any miss → red |
| **GATE 2 · rubric** | reviewer sees each scored question (band + failed checkpoints + plain-language briefing); **approve / edit / reject** (reject requires a reason) | `interrupt()` + resume | reject → distilled category rule (10) + possible checkpoint promotion |
| **finalize** | park rubric-approved survivors for variants | `rubric_approved` | survivors grouped by set |
| **variants_generate** | for each approved base, its **typed variant set** — text (11) or, for a code-related base in a coding session, code-analysis/FIB (15) — with exact portal keys | `variants` | each base has its variant set |
| **variants_score** | per-variant rubric (07) + deterministic **type validator** + per-set checkpoints; **optimize** (12) RED/wrong-format only (≤2 rounds); briefings (13) | `variant_scores`, `set_variant_scores` | bands + per-set variety pass |
| **GATE 3 · variants** | reviewer sees each base with its variants beneath, each scored; **approve / edit / reject** | `interrupt()` + resume | reject → learning (10) |
| **export_finalize** | apply gate-3 decisions; write `set_01/` + `set_02/` (md + json + reading) + the portal zips | `exported` | files on disk + valid portal JSON |

**How "quality" is checked — two layers:** (1) **concept coverage** (concept-check ⟲ refine) ensures each planned outcome has a covering question; (2) the **rubric + pass rule** (35 checkpoints, code ones scoped to code questions; every applicable checkpoint must be met — strict binary) gates the rubric and variant phases. **Learning loop:** human reject + reason → a generic, category-tagged rule (`("feedback",)`) → injected into future generation/optimization → on recurrence (`hit_count ≥ rubric_promote_threshold`) sharpens that checkpoint's `met_when`. Generated questions are **exported, never stored in memory**.

## C. Glossary

- **Set** — one half of a session (`set_a`→`set_01`, `set_b`→`set_02`); a run produces both. **Base question** — a generated MCQ. **Variant** — one of 8 typed reformulations of a base (standard, true/false ×2, statement-based, fill-in-the-blank, multi-select, all-of, none-of).
- **Checkpoint** — one of the 30 rubric criteria (`04`), scored **met (1) / not (0)**. **Pass rule** — strict: **every** applicable checkpoint must be met. **Band** — 🟢 green (pass) / 🔴 red (any miss); no amber.
- **Outcome** — a learning outcome a question targets (planned per set). **Feedback rule** — a one-sentence authoring rule learned from a human rejection (the learned memory). **Promotion** — a recurring rule sharpening a rubric checkpoint.
- **Gate** — a LangGraph `interrupt()` for human review (classroom: 3 — generation, rubric, variants; mcq_practice: 2 — generation, rubric). **Run** — one workflow execution (one daemon thread, parked at gates).

## D. What shipped (success criteria)

A **working app** = (1) bulk-ingest `reading_materials/` into session-keyed memory; (2) from the UI, run a **classroom quiz** end-to-end → valid portal files (md + json + zip per set); (3) **three human gates** with accept/edit/reject + mandatory reject reasons; (4) every question scored against the rubric (35 checkpoints, the code-specific ones scoped to code questions; category points → 🟢/🔴); (5) reject → category-tagged feedback rule (+ checkpoint promotion on recurrence); (6) a React frontend driving all of it, never blank, with live SSE; (7) **real per-run cost** in ₹/$ (OpenRouter usage diff) + a balance badge; (8) **resilient + observable** — Neon idle-drop handling, stalled-run reconcile, optional LangSmith tracing. Each maps to a check in `09-acceptance-criteria.md`.

## E. Future scope (NOT in the build / plan folder)

These extend the **same** as-built pipeline; they are documented as future intent in the specs only:

- **Module Quiz (`module_quiz`)** — assemble **2–3 sessions** into one pooled set, balanced and de-duplicated across sessions, then run the existing split→generate→rubric→variants→export pipeline at a larger target. New logic: a multi-session **assemble** step + cross-session dedup; per-question `source_label`. (`05 §Future`, `03 §Future`.)

> **MCQ Practice (`mcq_practice`) — now built (Feature 8).** A `workflow` discriminator on the run request (validated in `api/agent.py`, threaded through `run.start_run` → `QuizState.workflow` → run record) forks the graph: `assemble` routes to `generate_practice_pool` (whole session, **no Set 1/Set 2** — label `pool`), and after the rubric gate `finalize` routes to `practice_export` instead of the variants phase. So a practice run has **2 gates** (generation + rubric, no Gate 3). **Deviation from the original sketch above:** because there are no variants, the pool generator authors **all content types directly** (reusing the variants type catalog + `validate_variant_type`), and the question count is **agent-decided, rounded to a multiple of 5** — there is **no `WORKFLOW_TARGETS` table**. The rubric, both gates' self-evolving learning loop, memory, cost, and observability are reused verbatim (the rubric was made label-neutral via `rubric.present_labels`). See `feature-08-mcq-practice.md` in the plan folder and `05 §Future`.

A `WORKFLOW_TARGETS` table is **not** used (the count is computed, not table-driven). **Deferred entirely:** within-run per-question fan-out beyond the 2-set split; cross-run batch/parallel Start; per-student pools; auth / multi-tenant; PPT/PDF ingestion (today ingestion is Markdown-tree based).

---

## F. How it was built (history)

The system shipped as one feature with refinements (see `.claude/plan/`):
1. **Ingestion + content API + frontend** — Markdown-tree ingest into `PostgresStore`; courses/sessions API; React shell. (`feature-01`, `feature-02`)
2. **Agentic generation** — split → plan → generate → concept-check ⟲ refine → Gate 1; PostgresStore memory. (`feature-03`)
3. **Rubric critic** — 30-checkpoint rubric, `score_question`, evaluate ⟲ optimize → Gate 2, the reject→distill→promote learning loop. (`feature-04`)
4. **Variants + portal export + cost/latency/observability + UX/lifecycle + ₹ + the architecture demo doc** — 8 typed variants → Gate 3 → export; bounded parallelism (`pmap`, ~−65% wall-time); exact OpenRouter cost in ₹/$; LangSmith; Neon resilience; mandatory reject-feedback; the full-screen architecture doc `.claude/plan/06-classroom-quiz-flow.html`. (`feature-05`, consolidated)
5. **Code question types** — `CODE_ANALYSIS_MULTIPLE_CHOICE` / `CODE_ANALYSIS_TEXTUAL` / `FIB_CODING` + a `match` text type; per-base, language-aware gating (coding detected in `assemble`, code-related bases classified → prompt 15); 5 code-scoped rubric checkpoints (`6.x`, `applies_to_types`) on the same self-evolving loop; type-aware, JSON-load-safe export. Non-coding sessions unchanged. (`feature-07`)
6. **Pause / Cancel / Resume a run** *(in progress — current increment)* — a reviewer can **stop** a running run: `POST /pause` halts it at the next node boundary (`status=paused`, resumable from the last checkpoint via `/recover`); `POST /cancel` stops + marks `dismissed`. The driver switches `graph.invoke`→`graph.stream` to observe a `_STOP` signal between super-steps; resume reuses the existing checkpoint/recover machinery, and a paused run reuses the stalled-run `Resume`/`Dismiss` UI. (`feature-10`)

---

### Reference map
`01` architecture · `02` data model + memory layout · `03` ingestion + session memory · `04` rubric · `05` agent nodes/workflow · `06` classroom deep-dive (incl. prompts, gates, learning demo) · `07` API + frontend · `08` infra · `09` acceptance. This doc says **what the system is**; the others say **exactly how**.
