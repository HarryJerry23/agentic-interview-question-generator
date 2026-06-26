# Classroom Quiz — End-to-End Flow

> A complete walkthrough of the **`classroom_quiz`** workflow: every phase, the **three points where a
> human reviews the work**, how the system checks its own quality, the rubric, the screens, and how it
> learns. Companion to `00` (overview), `05` (node contracts), and the interactive demo at
> `.claude/plan/06-classroom-quiz-flow.html` (click any stage to see its inputs and outputs).
>
> **Related workflows.** `mcq_practice` (Feature 8, `05 §2.5`) is this flow minus the split and minus
> variants (one `pool`, 2 gates). `module_quiz` (Feature 9, `05 §2.6`) is the inverse of the split:
> instead of **splitting one session** into Set 1 / Set 2, it **merges several selected sessions** into
> one `module` body, selects the **≥6 most important concepts per session** (no cap) and authors one
> **assessment-level** base per concept (APPLY/ANALYZE/EVALUATE, no rote recall), and then reuses this
> flow's **rubric + variants + export** tail unchanged (3 gates, single `module_quiz/` export).

---

## Overview

You pick a course and a session (a single reading) and click **Generate**. From there an assistant
does the work, pausing three times for a person to make the calls:

1. It **splits the reading into two balanced halves** ("Set 1" and "Set 2") so each becomes its own
   short quiz.
2. For each half it **writes one question per learning goal**, then **checks its own questions** — does
   each one actually cover the goal it was written for? Anything weak is rewritten and re-checked.
3. **Checkpoint 1 — a human reviews the questions** and can accept, improve, or delete each one.
   Deleting asks *why*, and that reason teaches the system.
4. The accepted questions are **graded against a 30-point quality checklist** (the rubric). Anything
   that falls short is automatically rewritten and re-graded.
5. **Checkpoint 2 — a human reviews the graded questions** and approves, improves, or rejects each.
   A rejection requires a reason, which again teaches the system.
6. Each approved question is expanded into **eight different variations** (true/false, fill-in-the-blank,
   and so on), which are graded the same way.
7. **Checkpoint 3 — a human reviews the variations**, then the finished quiz is written out as
   ready-to-upload files you can download.

Two things run quietly throughout: the assistant **double-checks its own work** with automatic
fix-and-recheck loops, and it **learns from every correction** a reviewer makes (see *How the system
learns*) so the next quiz starts smarter. It never stores the questions themselves as "answers" — the
only standard it grades against is the rubric.

---

## 1. At a glance

```
  assemble ── load the session's exact full Markdown + ordered sections + outcomes
     ▼
  split ───── choose the Set 1 / Set 2 seam .................................... P01
     ▼  ⟨Send ×2⟩
  process_set (set_a) ∥ process_set (set_b)   each set, internally:
     plan outcomes (P02) → generate one MCQ/outcome (P03, streamed)
        → concept-check (P04) ── not met ─▶ refine (P05) ⟲ ≤3
     ▼  (barrier)
  👤 GATE 1 · generation  — accept · improve · delete (delete asks why) ........ P06 distill
     ▼
  rubric_score — critic (P07, batched) → score_question → band
        ── fail ─▶ optimize (P08) ⟲ ≤2 (re-score changed subset) · briefings P09
     ▼
  👤 GATE 2 · rubric  — approve · improve · reject (reason required) ........... P10 distill/promote
     ▼
  finalize → variants_generate — typed variants/approved base (text P11 · code P15) ............... P11
     ▼
  variants_score — critic (P07) + type validator + per-set; optimize P12 ⟲ ≤2; briefings P13
     ▼
  👤 GATE 3 · variants — approve · improve · reject ........................... P10 distill/promote
     ▼
  export_finalize — write set_01/ + set_02/ (md+json+reading) + portal zips
        (downloadable from the done screen — Feature 6)
```

**Loops:** concept-check⟲refine ≤3 (per set); rubric evaluate⟲optimize ≤2; variant evaluate⟲optimize ≤2. **Memory writes:** only at the gates — a category-tagged feedback rule (which may promote a checkpoint) from a **reject or an improve** (Feature 6: feedback → LLM rewrite via P14 → memory). **Quality gate:** the rubric (35 checkpoints; code ones scoped to code questions), scored in Python from the critic's failures-only output.

---

## 2. How a run starts (inputs)

`POST /api/agent/run` — just the addressing:
```jsonc
{ "course": "building_llm_applications",
  "session": "integrating_mcp" }
```
- The session must already be ingested (its full source lives in `("source", course, session)`). Selecting it in the UI is what `assemble` loads.
- No params, no `set_name`, no `workflow` field — the run produces **both sets** (`set_a`→`set_01`, `set_b`→`set_02`) of the `classroom_quiz` when the session is large enough to split; a **small/single-section session yields a single set** (the empty half is skipped by `split_fanout` — by design, surfaced in the UI; Feature 6). A re-run **replaces** that session's exports.

---

## 3. Nodes & prompts

