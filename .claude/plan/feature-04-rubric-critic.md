# Feature 4 — Rubric critic phase: evaluate → optimize → rubric human gate (pre-variants)

> **Feature 4.1 refinement (UI transparency + resumability) — built & verified.**
> - **Resumability:** `run.py` tracks live drivers in `_ACTIVE` (marked synchronously in
>   start/resume/recover, discarded in `_drive`'s finally); `is_live(run_id)`. `recover_run(run_id)`
>   re-drives a stalled run with `graph.invoke(None, cfg)` from the last LangGraph checkpoint
>   (re-parks a gate or continues a dead mid-run), no-op on a live or terminal run. `POST
>   /api/agent/recover/<id>`; `get_result`/`/run` include `live`.
> - **Transparency:** `lib/pipelineState.js::derivePipeline(events)` is the single source for
>   `{phase, inRubric, now, stages}`. New `PipelineStepper.jsx` (always-visible chip row +
>   plain-language "now" line). `PipelineGraph.jsx` wrapped in `ReactFlowProvider`; an effect keyed
>   on `phase` calls `fitView({nodes: <active-cluster>})` so the view auto-focuses generation → rubric
>   (fixes the mount-only-fitView off-screen bug).
> - **Stale-state clear:** `Generate.jsx` renders the generation `SetColumn`s only when `!inRubric`;
>   once scoring starts they're removed and only rubric cards show. Done-state shows an "✋ Awaiting
>   next move — variant generation (next feature)" callout. Empty-rubric guard handled.
> - **Resume UI:** `useAgentRun` auto-recovers on open when `status==="running" && !live`; stalled
>   banner on the run view; History shows a **Resume ▸** on non-terminal rows.
> Verified: backend recover re-parks both gates (re-emitting rubric cards) + double-drive guard;
> headless UI shows the stepper narrating each phase, set-cols 2→0 at the rubric gate, the graph
> auto-focusing the rubric cluster, the awaiting-next callout, and 6 Resume buttons in History.

> **Feature 4.2 (live, never-blank questions panel) — built & verified.** The question area now
> reflects every phase the moment it happens and never blanks: `useAgentRun` seeds `sets` on the
> `split` event (topics shown immediately) and merges `outcomes` on `plan`; re-adds `criticScores`
> (per-qid band/points from `critic`) and tracks `scoringQuestions` from an enriched `collected`
> event (now carries the accepted question dicts). New `ScoringCard.jsx` renders the accepted set
> during rubric scoring with a live band chip (⏳ evaluating… → GREEN/RED·pts) — so questions
> stay visible between the generation gate and the rubric gate (was a blank gap). `Generate.jsx`
> renders by sub-phase (generation `SetColumn`s → scoring grid → rubric-gate `RubricCard`s → done).
> `SetColumn` shows topic chips (split) until outcomes (plan) and a "Generating questions…"
> placeholder. Verified headless: columns+topics visible at split before any question; **0 blank
> frames** during scoring with bands filling in live; gate → cards; done → summary.

## Context

The generation phase (split → plan → generate → concept-check → human-accept) produces
concept-checked, human-accepted MCQs. Concept-check only proves *covers its outcome + faithful to
text*. This feature adds the **quality bar**: score every accepted question against the **25
per-question rubric checkpoints** (clarity, distractor plausibility, answer validity, pedagogy),
auto-fix the failures, then put the still-failing ones in front of a human reviewer who
approves / edits / rejects. Rejections teach the system — distilled into category-tagged feedback
rules that inject into future runs and, on recurrence, **auto-refine the rubric checkpoints
themselves**.

The foundation already exists and is reused as-is:
- `domain/scoring.py` → `score_question(met, scope)` — tallies the 5 categories, applies the strict
  pass rule (**every** applicable checkpoint met), returns `category_points/band(green|red)/pass`. The
  LLM only returns `met{cp_id:bool}` + reasons; **scoring is deterministic Python**, not the model's job.
- `domain/rubric_seed.py` → the 30 checkpoints (we use the **25 per-question** ones here).
- `memory.py` → `load_rubric()`, the `("feedback",)` rule store, the `ready_for_rubric` hand-off.

This phase runs **in the same LangGraph run** as generation — a second interrupt/resume cycle on
the same `run_id`. It writes **no files** (the structured set_01/set_02 export lands with the
variants phase, next).

## Locked decisions

- **Continuation, same run.** After the generation accept-gate resumes, the graph flows straight
  into `evaluate → optimize ⟲ → rubric_gate → finalize`. Two human gates per run (generation, then
  rubric), distinguished by a `gate` discriminator on the interrupt payload.
- **Per-question only.** Score against the **25 per-question checkpoints** (4 categories: Question
  Text Quality, Options Quality, Correct Answer Validity, Pedagogy). **Defer all per-set (4.x type/
  format, 1.4 redundancy) checkpoints to the variants phase** — they're variant-dependent and
  redundancy is already covered by concept-check's distinct-outcome guarantee. Keeps scope tight.
- **No variants, no export, no files** this phase. Survivors are parked in a `ready_for_variants`
  store for the next phase; nothing is written to disk.
- **Auto-refine checkpoints.** Recurring rejection feedback in a category (hit_count ≥ threshold)
  refines a checkpoint's `met_when`/`bad_example` (or adds one) **within that category only**.
- **LLM** = `anthropic/claude-haiku-4-5` via OpenRouter (critic at temp ≈ 0 for stable verdicts).

## Flow (graph topology)

```
… process_set ×2 → human_gate(generation) ──resume(accept/edit/drop)──┐
                                                                       ▼
  collect_accepted  (apply gen decisions, distill gen feedback, build the accepted set)
        → rubric_score   (evaluate ⟲ optimize, ≤2 rounds, internal loop)
        → rubric_gate    (interrupt: reviewer approves/edits/rejects flagged Qs) ──resume──┐
                                                                                           ▼
        → finalize       (apply rubric decisions, P8 distill + checkpoint promotion,
                          park survivors in ready_for_variants, status=done)
        → END
```

The `evaluate ⟲ optimize` loop is **encapsulated inside `rubric_score`** (same pattern as
`process_set`'s internal check↔refine loop), so the graph stays flat and the loop is emitted via
SSE for the UI.

## Nodes (delta-only returns; SSE per step)

- **collect_accepted** — repurposed from today's `finalize`'s first half. Applies the generation
  gate's accept/edit/drop, distills generation feedback (concept-check not-met + human drops, as
  today), and returns the accepted `Question[]`. Does **not** park/finish (that moves to `finalize`).
- **rubric_score** — loop `round = 1..2`:
  1. **evaluate** the accepted set in batches ≤5 (one critic LLM call per batch). Each call returns
     `met{cp_id:bool}` + `reasons{cp_id:str}`; `score_question(met, "per_question")` computes
     `category_points/band/pass`. → `critic_scores{qid: CriticScore}`. SSE `critic` (qid, band,
     pass, round).
  2. **route**: questions with `pass==False` and `round<2` → **optimize**; else stop.
  3. **optimize** the failing batch (P5): regenerate **same qids** given each Q's not-met
     checkpoints + reasons + top-k category feedback rules → improved MD `-END-` blocks → reuse
     `mcq_parser` → structural-validate. SSE `optimizer` (qids, round). Loop back to evaluate.
  After the loop, questions still `pass==False` are `flagged_for_human`. Returns `{critic_scores,
  questions(updated), rubric_iteration}`.
- **rubric_gate** — build a **P9 briefing card** per question (LLM, cached on `(run_id, qid)`):
  plain-language *what's wrong* + a concrete *suggested fix* + a source excerpt, from the critic's
  failed checkpoints. `interrupt(payload={gate:"rubric", cards:[…], scores:{qid:band/category_points}})`.
  Sets `status=awaiting_human`. Flagged (red) sorted first and require a decision; passing
  (green) shown pre-marked **approve**, still editable. On resume → `{rubric_decisions}`.
- **finalize** — apply approve/edit/reject (edits re-run the structural validator). On **reject**:
  run **P8 distill** → one category-tagged ≤1-sentence rule into `("feedback",)`; if that category's
  hit_count crosses threshold, **promote** (refine/add a checkpoint in that category). Park survivors
  in `("ready_for_variants", course, session, set)`. `status=done`. SSE `finalize` (approved,
  rejected, edited, promoted_checkpoints).

## Prompts — 4 new (continue numbering; gate + feedback detailed)

`backend/agent/prompts/` — each headers the node that loads it. `llm.fill()` raises on any unbound
`{{…}}`.

| # | File | Node | In → Out |
|---|------|------|----------|
| 07 | `07_rubric_critic.md` | rubric_score (evaluate) | `{{checkpoints}}` (25 per-Q: id, criterion, met_when, good/bad example) · `{{set_content}}` (source for these Qs) · `{{questions}}` (batch ≤5 rendered) · `{{feedback_rules}}` (top-k by category) → JSON per qid: `{met:{cp_id:bool}, reasons:{cp_id:str}}` (reason only for not-met). Temp 0. |
| 08 | `08_rubric_optimize.md` | rubric_score (optimize) | `{{failing_questions}}` (each: full Q + its not-met checkpoint ids + reasons) · `{{set_content}}` · `{{feedback_rules}}` → improved MD `-END-` blocks, **same QUESTION_KEY**, fixing exactly the cited checkpoints without breaking the others. |
| 09 | `09_gate_briefing.md` | rubric_gate (P9) | `{{question}}` · `{{failed_checkpoints}}` (id + name + criterion + critic reason) · `{{source_excerpt}}` → `{summary, suggested_fix}` — plain-language, no jargon, no verdict. Cached on `(run_id, qid)`. |
| 10 | `10_rubric_feedback_distill.md` | finalize (P8) | `{{rejection}}` (Q summary + reasons + note) · `{{category}}` · `{{existing_rules}}` → `{rule, checkpoint_ref?, promote?}` — ONE generic ≤1-sentence imperative scoped to the category, no session facts. |

(Existing `06_feedback_distill.md` stays for the generation phase; #10 is the rubric-specific,
category-tagged distiller.)

**Prompt authoring style + field conventions (inspired by the variant guide).** All four prompts
are written in that guide's detailed, example-driven, checklist style:
- **Concrete good/bad examples per rule.** `07_rubric_critic` renders each checkpoint with its
  `criterion`, `met_when`, **and** the `good_example`/`bad_example` from `rubric_seed.py`.
- **Strict `-END-` field conventions for the optimizer.** `08_rubric_optimize` emits the exact
  portal block `mcq_parser` reads — preserving the original `QUESTION_KEY`, options balanced
  **50–70 chars**, **no full-stops on options**, no partial-correctness distractors, material-only
  terminology, `LEARNING_OUTCOME` **3–5 words snake_case**, `EXPLANATION` names the correct option,
  `QUESTION_TYPE` matches the answer format. Variant types stay out of scope.
- **Critic enforces the same conventions** (they are the Options/Text/Pedagogy checkpoints).
- A **closing quality checklist** in `07`/`08` mirrors the guide's "CRITICAL REMINDERS".

## Models / state additions

`domain/models.py`:
- `CriticScore` — `scope, met:{cp_id:bool}, reasons:{cp_id:str}, category_points, category_max,
  points, max_points, band, pass_` (the `score_question` shape + the LLM's met/reasons).
- `RubricDecision` — `qid, action:Literal["approve","edit","reject"], edited:Optional[Question],
  rejection_reasons:List[str], feedback_text:str`.

`domain/state.py` (declare channels — LangGraph only persists declared ones):
- `critic_scores: Dict[str, dict]` (merge by qid) · `rubric_iteration: int` ·
  `flagged_for_human: List[str]` · `rubric_decisions: Dict[str, dict]` ·
  `promoted_checkpoints: List[str]`.

## Memory + checkpoint promotion (`memory.py`)

- Extend `put_feedback_rule(...)` to carry `category` + `checkpoint_ref` (still deduped, hit_count
  bumped). `top_feedback_rules(k, category=None)` gains an optional category filter.
- **Scalable retrieval (later, non-destructive):** `put_feedback_rule` also does semantic
  evolve-in-place (paraphrase → bump existing rule + `aliases`, never a duplicate row);
  `relevant_feedback_rules(store, query, k, category)` selects rules by relevance to the failing
  reasons (hybrid: similarity + `hit_count`) when `feedback_retrieval_mode` ≠ `"frequency"`. No
  deletes; `memory_admin backfill`/`fold` are the one-time maintenance ops. See
  `memory-and-feedback-explained.md` §Scalability.
- NEW `promote_checkpoint_from_feedback(store, category, checkpoint_ref, guidance)` — when a
  category's rule hit_count ≥ `PROMOTE_THRESHOLD` (default 3): load the referenced checkpoint,
  append guidance to its `met_when`/`bad_example`, write it back. **Never crosses categories.**
  Returns the checkpoint id changed.
- NEW `put_for_variants/get_for_variants` over `("ready_for_variants", course, session, set)`.

## API (`backend/api/agent.py` + `run.py`) — two-gate handling

- The interrupt payload carries `gate: "generation" | "rubric"`. `/stream` emits `awaiting_human`
  with the gate type. `/resume` forwards the decision list to `Command(resume=…)`; the active gate
  node interprets it. No new endpoints.
- `get_result` adds `critic_scores`, a `rubric` summary (band counts, approved/rejected/edited),
  and `promoted_checkpoints`.

## Frontend

- `PipelineGraph.jsx` — extend after the generation **Accept** gate: `Evaluate ⟲ Optimize`
  (round badge + dashed ↺ loop-back arc) → `Rubric review` → `Done`.
- `useAgentRun.js` — track `gate` type from `awaiting_human`; accumulate `critic_scores`.
- `QuestionCard.jsx` — **rubric mode**: band chip, category breakdown, failed-checkpoint list with
  *what's wrong* + *suggested fix*, **Approve / Edit / Reject** controls (reject = reason + note).
- `Generate.jsx` — `gate==="rubric"` renders the rubric review panel; done summary shows band
  counts, rejected/edited, and any `promoted_checkpoints`.

## Verification

1. **CLI** full run (auto-accepts both gates): prints per-question bands + category points, shows
   the evaluate⟲optimize loop ran, asserts no files written. A second run with `PROMOTE_THRESHOLD=1`
   + an injected rejection confirms a category rule is stored and the checkpoint is refined.
2. **API**: run → `awaiting_human{gate:"generation"}` → resume → critic/optimizer events →
   `awaiting_human{gate:"rubric"}` → resume → `done`; `GET /run/<id>` returns scores + summary.
3. **UI (headless-Chrome)**: graph shows the rubric loop + second gate; cards show bands +
   checkpoints + fix + controls; done summary shows band counts + promoted checkpoint.
4. `GET /api/rubric` reflects a promoted checkpoint, promotion stayed within category.

## Out of scope (next phase)

Variant generation + their loop, the per-set checkpoints (4.x, 1.4), and the structured repo
export. Generation flow, the 6 existing prompts, ingestion, and the content API are unchanged.
