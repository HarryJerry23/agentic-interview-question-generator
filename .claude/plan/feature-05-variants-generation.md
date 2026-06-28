# Feature 5 — Variant generation, optimization, portal export & the manager deliverable

This is the single, consolidated Feature 5 plan. It covers the original variants phase and every
refinement that followed, organized as sub-features:

- **5.0** — Variant generation + variant rubric checking + portal export + manager-review report
- **5.1** — Latency + cost optimization + LangSmith observability
- **5.2** — UI/UX refinement + real-cost + run-lifecycle hardening
- **5.3** — Hotfix: Neon connection resilience ("Generate quiz does nothing")
- **5.4** — INR cost · mandatory reject-feedback · architecture demo doc · readability refactor

> Builds directly on `[[feature-04-rubric-critic]]`. Out-of-scope across the whole feature: the agent
> graph topology beyond the variants extension, prompt *content*, scoring math, export/zip formats, and
> the fixed set of variant types — unless a sub-feature says otherwise.

---

## 5.0 — Variant generation + rubric checking + portal export + manager report

### Context

The pipeline previously ended at the rubric gate (`… → rubric_gate → finalize → END`); `finalize`
parked survivors in `("ready_for_variants", …)`, set `status=done`, and the UI showed a disabled
"Generate variants" callout. This sub-feature builds the deferred final phase **plus** an end-to-end
transparency deliverable for managers.

For every rubric-approved base question: generate the **8 typed variants** (per the variant guide),
**rubric-check** them, pause at a **third human gate**, then **export** the portal files (md + json +
reading_material), the **parent-convention portal ZIPs**, and a **self-contained manager_review.html**
that documents the whole run (stages, prompts, gates, rubrics, timing, learning).

**Locked decisions:**
1. **Same run, third gate.** `finalize` no longer ends the run; flows into variants generate → score
   ⟲ optimize → variants_gate → export. Three human gates (`payload.gate` = generation | rubric |
   variants).
2. **Variant output structure is exact.** Prompts may be authored fresh, but every variant `-END-`
   block MUST use the exact portal keys (TOPIC, SUB_TOPIC, CONCEPT, QUESTION_ID/KEY,
   BASE_QUESTION_KEYS, QUESTION_TEXT, CONTENT_TYPE, QUESTION_TYPE, LEARNING_OUTCOME, CODE,
   CODE_LANGUAGE, OPTION_x[_ID], CORRECT_OPTION, EXPLANATION, BLOOM_LEVEL) — that's what the json/zip
   conversion depends on. The **8 variant types are fixed/hardcoded** (no extensibility registry).
3. **Rubric checking of variants** = per-question rubric on each variant (reuse 07/08) + per-set
   checkpoints via `score_question(scope="per_set")` (deterministic `score_variant_set`) + a
   **deterministic variant-type structural validator**.
4. **Export at the end** under the agentic app's `generated_quizzes/`: (a) set folders (reuse
   `export_set`), (b) **parent portal ZIP per set** `{session}_{set_NN}_classroom_quiz.zip` containing
   `Default_new/{session}_{set_NN}_classroom_quiz.json`, (c) **manager_review.html** (session-level —
   note: removed in 5.4, see below).
5. **Provenance**: capture EVERY LLM call (whole run) to a durable `("provenance", run_id)` Postgres
   store, so the report is rebuildable and survives recovery (Feature 4.1).

### Graph topology (graph.py)

```
… → rubric_gate → finalize → variants_generate → variants_score → variants_gate → export_finalize → END
```
`finalize` change: `status: "running"` (was `"done"`); still parks `ready_for_variants` + learns +
produces `rubric_approved`. New nodes in **backend/agent/variants.py**. The CLI auto-accept loop and
API resume already handle N gates.

### Provenance instrumentation (whole run) — NEW backend/agent/provenance.py

- `record_prompt(run_id, stage, prompt_name, filled, *, model) -> int` → append to
  `("provenance", run_id)` (key = zero-padded seq), value `{seq, stage, prompt_name, role, filled,
  model, started_at, duration_ms?, output_summary?}`, `index=False`. Returns seq.
