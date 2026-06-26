# 01 — System Architecture (as-built)

> Components, the LangGraph topology, the execution/parallelism model, SSE, and the run lifecycle — **as actually built** for the `classroom_quiz` workflow. Data shapes are in `02`; node logic in `05`; the API + React frontend in `07`. Module/MCQ workflows are future scope (`00 §E`).

## 1. Components

```
┌── React frontend (Vite) — 07 ──────────────────────────────────────────┐
│  pages (ContentLibrary · Generate/Run · History · RubricView)           │
│  + Workspace context + useAgentRun hook + EventSource (SSE)             │
└───────────────┬──────────────────────────────────────────────────────────┘
                │ REST + SSE  (Vite dev proxy → Flask)
┌───────────────▼── Flask API — 07 (backend/api/) ────────────────────────┐
│  blueprints: agent · content · rubric   (+ /api/health)                 │
└───────────────┬──────────────────────────────────────────────────────────┘
                │ start_run / resume_run / recover_run / get_result
┌───────────────▼── backend/agent/run.py — one daemon thread per run ─────┐
│  the thread invokes the graph; parks at each gate (interrupt) and       │
│  resumes on the same thread_id == run_id; _ACTIVE tracks live drivers   │
└───────────────┬───────────────────────────────────────────┬─────────────┘
                │ LLM + embeddings                            │ persistence
                ▼                                             ▼
   OpenRouter (claude-haiku-4-5,              Neon Postgres:
    text-embedding-3-small)                   · PostgresStore  (memory: content, source,
                                                outcomes, rubric, feedback, provenance, run_cost)
                                              · PostgresSaver  (graph checkpoints)
                                              · agent_runs / agent_step_events (operational)
```

Independent LLM calls inside a node fan out on a **bounded thread pool** (`backend/agent/concurrency.py::pmap`, max `llm_max_concurrency=6`) — not via per-question LangGraph `Send`. The only graph-level fan-out is the **2-way set split** (`split` → `Send("process_set")` ×2).

## 2. Backend package layout (actual)

```
backend/
  settings.py            pydantic-settings: DSNs, OpenRouter model, embeddings, concurrency,
                         batch size, prices, usd_to_inr, rubric_promote_threshold, langsmith_*
  memory.py              PostgresStore wrapper (app_store/open_store) + namespaced helpers:
                         put_chunk, get_session, get_source, list_courses/sessions,
                         seed_rubric_if_empty, load_rubric, put_feedback_rule,
                         promote_checkpoint_from_feedback, put_run_cost/get_run_cost
  agent/
    graph.py             build_graph (StateGraph + PostgresSaver pool) · warm_agent (init)
    nodes.py             assemble · split · split_fanout · process_set (plan→generate→
                         concept-check⟲refine) · human_gate · collect_accepted
    rubric.py            rubric_score (critic⟲optimize) · rubric_gate · finalize · _handle_rejection
    variants.py          variants_generate · variants_score · variants_gate · export_finalize
    llm.py               get_llm(temp 0.4) · get_critic_llm(temp 0.0) · load_prompt · fill
    mcq_parser.py        parse_mcq_blocks / parse_one_block / structural_ok  (-END- blocks)
    concurrency.py       pmap (bounded ThreadPoolExecutor)
    provenance.py        traced · record_prompt · record_result · get_provenance (token capture)
    cost.py              key_usage · snapshot · run_cost (OpenRouter /auth/key)
    events.py            RunBus (in-memory) + durable batch-writer thread + flush_events
    storage.py           ensure_schema · agent_runs/agent_step_events · list_runs · reconcile_stalled
    run.py               start_run · resume_run · recover_run · request_stop · get_result · _drive · _cost_fields
    feedback.py          distill_and_persist (generation-phase rules)
    export.py            build_set_files · export_set · write_portal_zip
    report.py            build_manager_review_html (+ section builders)
    observability.py     init_tracing (LangSmith env wiring)
    prompts/             01..15_*.md  (the 15 prompt templates)
  domain/
    state.py             QuizState (TypedDict) + reducers + MAX_*_ROUNDS
    models.py            Question · CriticScore · HumanDecision · RubricDecision · VariantDecision · …
    rubric_seed.py       Checkpoint model · 35 checkpoints (30 base + 5 code-scoped) · CATEGORY_MIN per scope
    scoring.py           score_question (category points · pass · band)
  api/
    app.py               Flask create_app · blueprint registration · /api/health
    agent.py             /api/agent: run · stream · resume · recover · dismiss · pause · cancel · cost · runs · run
    content.py           /api/content: courses · sessions · session · upload
    rubric.py            /api/rubric (GET)
  ingestion/
    cli.py               python -m backend.ingestion.cli --tree reading_materials/ …
    parse.py             chunk_markdown · extract_title · derive_outcomes · slugify
    curriculum.py        parse_curriculum (xlsx enrichment, optional)
```