| Node (file) | Role | Prompt(s) |
|---|---|---|
| `assemble` (nodes.py) | load full source + sections + outcomes | — |
| `split` (nodes.py) | choose the Set 1 / Set 2 seam | **P01** |
| `process_set` (nodes.py) | per set: plan → generate → concept-check ⟲ refine | **P02, P03, P04, P05** |
| `human_gate` (nodes.py) | GATE 1 — generation review | — (interrupt) |
| `collect_accepted` (nodes.py) | apply Gate-1 decisions; distill rules | **P06** |
| `rubric_score` (rubric.py) | per-question rubric ⟲ optimize; briefings | **P07, P08, P09** |
| `rubric_gate` (rubric.py) | GATE 2 — rubric review; learn on reject | **P10** |
| `finalize` (rubric.py) | park approved survivors for variants | — |
| `variants_generate` (variants.py) | typed variants per approved base — text or code-analysis/FIB | **P11 · P15** |
| `variants_score` (variants.py) | per-variant rubric + type validator + per-set; optimize; briefings | **P07, P12, P13** |
| `variants_gate` (variants.py) | GATE 3 — variants review; learn on reject/improve | **P10** |
| `export_finalize` (variants.py) | write set folders + portal zips | — |
| `improve` (improve.py · any gate) | rewrite one question from reviewer feedback (Feature 6) | **P14** |

The full input→output blueprint for each of the 15 prompts is in `05 §2` and is browsable interactively in `.claude/plan/06-classroom-quiz-flow.html`.

**Notes (apply to all generators/critics):**
- **Portal `-END-` blocks.** Generators (P03, P05, P08, P11, P12) emit `-END-`-delimited Markdown parsed by `mcq_parser.parse_mcq_blocks`; `structural_ok()` validates exactly-one-correct (≥1 multi), 3–5 unique options, non-empty explanation, base↔variant link.
- **Critic returns failures only.** P07 returns just the failed checkpoints; `score_question` (Python) computes points/band/pass.
- **Rewrites preserve keys.** P05/P08/P12 return the **same QUESTION_KEY** (P12 also the same variant type) → the reducer upserts in place.
- **Feedback injected top-rules** (deduped) so prompts don't grow unbounded.
- **Two temps:** critic 0.0 (stable verdicts), author 0.4 (variety).

---

## 4. Phase by phase

**assemble + split.** Load the exact full session Markdown (never sampled); P01 chooses the seam so Set 1 and Set 2 are coherent, balanced halves with their own topics + outcomes.

**process_set ×2 (parallel via `Send`).** Per set: P02 plans the learning outcomes (one question per outcome); P03 generates one MCQ per outcome (streamed live to the UI as each `-END-` block arrives); P04 concept-checks each question MET/NOT-MET against its outcome; NOT-MET questions go to P05 refine and re-check, looping until all MET or `MAX_REFINE_ROUNDS=3`. Concept-check runs batched via `pmap`. Each set owns disjoint `qid`s.

**GATE 1 · generation.** After both sets finish, the run pauses. The reviewer sees the questions in a **Set 1 / Set 2** two-column view with each question's concept-check, and chooses **accept / improve / delete**. Improve (Feature 6) asks for feedback → P14 rewrites the question → the reviewer confirms; deleting asks **why**. Both feed learning. `collect_accepted` applies the decisions and distills generic authoring rules (P06) from the run's not-met + human reasons (drop reasons + improve feedback).

**rubric_score.** The accepted questions are scored against the 25 per-question checkpoints (P07, batched 8/call via `pmap`); `score_question` bands each green (all met) / red (any miss). Failures (any RED) are rewritten by P08 optimize; round 2 **re-scores only the changed subset** and merges (≤ `MAX_RUBRIC_ROUNDS=2`). P09 writes a plain-language "what's wrong + suggested fix" briefing for every non-green question.

**GATE 2 · rubric.** The reviewer sees each question with its band, failed checkpoints, and briefing, and chooses **approve / improve / reject**. **Reject requires a reason** → `_handle_rejection` distills a category-tagged rule (P10) into `("feedback",)` and, on recurrence (`hit_count ≥ rubric_promote_threshold`), promotes that checkpoint's `met_when`. **Improve** (Feature 6) applies the P14 rewrite and distills the feedback the same way (`improve.persist_improve_feedback`). `finalize` parks the approved survivors.

**variants_generate.** For each code-related base in a coding session, P15 emits the code-analysis/FIB variant set; otherwise P11 emits the 9 text variants with exact portal keys, run across bases via `pmap`, streamed under each base in the UI.

**variants_score.** Each variant is scored by P07 plus the deterministic `validate_variant_type`; `score_variant_set` adds the per-set checkpoints (≥3 distinct types, both T/F present, code shown, redundancy). RED/wrong-format variants are rewritten by P12 (same type), re-scored on the changed subset (≤ `MAX_VARIANT_ROUNDS=2`); P13 briefs the flagged ones.

**GATE 3 · variants.** The reviewer sees each approved base with its variants beneath it, each scored, and chooses **approve / improve / reject** (same learning loop — P10 for reject, P14 + `persist_improve_feedback` for improve; variant type preserved).