- `record_result(run_id, seq, duration_ms, output_summary)` → patch the entry after the call.
- `get_provenance(run_id) -> list` (sorted by seq).
- Insert a `record_prompt`/`record_result` pair at **every** LLM call site: nodes.py (split, plan,
  generate [stream], concept_check, refine, distill), rubric.py (critic, optimize, briefing, distill),
  variants.py (generate, optimize, briefing). Capture is fire-and-forget (a failure to record never
  breaks the run). `role` is mapped from `prompt_name` in report.py.

### Backend variant nodes (backend/agent/variants.py, mirrors rubric.py)

- **VARIANT_TYPES** module constant — list of 8 `{suffix, label, format_hint, validator}` (tf_true,
  tf_false, sb_two, fill, multi, all, none, plus standard `v2`). Drives the generation prompt's type
  list, the validator, and the per-set variety check.
- **variants_generate** — group `rubric_approved` by `set_label`; per base question, ONE LLM call
  (prompt 11) emits the full typed variant set as `-END-` blocks → `parse_mcq_blocks` → set
  `base_question_keys = base.question_key`, `variant_type`, inherit topic/sub_topic/bloom/outcome,
  fresh `qid`. Emit `variant` SSE per block (live reveal). Returns `{variants, status:"running"}`.
- **variants_score** — evaluate ⟲ optimize (`round=1..MAX_VARIANT_ROUNDS=2`):
  - per-variant: `_run_critic_batch` (reuse) over batches → `variant_scores`.
  - `validate_variant_type(q)` (deterministic) folds a type-format failure into that variant's problems
    (T/F exactly True/False + matching correct; fill has escaped `\_\_\_\_\_\_\_`; sb_* has
    "Statement I/II"; multi is `MORE_THAN_ONE_MULTIPLE_CHOICE` + comma `CORRECT_OPTION`; all/none has
    the sentinel last option + correct = last).
  - route failing → optimize (prompt 12, preserves QUESTION_KEY + variant type); loop.
  - per-set (deterministic): `score_variant_set(variants_of_set)` builds `met` mechanically (4.1 ≥3
    distinct types; 4.2 both tf_true & tf_false present; 4.3 code shown; 4.4 met if no match type; 1.4
    distinct base concepts) → `score_question(met,"per_set")` → `set_variant_scores{label}`.
  - briefings for flagged variants (prompt 13, batched, computed before the interrupt).
- **variants_gate** — `interrupt({gate:"variants", cards[grouped by base], set_scores})`; carry full
  cards on the `awaiting_human` emit (Feature 4.2 fix). Returns `{variant_decisions}`.
- **export_finalize** — apply approve/edit/reject (edit re-runs `structural_ok` + type validator). **On
  reject the same self-learning loop as the rubric phase fires** (reuse rubric.py `_handle_rejection`):
  distill a category-tagged generic rule via prompt 10 → `put_feedback_rule(…, category,
  checkpoint_ref)` (dedup + bump `hit_count`) → `promote_checkpoint_from_feedback` when `hit_count ≥
  settings.rubric_promote_threshold` auto-refines that checkpoint's `met_when`. Then assemble per set =
  approved base (`rubric_approved`) + approved variants; then:
  - `export_set(...)` → set folders (reuse export.py).
  - **portal zip** per set (`export.py::write_portal_zip(course, session, set_label, json_items)`) →
    `generated_quizzes/{course}/{session}/classroom_quiz/{session}_{set_NN}_classroom_quiz.zip` with
    member `Default_new/{session}_{set_NN}_classroom_quiz.json` (the `build_set_files` json).
  - Emit `export` (paths + counts). Returns `{variants_approved, variants_rejected, variant_summary,
    exported, status:"done"}`.

### Memory & self-learning (variants reuse the Feature 4 loop end-to-end)

The variants phase both **reads** and **writes** the shared `("feedback",)` memory — no parallel system:
- **Read (inject):** prompts 11 (generate) + 12 (optimize) receive `{{feedback_rules}}` via
  `_fb_block(category=…)` (`top_feedback_rules`), so accumulated lessons steer variant authoring.