`domain/` is pure (no IO, no LangGraph). There is **no** `backend/agents/`, `backend/eval/`, `backend/jobs/`, `backend/storage/`, `backend/llm/`, `backend/assembly/`, or top-level `backend/prompts/` — those were in the pre-build spec and were not built that way.

## 3. Graph topology (`backend/agent/graph.py`)

One `StateGraph(QuizState)` for `classroom_quiz`:

```
START
  → assemble          load the session's exact full Markdown + ordered sections + outcomes
  → split             choose the Set 1 / Set 2 seam (prompt 01)
  → split_fanout ──Send["process_set"]×2──▶ process_set (set_a) ∥ process_set (set_b)
        process_set (per set, internal loop):
            plan (02) → generate (03, streamed) → concept_check (04) ⟲ refine (05)   [≤ MAX_REFINE_ROUNDS=3]
  → human_gate        👤 GATE 1 — interrupt(generation): accept · edit · delete
  → collect_accepted  apply decisions; distill generic rules (06)
  → rubric_score      critic (07, batched) → score_question → band;
                      optimize (08) failures, re-score changed subset  [⟲ ≤ MAX_RUBRIC_ROUNDS=2];
                      briefings (09) for non-green
  → rubric_gate       👤 GATE 2 — interrupt(rubric): approve · edit · reject
  → finalize          park rubric_approved survivors for variants
  → variants_generate typed variants per approved base — text set (11) or code set (15, coding sessions)
  → variants_score    per-variant critic (07) + type validator + per-set checkpoints;
                      optimize (12) RED/wrong-format  [⟲ ≤ MAX_VARIANT_ROUNDS=2]; briefings (13)
  → variants_gate     👤 GATE 3 — interrupt(variants): approve · edit · reject
  → export_finalize   apply decisions; write set_01/ + set_02/ + portal zips; learn on reject (10)
  → END
```

Loop budgets live in `domain/state.py`: `MAX_REFINE_ROUNDS=3` (+ `MIN_REFINE_ROUNDS`), `MAX_RUBRIC_ROUNDS=2`, `MAX_VARIANT_ROUNDS=2`. The three gates each fire **once** (mandatory review), not "only after N failures."

**plan and refine are not separate graph nodes** — they run inside `process_set`'s internal loop. The only conditional fan-out is `split_fanout` (2 sets).

## 4. Execution & parallelism model

The pre-build spec proposed `Send` fan-out per question + a `JobManager` batch layer. **As built it is simpler:**

- **One daemon thread per run** (`run.py::start_run`) drives `graph.stream(...)` — a checkpoint-faithful substitute for `invoke` that lets the driver **stop between super-steps** (Feature 10). The thread runs to the first `interrupt` (a gate), the API returns, and the UI streams progress. `resume_run(decisions)` continues the **same** `thread_id == run_id` via `Command(resume=...)`. `_ACTIVE: set[str]` tracks which runs have a live driver (used by `recover_run` + stalled detection); `_STOP: dict[str, str]` carries a reviewer-requested `pause`/`cancel` that `_drive` observes at the next node boundary (Feature 10).
- **Bounded in-node parallelism** via `concurrency.pmap(fn, items, max_workers=llm_max_concurrency)` — a `ThreadPoolExecutor`, order-preserving, per-item exception → `None`. Used for: concept-check batches, rubric critic batches (`critic_batch_size=8`), and variant scoring. This is where the ~−65% wall-time comes from (`feature-05.1`).
- **Set-level fan-out** via LangGraph `Send`: `split_fanout` emits two `Send("process_set", …)` (set_a, set_b); the barrier after both is implicit (the graph waits before `human_gate`). Each set owns disjoint `qid`s, so the `merge_questions_by_qid` reducer never collides.
- **No cross-run batch / group runs.** One run per `POST /api/agent/run`.

`get_llm()`/`get_critic_llm()` are lru-cached singletons with `max_retries=2` + `timeout=60` (absorbs concurrent 429s). `emit()` and `provenance.record_*` are concurrency-safe.

## 5. SSE event model