**export_finalize.** Applies the decisions and writes, per set: `reading_material.md` + `classroom_quiz.md` (`-END-`) + `classroom_quiz.json` (shared UUIDs) + the portal zip (`Default_new/…json` member). A re-run replaces the set folders. **No per-session HTML** is written. The zips are **downloadable from the done screen** via `GET /api/agent/download/<run_id>?set=` (Feature 6).

---

## 5. The rubric (recap — full detail in `04`)
25 per-question checkpoints in 4 categories (Question Text 9 · Options 8 · Answer Validity 3 · Pedagogy 5) + 5 per-set (redundancy 1.4 · Type & Format 4.1–4.4) + **5 code-scoped (`6.x`, "Code Question Quality")** that apply only to code question types (Feature 7) — so a text question's applicable max is 25, a code-analysis MC's is 28, a FIB's is 29. Pass = **every** applicable checkpoint met (strict binary — no minimums). Band: 🟢 all met · 🔴 any miss. No amber. The LLM returns only failures; Python scores.

---

## 6. The variant types & portal export
**Text (9):** `v2` standard · `tf_true`/`tf_false` True/False · `sb_two` statement-based · `fill` fill-in-the-blank · `multi` multiple-correct · `all` all-of · `none` none-of · `match` match-the-following. **Code (8, Feature 7 — code-related bases in a coding session):** `co`/`cotf` output-prediction (MC / True-False) · `cerr` error-id · `cfix` fix · `cfun` functionality · `clogic` logic (all `CODE_ANALYSIS_MULTIPLE_CHOICE`) · `ctxt` free-text output (`CODE_ANALYSIS_TEXTUAL`) · `cfib` fill-in-the-blank coding (`FIB_CODING`). Each ships with the exact portal field keys (option-less code types export `options:[]` + `expected_output`), so the json/zip conversion is a direct mapping. Export layout + JSON shape: `02 §6–§7`.

---

## 7. Memory-feedback demo (verified)
A reviewer rejects a question at Gate 2 with reason "weak distractor / distractors too obviously wrong." `_handle_rejection` distills the rule *"Ensure every distractor is plausibly wrong based on common misconceptions, not obviously incorrect"*, tagged to **Options Quality / 2.5**, stored in `("feedback",)` (rule count 31 → 32). It is injected into P03/P08 next run; if "weak distractor" rejections recur past the threshold, checkpoint **2.5**'s `met_when` is sharpened in memory — the rubric the agent applies tomorrow is shaped by today's rejections. (This loop fires identically at all three gates.)

---

## 8. Cost, speed & observability
- **Exact cost:** the run snapshots OpenRouter `/auth/key` usage before/after → the run's exact $ (or the token estimate when >1 driver is live), shown in **₹ and $** (`💰 This run cost ₹X (≈$Y, exact)`) + a balance badge. Rate `usd_to_inr` is configurable.
- **Speed:** independent calls run on a bounded thread pool (`pmap`); round 2 re-scores only what changed; telemetry writes are batched off the critical path → ~−65% wall-time.
- **Traces:** with `langsmith_tracing` on, every run is a full LangSmith trace tree (per-call latency/tokens/cost) — the per-session drill-down.

---

## 9. The UI screens (`07` for full contracts)
- **Content Library** (`/`) — courses/sessions; upload/paste Markdown.
- **Generate / Run** (`/generate`, `/run/:id`) — pick course + session → Generate; then the **live run**: a `PipelineGraph`/`PipelineStepper`, questions streaming into a **Set 1 / Set 2** layout (`SetsLayout`/`SetColumn`; a **single-set** run shows one column + a note), a single **`GateBanner`** ("✋ Action needed") at each of the 3 gates with `QuestionCard`/`RubricCard`/`VariantCard` (band chips, failed checkpoints, briefing) + the shared **`RejectBox`** (a reason is required to reject/delete) and the shared **`ImproveBox`** (Feature 6 — type feedback → preview the rewrite → Use this), variants grouped under each base (`BaseVariantGroup`), and a done summary with the ₹ cost + exported paths + a **⬇ Download zip** button per set. Progress states use a muted `ProgressNote`, never confusable with a gate. The `PipelineGraph` is open by default and re-fits when shown (Feature 6 fix).
- **History** (`/history`) — past runs with status (⏵ running · ⏸ stalled · ⏳ awaiting review · ✓ done · ✗ error); stalled rows offer Resume/Dismiss (stalled = no spend).
- **Rubric** (`/rubric`) — the rubric checkpoints (all required to pass) from `/api/rubric`.

---

## Definition of Done
- [ ] A classroom run goes assemble → split → process_set ×2 → Gate 1 → rubric ⟲ → Gate 2 → variants ⟲ → Gate 3 → export, end-to-end from the UI.
- [ ] Both sets are produced (set_01/set_02); each approved base ships with its typed variants; portal md+json+zip per set are valid.
- [ ] All 3 gates pause the run with a single clear action banner; reject/delete requires a reason; a reject writes a category rule (and promotes a checkpoint on recurrence).
- [ ] The run shows its exact ₹/$ cost; LangSmith traces when enabled; the interactive architecture doc reflects this flow.