- **Write (learn):** a variant reject → `_handle_rejection` distills ONE category-tagged generic rule
  (prompt 10) → `put_feedback_rule(…, category, checkpoint_ref)` (deduped, `hit_count` bumped) →
  `promote_checkpoint_from_feedback` auto-refines the checkpoint's `met_when` once `hit_count ≥
  settings.rubric_promote_threshold` — **never crossing categories**. Surfaced in the report's
  "Learning" section + the done summary. Exactly the rubric phase's loop, reused.

### Manager-review report — NEW backend/agent/report.py

- `build_manager_review_html(run_id) -> str` — a **self-contained** HTML/CSS/JS document (inline styles
  + a little vanilla JS for collapsibles; opens offline, no external deps). Sections: (1) Header —
  course/session, run_id, totals, timestamp; (2) Stage timeline — ordered phases + where each of the 3
  gates triggered + reviewer decisions; (3) Prompts per stage — collapsible `<details>` revealing the
  exact filled prompt + timing; (4) Rubric checks — per-question + per-set bands + checkpoint
  definitions; (5) Learning — distilled rules + auto-promoted checkpoints. Data sources:
  `get_provenance`, `get_result`, `load_history`, `load_rubric`. Rebuildable from durable stores.
  (Originally written to a per-session file; **the per-session file is removed in 5.4** — the builder is
  kept for the in-app/cost path.)

### Prompts — 3 new (11–13), authored fresh, exact `-END-` key structure

- **11_variant_generate.md** — in: `{{base_question}}`, `{{reading_material}}`, `{{variant_types}}`,
  `{{feedback_rules}}` → full typed variant set as `-END-` blocks with exact portal keys,
  `QUESTION_KEY=<base>_<suffix>`, `BASE_QUESTION_KEYS=<base>`.
- **12_variant_optimize.md** — in: `{{failing_variants}}` (+ not-met checkpoints/reasons +
  `{{variant_type}}`), `{{reading_material}}`, `{{feedback_rules}}` → rewritten block, **same
  QUESTION_KEY + same type**.
- **13_variant_briefing.md** — mirrors 09: plain-language `{summary, suggested_fix}` per flagged variant.

### Models, state, settings, API, frontend (5.0)

- **models.py**: add `variant_type: str = ""` to `Question`; `VariantDecision` (mirror `RubricDecision`).
- **state.py**: declare channels: `variants` (merge_questions_by_qid), `variant_scores` (merge_dict),
  `set_variant_scores`, `variant_briefings`, `variant_iteration`, `variant_decisions`,
  `variants_approved`, `variants_rejected`, `variant_summary`, `exported`. Add `MAX_VARIANT_ROUNDS = 2`.
- **export.py**: add `write_portal_zip(...)`. Reuse `build_set_files`/`export_set`.
- **run.py `get_result`**: add `variants`, `variant_scores`, `set_variant_scores`, `variant_summary`,
  `exported`. The 3rd gate flows through existing `/resume/<id>`. CLI prints variant bands by base +
  per-set band + exported paths.
- **Frontend**: `lib/pipelineState.js` adds `variants`/`variant_review` stages (`finalize` no longer
  terminal); `PipelineGraph.jsx` adds a variants cluster + loop arc; `useAgentRun.js` handles
  `gate:"variants"` + `variantsByBase` (keyed by `base_question_keys`); **NEW `BaseVariantGroup.jsx`**
  (base question header + its 8 variants beneath, used live AND at the gate); **NEW `VariantCard.jsx`**
  (mirror `RubricCard`); `Generate.jsx` variants sub-phases + done summary with exported paths.

---

## 5.1 — Latency + cost optimization + LangSmith observability

**Problem.** 5.0 works, but every LLM call runs **sequentially** and makes more calls / spends more
tokens than needed (~12 min wall-clock on a real run). Both latency and cost/calls matter — app-wide.
Cost must also become **visible**.

**Locked decisions:**
- **Latency:** parallelize all independent LLM calls with a **bounded thread pool (max 6)** + auto-retry
  on transient/429s. Target ~12 min → ~3–4 min.
- **Cost (mostly lossless — same outputs):** (1) **Fewer, fuller batches** — critic scoring batch size
  **5 → 8** (`critic_batch_size`), amortizing the re-sent `set_content` + 25 checkpoints → ~⅓ fewer
  calls and input tokens; (2) **Round 2 re-scores only what changed** (the optimized subset), merged
  with round-1 passing scores — for BOTH `rubric_score` and `variants_score`; (3) **Trim the optimize
  trigger (variants only)** — auto-fix any RED / wrong-format (strict binary: any miss is RED); (4) briefings
  already fire only for non-green; keep.
- **Cost visibility:** capture **token usage per call** and show it in the report.

**Changes:**
- **NEW `backend/agent/concurrency.py`** — `pmap(fn, items, *, max_workers) -> list` (ThreadPoolExecutor,
  order-preserving, per-item exception → `None`).
- **`backend/settings.py`** — `llm_max_concurrency: int = 6`, `critic_batch_size: int = 8`,
  `price_input_per_m` + `price_output_per_m` (Haiku list price, for the $ estimate).
- **`backend/agent/llm.py`** — `max_retries=2` + `timeout=60` on `get_llm()`/`get_critic_llm()`.
- **Token capture in `backend/agent/provenance.py`** — `traced(...)` runs the call with a fresh
  `UsageMetadataCallbackHandler` via `config={"callbacks":[cb]}`, then records `input_tokens` /
  `output_tokens`. Call-site lambdas become `(_p, _cfg)` and pass `config=_cfg`. Streamed `generate`
  passes the same callback to `.stream(config=...)`. Fully backward-compatible (fields optional).
- **`backend/agent/variants.py`** — `variants_generate`: per-base loop → `pmap` over bases.
  `variants_score`: all per-question critic batches run in ONE `pmap` wave; narrow optimize trigger to
  RED/invalid; round 2 re-scores only the optimized subset and merges.
- **`backend/agent/rubric.py` `rubric_score`** — same: batches via `pmap` in one wave; round 2 re-scores
  only the optimized subset.
- **`backend/agent/events.py` — telemetry off the critical path (the big app-wide win).** Each durable
  event write is a ~300 ms round-trip to remote Neon; ~300+ events/run done synchronously added ~9 min
  of pure DB wait. Fix: a pooled `ConnectionPool` + a **background batch-writer thread** — `_persist`
  enqueues and returns instantly (live SSE still served synchronously from the in-memory bus);
  `flush_events()` is called before the report reads `load_history`. `provenance.record_result` keeps
  the in-flight row in memory (`_PENDING`) so it rewrites with one `put`. Measured: emit 337 ms → ~0 ms.
- **`backend/agent/report.py`** — NEW "Cost, calls & latency" section: per-stage table (calls,
  input/output tokens, est. $) + grand totals + a **latency-reduction metric**: `sequential_ms =
  Σ(duration_ms)` vs `wall_ms` → `saved = (1 − wall_ms/sequential_ms) × 100 %` headline. Header badge:
  `N LLM calls · ~T tokens · ~$X · ⚡ −P% latency`.

**Thread-safety:** `get_llm()`/`get_critic_llm()` are lru-cached singletons; `ChatOpenAI.invoke` is
concurrency-safe (httpx). `emit()` and `provenance.record_*` are concurrency-safe. Each node returns ONE
delta dict after its parallel calls finish.

### LangSmith observability (full tracing of every LLM call)

`langsmith` is installed and the app uses LangChain `ChatOpenAI` everywhere, so LangChain **auto-traces**
once the right env vars are present. Work = wiring them in from `.env` and turning it on at startup.

- **`backend/settings.py`** — add `langsmith_api_key: str = ""`, `langsmith_project: str =
  "agentic-mcq-workflow"`, `langsmith_tracing: bool = False`.
- **NEW `backend/agent/observability.py`** — `init_tracing()`: if enabled + key set, export
  `LANGCHAIN_TRACING_V2="true"`, `LANGCHAIN_API_KEY`, `LANGCHAIN_PROJECT`,
  `LANGCHAIN_ENDPOINT="https://api.smith.langchain.com"` **before any LLM call**. Idempotent.
- **Call `init_tracing()`** at both entrypoints: `graph.py::warm_agent()` and the top of `run.py::_cli()`.
- **EXACT place to put the key:** **`agentic-mcq-generation-workflow/.env`** (same file as
  `OPENROUTER_API_KEY`). Append (also in `.env.example`):
  ```
  # ── Observability (LangSmith tracing) — optional ──
  LANGSMITH_TRACING=true
  LANGSMITH_API_KEY=lsv2_pt_...        # ← paste your LangSmith key here
  LANGSMITH_PROJECT=agentic-mcq-workflow
  ```
  Key from smith.langchain.com → Settings → API Keys. Blank key / `LANGSMITH_TRACING=false` = off, zero
  overhead. Complementary to the in-repo provenance/report.

---

## 5.2 — UI/UX refinement + real-cost + run-lifecycle hardening

### Context

Real use surfaced refinement needs — progress vs. human-action gates look identical, the pipeline graph
reads unclearly, variants mix Set A/B together, flagged questions don't stand out, the styling feels
legacy, cost is only an *estimate*, and History shows orphaned runs as "running" (alarming re: cost). A
focused UX + observability + lifecycle pass. No change to graph topology, prompts, scoring, or export.

**Locked decisions:** (1) per-run **exact cost** via OpenRouter `usage` snapshot diff + an account
**balance badge** (key stays server-side); (2) **modern light** visual refresh; (3) **auto-reconcile**
orphaned `running` runs → `stalled` on startup, with clear History labels + Resume/Dismiss.

> Step 0: moved `.claude/specs/06-classroom-quiz-flow.html` → `.claude/plan/`.

### 1) Real cost from OpenRouter — exact $, key server-side
- **`backend/agent/cost.py` (NEW)** — `key_usage()` GETs `https://openrouter.ai/api/v1/auth/key` with the
  server's key (never exposed) → `{usage, limit, limit_remaining, …}`. `snapshot()` returns current
  `usage`; cached ~5 s.
