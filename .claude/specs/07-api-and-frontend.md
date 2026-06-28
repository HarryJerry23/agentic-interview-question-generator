# 07 — HTTP/SSE API + React Frontend (as-built)

> The Flask blueprints **and** the React app that drives them. Internal tool — no auth; `run_id` acts as a capability. Base: Flask on `:5001`; the Vite dev server (`:5173`) proxies `/api` to it. The classroom flow is in `06`.

---

# Part A — API (`backend/api/`)

## A.1 Agent endpoints (`api/agent.py`, prefix `/api/agent`)

### POST `/run` — start one run
```jsonc
// classroom_quiz (default) | mcq_practice
{ "course": "building_llm_applications", "session": "integrating_mcp", "workflow": "classroom_quiz" }
// module_quiz (Feature 9) — merge several sessions; module_name is the run/export identity
{ "course": "building_llm_applications", "sessions": ["intro_to_langchain", "integrating_mcp"],
  "module_name": "Module 1 — LangChain Basics", "workflow": "module_quiz" }
// 201
{ "run_id": "…" }
```
Spawns one daemon thread (`run.start_run`) that drives the graph to the first gate. The `workflow` field selects the branch (`classroom_quiz` | `mcq_practice` | `module_quiz`); module_quiz takes `sessions[]` + `module_name` instead of a single `session` (`session = slugify(module_name)`). No `set_name`/`params` field, no `/run-batch`, no group runs. `/exists` is keyed by `(course, session-or-module-slug, workflow)`.

### GET `/stream/<run_id>` — SSE
Replays the durable history (`agent_step_events`) then tails the live `RunBus`. Events: `assemble`, `split`, `set_plan`, `question`, `concept_check`/`refine`, `rubric_critic`, `variant_bases`, `variant`, `variant_critic`, `awaiting_human` (carries the gate discriminator + cards), `export`, `complete`, `error`.

### POST `/resume/<run_id>` — resume after a gate
```jsonc
{ "decisions": {
    "<qid>": {"action": "accept",  ... },                                 // Gate 1: accept|improve|drop
    "<qid>": {"action": "reject", "rejection_reasons": ["weak_distractor"], "feedback_text": "…"},  // Gate 2/3: approve|improve|reject
    "<qid>": {"action": "improve", "edited": { /* rewritten Question */ }, "feedback_text": "…"} } }
// 202 → continues the run on the same thread_id; stream resumes
```
**A reason is required to reject (Gates 2/3) or delete (Gate 1)** — enforced in the UI (`RejectBox`). **Improve** (Feature 6) carries the accepted LLM rewrite in `edited` + the `feedback_text` that drove it; the feedback is distilled into memory on submit. Both reject and improve drive the learning loop.