- Each node calls `emit(run_id, node, payload)` (`backend/agent/events.py`) → pushed live to the run's in-memory `RunBus` queue **and** enqueued for a **background batch-writer** thread that persists to `agent_step_events` off the critical path (`flush_events()` before the report reads history).
- `GET /api/agent/stream/<run_id>` replays the durable history then tails the live bus, so a late subscriber or a reconnect sees the whole run.
- Key events: `assemble`, `split`, `set_plan`, `question` (streamed), `concept_check`/`refine`, `awaiting_human` (carries the gate discriminator + cards), `critic`/`rubric_critic`, `variant`/`variant_critic`, `variant_bases`, `export`, `stopping`/`paused`/`cancelled` (reviewer stop, Feature 10), `complete`, `error`. Payloads per node are in `07 §A.3`.

## 6. Run / job lifecycle

```
POST /api/agent/run {course, session}  → start_run → daemon thread → graph.invoke(...)
                                              ↓ interrupt (gate) → status=awaiting_human
POST /api/agent/resume/<id> {decisions} → Command(resume=decisions) → continues
                                              ↓
                                       export_finalize → status=done
POST /api/agent/recover/<id>            → re-drive from the last checkpoint if not live/terminal (also resumes a paused run)
POST /api/agent/dismiss/<id>            → mark a stale run terminal
POST /api/agent/pause/<id>              → signal the live driver to stop at the next node boundary → status=paused (resumable)
POST /api/agent/cancel/<id>             → signal stop + abandon → status=dismissed (no resume)
```

- **Reviewer pause / cancel (Feature 10):** `POST /pause` (or `/cancel`) sets `_STOP[run_id]`; the `_drive` loop checks it after each super-step and breaks — the last checkpoint is already committed, so a **pause** lands `status=paused` (resume via `/recover` re-drives from that checkpoint) and a **cancel** lands `status=dismissed`. Cost accrued up to the stop is recorded. **Granularity:** a node already in flight (e.g. a set's `pmap` generation) finishes before the stop is seen — cancellation is at **node boundaries**, not mid-LLM-call; in-flight LLM spend is sunk.
- **Checkpointing/resume:** native `PostgresSaver` keyed by `thread_id == run_id`; the gate interrupt fires on the merged state, so resume is unaffected by the set split.
- **Stalled-run reconcile:** a live driver thread cannot survive a process restart, so on startup `warm_agent()` → `reconcile_stalled()` marks orphaned `running` rows as `stalled`; `/api/agent/runs` returns `live` per row so the UI distinguishes a truly-live run from a stale label. Stalled = no thread = no spend.
- **Neon resilience:** every long-lived pool (`memory.app_store()`, the checkpointer pool, the event-writer pool) uses `check=ConnectionPool.check_connection` + `max_idle=120` so a connection Neon dropped after idle is transparently replaced (`feature-05.3`).

## 7. Cost & observability

- **Exact per-run cost:** `cost.snapshot()` reads OpenRouter `/auth/key` cumulative usage **before/after** the run; the diff is the run's exact $ (stored in the `("run_cost", run_id)` store). When `>1` driver is live at finish, the diff is ambiguous → store `null` and fall back to the **token estimate** (`provenance` tokens × `price_*_per_m`). Surfaced as `cost_usd`/`cost_inr` (× `usd_to_inr`) + `cost_estimate*`.
- **Provenance:** `traced(...)` wraps every LLM call, capturing input/output tokens (via `UsageMetadataCallbackHandler`) + duration into the `("provenance", run_id)` store — the source for the cost/latency report.
- **LangSmith (optional):** `observability.init_tracing()` exports the `LANGCHAIN_*` env vars at startup when `langsmith_tracing` + a key are set; every run becomes a full trace tree. Off by default, zero overhead.

## 8. Configuration

All knobs live in `backend/settings.py` (pydantic-settings) from `.env`: `postgres_store_dsn` (+ optional `agent_store_dsn` / `langgraph_checkpoint_dsn`, both fall back to it), `openrouter_api_key`/`openrouter_model`, `embedding_*`, `chunk_*`, `generated_quizzes_dir`, `llm_max_concurrency`, `critic_batch_size`, `price_input_per_m`/`price_output_per_m`, `usd_to_inr`, `rubric_promote_threshold`, `langsmith_*`. See `08`.

## Definition of Done
- [ ] `backend/` matches §2 (singular `agent/`, pure `domain/`); no `agents/eval/jobs/llm/assembly/storage` packages.
- [ ] The graph builds with the §3 topology: assemble → split → process_set ×2 → 3 gates → export.
- [ ] One daemon thread per run + interrupt/resume; `pmap` bounds in-node LLM parallelism; the 2-set `Send` fan-out merges via `merge_questions_by_qid`.
- [ ] SSE streams live + replays durable history; checkpoint resume works after each of the 3 gates.
- [ ] Stalled runs reconcile on startup; all pools survive Neon idle drops; exact ₹/$ cost is captured; LangSmith traces when enabled.