- **Per-run exact cost (snapshot diff).** `run.py::_drive` records `usage` before/after the graph; the
  diff is the run's exact $. Persisted in a `("run_cost", run_id)` store (no migration). Caveat: when
  `>1` driver is live at finish, the diff double-counts → store `cost_usd=null` and use the token estimate.
- **API:** `GET /api/agent/cost` → live `key_usage()` (balance badge); `get_result` gains `cost_usd`
  (exact, or null) + `cost_estimate`.
- **Report:** Cost section shows exact run $ when available (else estimate), + account balance.
- **Frontend:** header **balance badge** (polled on mount); run done-summary + while-running estimate.

### 2) Run-view UX consistency — progress vs. ACTION-NEEDED
- **New `components/GateBanner.jsx`** — one prominent, **sticky** "✋ Action needed" banner, used ONLY at
  the three real gates (bold accent, CTA, one-line "what to do"). Progress states use a separate **muted
  `ProgressNote`** (spinner + neutral text) — never looks clickable.
- **Generate.jsx** — replace per-gate `review-bar` with `<GateBanner>` and progress blocks with
  `<ProgressNote>`; exactly one GateBanner visible at a time (`awaitingHuman && gate===X`).
- **Flagged highlighting:** red or `!pass` cards get a colored left-rail + ⚠ chip + "needs your
  decision" tag; passing cards calm. A "N need your decision" jump-list at the top of a gate.