### Other agent routes
- `GET /exists?course=&session=` → `{exists, run_id?, finished_at?, zips}` — has this session already been generated (Feature 6)? `exists` = a portal zip on disk **or** a prior **done** run; `run_id` is that done run (so the UI can open it). Powers the pre-generate "already present" warning.
- `POST /improve/<run_id>` `{question, feedback, gate}` → **preview** an LLM rewrite of one question from reviewer feedback (Feature 6). Synchronous + read-only on the run (safe while parked at a gate); returns `{improved}` (or `422` if the rewrite didn't validate). For the `rubric`/`variants` gates it also **re-scores** the rewrite through the gate's own path (critic + the variant type-format dimension) and returns `{improved, score}`, so the card refreshes its band immediately (a fixed code True/False flips red→green). **No memory write** — the feedback is distilled only on the subsequent `/resume`.
- `GET /download/<run_id>?set=set_01` → download the run's portal zip for a set (Feature 6); path resolved from the run's recorded `exported` artifacts (no path traversal); `404` if absent.
- `POST /recover/<run_id>` → re-drive a stalled run from its last checkpoint (idempotent; no-op if live or terminal).
- `POST /dismiss/<run_id>` → mark a stale run terminal (`dismissed`).
- `POST /pause/<run_id>` → signal a **live** run to stop at the next node boundary → `status=paused`, resumable via `/recover` (Feature 10). No-op `{stopping:false, live:false}` if the run is already parked/terminal (nothing to signal).
- `POST /cancel/<run_id>` → stop + abandon (Feature 10): a **live** run is signalled to stop then marked `dismissed`; a parked run is marked `dismissed` directly. Unlike `/dismiss`, it accepts a live run (it carries an explicit stop intent).
- `GET /cost` → `{usage, limit, limit_remaining, …, usd_to_inr}` (OpenRouter `/auth/key`, server-side key only) — the balance badge.
- `GET /runs` → list past runs (newest first), each with `status` + `live` (so the UI labels stalled vs truly-live).
- `GET /run/<run_id>` → the run's result/current state (incl. `cost_usd`, `cost_inr`, `cost_estimate*`, `usd_to_inr`, the set questions/variants/scores/summary, `exported`) + the interrupt payload (cards) if parked at a gate.

## A.2 Content & Rubric

| Method & path | Params | Response |
|---|---|---|
| `GET /api/content/courses` | — | `[course, …]` |
| `GET /api/content/sessions` | `?course=` | `[{session, session_title, module, …}]` — the picker |
| `GET /api/content/session` | `?course=&session=` | `{source (full MD), session_title, outcomes, …}` |
| `POST /api/content/upload` | multipart/JSON: `course`, `session`, file or pasted Markdown `[, title]` | `{chunks, …}` (chunk + `put_chunk`; embed off by default) |
| `GET /api/rubric` | — | `{category_min:{per_question:{cat:min}, per_set:{cat:min}}, checkpoints:[{id,category,scope,name,criterion,met_when,bad_example,good_example}]}` |
| `GET /api/health` | — | `{status:"ok"}` |

> There are **no** `/api/eval/*`, `/api/feedback`, `/api/memory`, `/api/agent/params`, `/run-batch`, or `/api/agent/group/*` routes — those were pre-build proposals. The rubric is read-only via `/api/rubric` (it is editable in code/seed + grows via the learning loop). The API key never reaches the browser — cost is proxied through `/api/agent/cost`.

## A.3 SSE event model
One `data:` JSON per event (`id:` = `agent_step_events.id`). Key payloads:

| `event`/node | key fields |
|---|---|
| `assemble` / `split` | `section_count`, `seam`, set topics/outcomes |
| `set_plan` | `set_label`, `outcomes` |
| `question` | `set_label`, the streamed `Question` block |
| `concept_check` / `refine` | `set_label`, `met`/`not_met`, `round` |
| `rubric_critic` | `qid`, `band`, `failed_checkpoints`, `pass` |
| `variant_bases` | the approved bases (text + options + correct) |
| `variant` / `variant_critic` | `base_question_keys`, `variant_type`, `band`, … |
| `awaiting_human` | `gate: "generation"|"rubric"|"variants"`, the cards (+ `bases`/`set_scores` for variants) |
| `export` | exported paths + the band/summary counts |
| `stopping` / `paused` / `cancelled` | reviewer stop (Feature 10): `intent`; `paused` is resumable, `cancelled` → `dismissed` |
| `complete` / `error` | terminal status |

## A.4 Sequence (one run, three gates)
```
UI ─POST /run──▶ start_run ─▶ thread/graph
UI ─SSE◀── assemble…split…question…concept_check… ── awaiting_human(generation)
UI ─POST /resume(gen decisions)──▶ … rubric_critic … ── awaiting_human(rubric)
UI ─POST /resume(rubric decisions)──▶ … variant… ── awaiting_human(variants)
UI ─POST /resume(variant decisions)──▶ … export ── complete(done)
```

## A.5 Errors
`{"error":"<message>", "code":"<code>"}` + HTTP status (400 bad body, 404 unknown run, 409 not awaiting_human on resume, 500 internal). Errors during a run surface as an `error` SSE event then `complete(error)`.

---

# Part B — Frontend (`frontend/`, React + Vite)

## B.1 Stack & layout
**React 18 + Vite + React Router**; SSE via native `EventSource`; a `fetch` wrapper (`lib/api.js`) + a `Workspace` context + the `useAgentRun` hook (no Redux). The Vite dev server (`:5173`) serves source via HMR and proxies `/api` → Flask (`:5001`). `npm run build` produces the static bundle.

```
frontend/src/
  main.jsx · App.jsx                  # Router: / · /generate · /run/:runId · /history · /rubric
  lib/        api.js                  # one method per route
              pipelineState.js        # derivePipeline(events) → phase + per-stage status for the graph
  context/    Workspace.jsx           # (course, session) selection + courses/sessions fetch + retry()
  hooks/      useAgentRun.js          # start run · stream SSE · resume; owns status + result + gate cards
  pages/      ContentLibrary · Generate · History · RubricView
  components/ PipelineGraph · PipelineStepper · GateBanner · ProgressNote
              QuestionCard · RubricCard · VariantCard · ScoringCard · RejectBox · ImproveBox
              BaseVariantGroup · SetsLayout · SetColumn · CostBadge
              Sidebar · UploadForm · Modal · Markdown · Article · Loading · Empty · ErrorState
```

## B.2 Shared infrastructure
- **`lib/api.js`** — `run`, `stream`(EventSource), `resume`, `recover`, `dismiss`, `pause`, `cancel` (Feature 10), `cost`, `runs`, `result`/`run`, `improveQuestion`, `downloadUrl`, `checkExists`, `courses`, `sessions`, `session`, `upload`, `rubric`. Errors surface `{error, code}` + status → `ErrorState`/inline.
- **`lib/pipelineState.js`** — `derivePipeline(events)` reduces the SSE event stream into the pipeline phase (`generation`|`rubric`|`variants`|`done`) + per-stage status (`pending`|`active`|`skip`|`done`) + a plain-language "now" line; consumed by `PipelineGraph`/`PipelineStepper`.
- **`hooks/useAgentRun.js`** — opens the SSE stream and reduces events into render-ready state: `{ status (running|awaiting_human|done|error), questions/variants by set, scores, gate cards + the gate discriminator, result, resume(decisions) }`. Owns `result` (mount snapshot + on `complete`), clears `awaitingHuman` on export/complete/error, and exposes `atGate`. Handles the `variant_bases`/`variant`/`variant_critic` + `awaiting_human` gate events. **Also exposes `pause()`/`cancel()` and handles the `stopping`/`paused`/`cancelled` events → `status=paused|dismissed` (Feature 10).**
- **`context/Workspace.jsx`** — global `(course, session)`; loads courses/sessions, clears error on success, exposes `retry()` (so a Neon blip doesn't strand the picker).

## B.3 Screens
- **Content Library** (`/`) — courses + sessions (chunk counts); `UploadForm` to add a `.md` or pasted Markdown.
- **Module Quiz** (Feature 9) — a third workflow option in Generate. Choosing it swaps the single-session start for a **multi-session checklist** (the course's sessions, each with its `module` chip) + a **name field prefilled from the ticked session titles** (editable). The run renders as one flat "Module questions" column at every gate (generation, rubric, **and variants** — the variants gate can't use the set_a/set_b `SetsLayout`), then exports a single `module_quiz/` quiz + zip.
- **Generate / Run** (`/generate`, `/run/:runId`) — pick course + session → Generate (Feature 6: if the session was **already generated**, a `Modal` warns first — **Update — regenerate** / **Open existing run** / Cancel, via `checkExists`) → navigate to the live run. The run view: `PipelineGraph` (open by default, re-fits when shown — Feature 6) + `PipelineStepper`; questions stream into `SetsLayout` (Set 1 left / Set 2 right; a **single-set** run renders one full-width column + a "small session" note) via `SetColumn`/`BaseVariantGroup`; at each gate **exactly one** `GateBanner` ("✋ Action needed") with the right cards (`QuestionCard` for Gate 1, `RubricCard` for Gate 2, `VariantCard` grouped under bases for Gate 3) — each with band/failed-checkpoint chips, briefing, the shared **`RejectBox`** (Confirm **disabled until a reason is given**), and the shared **`ImproveBox`** (Feature 6 — Improve replaces Edit: type feedback → preview the LLM rewrite Original vs Improved, with the re-scored band on the Improved side → **Accept ✓** / Try again / Discard). An accepted improve marks the card **"✓ accepted · improved"** and offers **Improve again** (which chains from the already-improved version, not the original). Progress uses the muted `ProgressNote`. The done summary shows `💰 This run cost ₹X (≈$Y, exact)` + the exported set paths + a **⬇ Download zip** link per set (`api.downloadUrl`), plus a collapsible **"What was exported"** list of the shipped questions (approved bases + approved variants, each tagged ✓ accepted / ✎ improved — rejected ones absent by construction). The sidebar shows the `CostBadge` (`💳 ₹… left`). **While the run is doing automated work (`running` + `live`, not at a gate) a control row offers ⏸ Pause and ✕ Cancel run (Feature 10); a paused run shows ▸ Resume run (→ `/recover`) + Discard — mirroring the stalled-run resume affordance.**
- **History** (`/history`) — past runs with status chips; stalled rows show `Resume`/`Dismiss` + "paused — costs nothing"; live rows show a spinner. A **`paused`** run (Feature 10 — reviewer-stopped) reuses the same ⏸ chip + `Resume`/`Dismiss` as stalled.
- **Rubric** (`/rubric`) — the rubric checkpoints + per-category mins from `/api/rubric` (searchable).

## B.4 Conventions
- **Every data view handles loading / empty / error** via the shared components.
- **Status colors:** running blue · awaiting_human amber · done green · error red · paused/stalled grey (Feature 10).
- **No business logic in the UI** — bands, counts, routing, and cost come from the backend; the UI renders state and posts decisions.
- **One action at a time** — a single `GateBanner` is visible only when `awaitingHuman && gate===X`; it is never confusable with a progress note.

---

## Definition of Done
- [ ] Every Part-A route is implemented with the documented shape; **no** `/api/eval/*`, `/run-batch`, `/params`, or `/feedback` routes; cost is proxied (key never in the browser).
- [ ] SSE emits the §A.3 events + replays durable history; resume on a non-`awaiting_human` run returns 409.
- [ ] Shared infra (`api.js`, `useAgentRun`, `Workspace`) exists and is reused; the run is never blank.
- [ ] The 3 gates each show one clear `GateBanner` with the right cards + mandatory `RejectBox`; Set 1/Set 2 are segregated; variants group under their base; the done summary shows ₹ cost + exported paths.