### 3) Set 1 / Set 2 segregation — two columns everywhere
- **New `components/SetsLayout.jsx`** — two-column shell: **Set 1 (set_a) left, Set 2 (set_b) right**
  (stacks on narrow screens), labelled header per column.
- **Scoring grid + variants (live and gate):** split by `set_label` into the two columns; within each,
  each base question (text + options + correct answer) is a header with its 8 variants beneath
  (`BaseVariantGroup`, extended to render the base's options). Generation keeps its two columns, restyled.

### 4) Pipeline graph clarity
- **`PipelineGraph.jsx`** — clean left→right lane, three phases grouped (Generation · Rubric · Variants),
  active node highlighted, subtler loop arcs, compact legend, current-phase auto-fit. Fallback (if still
  unreadable at width): make `PipelineStepper` primary and the graph a collapsible "detailed view".

### 5) Modern light visual refresh
- **`styles/theme.css`** — refined indigo/slate palette + single accent, roomier spacing, lighter
  borders, softer shadows, modern radius; restyle cards, buttons, pills, band chips, stepper, tables,
  sidebar, gate banner. Token-driven. No structural HTML churn beyond the new components.

### 6) Traces check
- Verify LangSmith end-to-end; confirm `init_tracing()` runs before the first LLM call; document the
  `.env` lines + where to view; surface tracing on/off + project in the report header.

### 7) Run lifecycle — stalled vs running
- **`storage.py`** — `reconcile_stalled()`: `UPDATE agent_runs SET status='stalled' WHERE
  status='running'` (a live driver can't survive a restart). Called from `graph.warm_agent()`. `/runs`
  adds `live` per row via `is_live(run_id)`.
- **`api/agent.py`** — `/runs` rows include `live`; new `POST /api/agent/dismiss/<run_id>` → set terminal.
- **`History.jsx`** — status: ⏵ Running (live) · ⏸ Stalled · ⏳ Awaiting review · ✓ Done · ✗ Error;
  Stalled rows show `[Resume] [Dismiss]` + "paused — costs nothing". Reassures the cost worry.

### 8) Loopholes found — proactively addressed
- API key never reaches the browser (server-side `/api/agent/cost` proxy only; verified no key in
  `frontend/`). Per-run cost skew under concurrency → null + estimate when `>1` live. Orphaned `running`
  runs reconciled on startup (a dead thread makes no calls; live runs bounded by `MAX_*_ROUNDS`). Parked
  `awaiting_human` runs hold no thread → no cost. Background event-writer tail loss on hard kill is
  acceptable (report rebuilds from provenance + state). `key_usage()` wrapped (timeout + try/except).

---

## 5.3 — Hotfix: Neon connection resilience ("Generate quiz does nothing")

### Context

After selecting a course + session, clicking **Generate quiz** showed nothing. Server log root cause —
**Neon closes idle pooled connections** and the pools hand the dead connections back out:
```
psycopg.OperationalError: consuming input failed: SSL connection has been closed unexpectedly
  … memory.py list_sessions → store.search(...) ; list_courses → store.list_namespaces(...)
GET /api/content/sessions … 500   GET /api/content/courses … 500
```
Chain: `/api/content/sessions` 500s → dropdown empty → Generate button `disabled={!course||!session}`
→ clicking does nothing, no error shown. Root cause: `app_store()` pool had **no health-check**.

### Fix — validate/recycle pooled connections (the documented Neon fix)

`psycopg_pool.ConnectionPool` supports `check=ConnectionPool.check_connection` (liveness check on every
checkout, transparently replacing a dead connection) and `max_idle` (recycle before Neon's ~5-min
cutoff). `langgraph`'s `PoolConfig` does **not** expose `check`, so for the store we build the
`ConnectionPool` manually and pass it to `PostgresStore(pool, index=…)`. Apply `check` + `max_idle` to
**all three** long-lived pools:

- **`memory.py::app_store()`** — manual `ConnectionPool(settings.postgres_store_dsn, min_size=1,
  max_size=4, kwargs={"autocommit": True, "prepare_threshold": 0, "row_factory": dict_row},
  check=ConnectionPool.check_connection, max_idle=120, reconnect_timeout=10, open=True)` →
  `PostgresStore(pool, index={…})` → `.setup()`. Keep the module-global so it isn't GC'd.
- **`graph.py::_saver()`** — add `check=ConnectionPool.check_connection, max_idle=120` to the existing pool.
- **`events.py::_pool()`** — add the same to the durable-event writer pool.

Belt-and-suspenders read path: wrap `memory.list_courses` / `memory.list_sessions` so an `OperationalError`
retries once (`check` will have replaced the dead connection). One `_retry_once(fn)` helper.

### Frontend — never leave the user stuck silently
- **`Workspace.jsx`** — the sessions/courses fetch keeps the selection and exposes `error` + `retry()`.
- **`Sidebar.jsx`** — on `error`, show a compact "Couldn't load sessions — Retry" under the picker.

---

## 5.4 — INR cost · mandatory reject-feedback · architecture demo doc · refactor

### Context

Five refinements after the 5.x build:
1. Show the run's cost in **Rupees** (₹) alongside $, "for that particular session".
2. Make the **self-evolving learning** reliable: every **reject/delete at any gate** must capture *why*
   (generation "Delete" captured nothing; rubric/variant reject let you confirm with none).
3. The per-session `manager_review.html` "in each set" isn't the right manager artifact — instead make
   **`.claude/plan/06-classroom-quiz-flow.html` a complete, full-screen, demo-ready architecture view**
   and **stop writing the per-session report** (per-session detail lives in LangSmith).
4. Confirm session-level traces are in **LangSmith** (they are, when tracing is on).
5. A **targeted, behavior-preserving readability** pass on the most complex code.

**Locked decisions:** (1) configurable fixed `USD_TO_INR` rate (default 83.5); (2) **drop** the
per-session manager_review.html; (3) **require a reason** to reject/delete at every gate; (4) LangSmith
for session traces; (5) targeted refactor with build + one full run as the safety net.

### 1) Cost in Rupees (₹)
- **`settings.py`** — add `usd_to_inr: float = 83.5`.
- **`run.py::_cost_fields`** — add `cost_inr` (= `cost_usd * usd_to_inr`) + `cost_estimate_inr` + expose
  `usd_to_inr`.
- **`Generate.jsx` done summary** — `💰 This run cost ₹25.18 (≈$0.302, exact, OpenRouter)` (₹ primary);
  fall back to the estimate in ₹ when `cost_usd` is null.
- **`CostBadge.jsx`** — balance in ₹ too: `💳 ₹1,481 left (≈$17.73)`.
- **`report.py`** — Cost section shows ₹ alongside $. ₹ is purely a formatting layer.

### 2) Mandatory reject-feedback at every gate (self-evolving learning)
The learning loop already exists end-to-end (generation `human_reasons` → `distill_and_persist`;
rubric/variants reject → `_handle_rejection` → `put_feedback_rule` → `promote_checkpoint_from_feedback`).
The gap is the UI not *capturing* a reason on every reject. Fix the capture:
- **NEW shared `components/RejectBox.jsx`** — reason-chip picker + optional note; `canConfirm =
  reasons.length>0 || note.trim()`; **Confirm disabled until a reason is given**. Reused by all 3 cards.
- **`QuestionCard.jsx`** — "Delete" now opens `RejectBox` first; the drop carries `reason`
  (`collect_accepted` already forwards `d.reason` into `human_reasons`).
- **`RubricCard.jsx` / `VariantCard.jsx`** — replace inline reject UI with `RejectBox`; reject blocked
  until a reason given. No backend change needed.

### 3) Architecture demo doc + stop the per-session report
- **Stop writing per-session `manager_review.html`** in `variants.py::export_finalize` (keep
  `build_manager_review_html` for `get_result`/debugging). Runs still write `set_01/ set_02/` + portal
  zips.
- **`.claude/plan/06-classroom-quiz-flow.html`** is the manager deliverable — a complete, full-screen
  architecture of the as-built system: end-to-end flow (3 gates + loops), the 3 gates, the 30-checkpoint
  rubric + banding, the 8 variant types + exact portal export, the self-evolving memory loop, cost
  ₹/$ + speed + LangSmith, and the 13 prompts. (Post-5.4 the doc was redesigned into a **light/blue,
  interactive** site: a hand-built **SVG flow graph** replicating the LangGraph topology — down-spine
  pipeline, decision diamonds, dashed self-correction loop-backs, and the **Self-evolving memory
  cylinder fed by all 3 gates + a "injects learned rules" arrow back to Generate** — plus an **inline
  accordion** on the 13 prompts that reveals each prompt's Inputs → Outputs blueprint. Clicking a flow
  node opens its prompt. Self-contained, opens offline.)

### 4) LangSmith for session traces (confirm + surface)
- Confirmed: with `LANGSMITH_TRACING=true` + key in `.env`, every run is a full trace tree (per-call
  latency/tokens/cost). Documented in the architecture doc as the per-session view. No code change beyond
  a "where to look" note + the existing report header line.

### 5) Targeted readability refactor (behavior-preserving)
- **`report.py`** — split `build_manager_review_html` into small section builders (`_header`, `_timeline`,
  `_cost_section`, `_rubric_section`, `_learning_section`); same output.
- **Frontend card dedupe** — `RubricCard`/`VariantCard`/`ScoringCard` share band-chip + options +
  `RejectBox`; extract a tiny `QuestionBody`.
- **`Generate.jsx`** — pull each gate/phase block into a small helper so the main render reads as a phase
  switch.
- **`variants.py`** — tidy names/comments on the scoring/optimize/per-set helpers.
- Guardrail: no behavior change; verified by `npm run build` + one full run producing the same set
  folders + zips + bands.

---

## Verification (whole feature)

**5.0** — CLI full run (auto-accepts 3 gates) prints generation → rubric → variant bands by base +
per-set band + exported paths. Under `generated_quizzes/.../classroom_quiz/`: `set_01/` & `set_02/` each
have `classroom_quiz.md` (`-END-` blocks with QUESTION_ID/OPTION_x_ID UUIDs matching
`classroom_quiz.json`) + `reading_material.md`, base + variants present, variant keys using
`_tf_true`/`_fill`/… + `BASE_QUESTION_KEYS`; portal zips unzip to
`Default_new/{session}_set_NN_classroom_quiz.json`. Re-run replaces (not appends). API: run → gate1 →
resume → gate2 → resume → variant events → gate3 → resume → `export` → `complete`. UI narrates
Generation → Rubric → Generate variants → Variant review → Done; variants grouped-by-base with live
bands. A 0-approved run exports nothing gracefully. Unit: `validate_variant_type`, `score_variant_set`,
`write_portal_zip`, `record_prompt`/`get_provenance` round-trip.

**5.1** — wall-clock ~3–4 min; same files/zips with base+variants; report shows a Cost & calls section
with non-zero tokens + a $ estimate + the header badge; **fewer total calls** than before; no
run-aborting 429s; `pmap` preserves order + runs concurrently; round-2 merge keeps round-1 passing
scores. With tracing on, the run appears as a LangSmith trace tree; with it off, `init_tracing()` is a
silent no-op.

**5.2** — `/api/agent/cost` returns balance; on done `get_result.cost_usd` ≈ token estimate; header
badge shows balance; report shows exact run $; bad key degrades gracefully. At each gate exactly one
highlighted ACTION-NEEDED banner; progress states are muted notes; flagged cards visually distinct. Set
1 left / Set 2 right with base + its variants beneath, boxed. Graph readable (or stepper-primary
fallback). Restart → previously-`running` rows become `stalled` with Resume/Dismiss; live run shows ⏵
Running; Dismiss marks terminal.

**5.3** — restart the API; hit `/api/content/courses` + `/api/content/sessions?course=…` repeatedly →
all 200, no SSL-closed 500s; idle a few minutes then hit again → still 200. End-to-end: select course +
session → dropdown populates → Generate quiz → `POST /api/agent/run` fires → navigates to `/run/:id` →
live pipeline renders (not blank).

**5.4** — done summary shows `💰 This run cost ₹X (≈$Y, exact)`; sidebar badge ₹ balance; `get_result`
returns `cost_inr`; changing `USD_TO_INR` scales values. At each gate Reject/Delete is disabled until a
reason is chosen; after a reject a new generic rule appears in `("feedback",)` (and a checkpoint promotes
at threshold). A run writes `set_01/ set_02/` + zips but **no** `manager_review.html`.
`06-classroom-quiz-flow.html` opens full-screen, covers the as-built pipeline + 3 gates + rubric +
variants + learning + cost/₹ + LangSmith, and reads as a standalone manager demo. `npm run build` clean;
one full run yields the same exports/bands.

## Out of scope (whole feature)

A variant-type extensibility registry (the 8 are hardcoded; future types → new prompt later), the
match-the-following type (4.4 auto-met), an in-app report page/endpoint, dark theme/toggle, and any
change to generation/rubric scoring math. Memory note: `[[feature-05-variants-generation]]` linking
`[[feature-04-rubric-critic]]`.
