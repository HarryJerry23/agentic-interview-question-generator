# Feature 3 — Agentic classroom-quiz generation (as built)

Turns a stored session into **concept-checked, human-accepted MCQs**, parks them for the rubric
phase, and writes them into the repo in the parent app's structured quiz format. This is the first
agentic step; the 30-checkpoint rubric, variants, and portal zip are the next phase.

## Flow

```
assemble → split → ⟨per set: plan → generate → (concept-check ⟲ refine)⟩ → human accept → finalize
```

1. **assemble** — load the session's exact Markdown (`memory.get_source`) and cut it into ordered
   heading sections. Concatenated in order they reproduce the whole reading material.
2. **split** — one LLM call picks a single **seam index k**: Set A = sections `0..k-1`, Set B =
   `k..n-1`. Each set's text is the **verbatim concatenation** of its sections, so
   `set_a.text + set_b.text == the whole session` (no content dropped, no overlap; the LLM only
   chooses where to cut). A deterministic check enforces disjoint+complete; falls back to the midpoint
   section if the LLM seam is invalid. Course outcomes are split to the matching half.
3. **plan** (per set) — derive the set's **key learning outcomes** (count is agent-decided from the
   content; no fixed cap).
4. **generate** (per set) — **one MCQ per outcome**, grounded in that set's full text, with the top-k
   generic feedback rules injected. The model is **streamed**; each completed `-END-` block is parsed
   and emitted as a `question` event so cards reveal one-by-one in the UI.
5. **concept-check ⟲ refine** (per set, ≥2 / ≤3 rounds) — each question is judged **met** = *covers
   its planned outcome* AND *faithful to the set text*. Not-met questions are regenerated (their reason
   as the fix signal, same `QUESTION_KEY`) and re-checked. Met → eligible; still-failing after the cap
   → `needs_attention`.
6. **human accept** — the two sets are auto-shown; the reviewer **accepts / edits / deletes** each
   (LangGraph `interrupt()` → resume with decisions).
7. **finalize** — accepted (+edited) questions are **parked** in Postgres for the rubric phase, and
   their failure reasons (+ human delete/edit reasons) are **distilled** into generic feedback rules.
   The run is marked `done`. **No repo files are written here** — see "Deferred repo export" below.

Two sets per run = the session's two halves; Set A → `set_01`, Set B → `set_02` (used by the final
phase's export).

## Prompts (`backend/agent/prompts/`, numbered by pipeline order)

Six prompts; only #3 is reused from the legacy app (`gen-ai-courseware/prompts/mcq_prompt.md`). Every
`{{placeholder}}` is filled by the loading node (`llm.fill()` raises on any unbound placeholder).

| # | File | Node | In → Out |
|---|---|---|---|
| 1 | `01_split_session.md` | split | sections (idx+heading+snippet) + course_outcomes → `{seam_index, set_a/set_b: {topics[], outcomes[]}}` |
| 2 | `02_plan_outcomes.md` | plan | a set's full text + topics/outcomes → `outcomes[]` (agent-decided count) |
| 3 | `03_generate_mcq.md` (reused) | generate | `{{reading_material}}`(set text) + `{{learning_outcomes}}` + `{{question_count}}` + `{{feedback_rules}}` → MD `-END-` blocks |
| 4 | `04_concept_check.md` | concept_check | `{{set_content}}` + `{{planned_outcomes}}` + `{{questions}}` → per-qid `{met, reason}` |
| 5 | `05_refine.md` | refine | `{{not_met_questions}}`+reasons + `{{set_content}}` + `{{feedback_rules}}` → improved MD blocks (same QUESTION_KEY) |
| 6 | `06_feedback_distill.md` | finalize | `{{not_met_reasons}}` + `{{human_reasons}}` → generic one-sentence rules[] |

## Memory & storage (all scalable Postgres — no browser storage)

LangGraph `PostgresStore` namespaces (via `backend/memory.py`):
- `("content", course, session)` — embedded chunks · `("source", …)` — full original Markdown ·
  `("outcomes", …)` — session outcomes/title · `("rubric_checkpoints",)` + `("rubric_config",)` — the
  rubric (next phase).
- `("feedback",)` — **generic one-sentence rules only** (deduped on normalized text + semantic
  similarity → `hit_count` and `aliases`; never deleted). Injected into generate/refine: top-k by
  `hit_count` for generation; **semantically relevant to the failure reasons** for refine when
  `feedback_retrieval_mode` is semantic/hybrid. Never stores questions or session facts. See
  `memory-and-feedback-explained.md` §Scalability.
- `("ready_for_rubric", course, session, set_label)` — accepted questions parked for the rubric phase
  (`put_accepted`/`get_accepted`/`clear_accepted`; a re-run clears then re-parks).

Operational tables (`backend/agent/storage.py`, on `settings.agent_dsn`): `agent_runs` (run_id,
course, session, status, started_at, finished_at) + `agent_step_events` (SSE replay log). `list_runs()`
powers History. LangGraph checkpoints (resume/replay) use a **pooled** `PostgresSaver`
(`graph.py::_saver()` — a `ConnectionPool`, so Neon idle-closing a connection doesn't break
resume/history-reopen).

## Deferred repo export (`backend/agent/export.py` — NOT called in this phase)

The structured repo files are produced **only in the final phase**, once everything (including the
rubric pass) is finalized — not in this pre-rubric step. This phase writes **nothing to disk**; it
only parks accepted questions in Postgres (`ready_for_rubric`). `export.py` is built and ready:
`export_set(course, session, set_label, questions, reading_text)` writes, under
`generated_quizzes/{course}/{session}/classroom_quiz/{set_01|set_02}/`:
- `reading_material.md` — the half's source text;
- `classroom_quiz.md` — portal `-END-` blocks with `QUESTION_ID` / `OPTION_x_ID` UUIDs;
- `classroom_quiz.json` — portal JSON array (`question_id` matches the MD, `tag_names` from
  topic/sub_topic/bloom/outcome/key, `is_correct` from `correct_option`, `explanation_for_answer`).

Mirrors the parent app's `courses/.../classroom_quiz/set_NN/` layout (Set A→set_01, Set B→set_02),
shared UUIDs between `.md`/`.json`, re-run overwrites. Path = `settings.generated_quizzes_dir`
(default `<repo_root>/generated_quizzes`). The final phase will call `export_set` for each set after
the rubric step so set_01/set_02 + md + json + reading_material are all emitted together.

## API (`backend/api/agent.py`, served on :5001)

| Method & path | Purpose |
|---|---|
| `POST /api/agent/run` `{course, session}` | start a run (background thread) → `{run_id}` |
| `GET /api/agent/stream/<run_id>` | SSE — replays persisted events then streams live; emits `question`, `awaiting_human`, `export`, `finalize`, `complete` |
| `POST /api/agent/resume/<run_id>` `{decisions:[{qid, action, edited?, reason?}]}` | apply accept/edit/delete, continue to finalize |
| `GET /api/agent/run/<run_id>` | snapshot: `{status, set_plan, questions, outcome_checks, accepted[], dropped[], needs_attention[], feedback_written[]}` |
| `GET /api/agent/runs?course=&session=&limit=` | run history (newest first) |

## Frontend — one standalone app (`frontend/src/`)

A persistent **left sidebar** (`components/Sidebar.jsx`) holds the brand, **one shared course→session
picker**, Upload, and nav: **Reading material · Generate quiz · History · Rubric**. The selection lives
in the **URL query string** (`context/Workspace.jsx` via `useSearchParams`) — reload-proof and
shareable, no localStorage. Views consume `useWorkspace()` (no duplicated pickers).

- `pages/ContentLibrary.jsx` — reading material for the selected session.
- `pages/Generate.jsx` (routes `/generate` and `/run/:id`) — one integrated page: a **react-flow
  pipeline graph** (`components/PipelineGraph.jsx`, `@xyflow/react`) that decomposes each set into
  **Plan▸Generate▸Check▸Refine** nodes with an animated **Refine→Check loop-back edge** + round badge
  and live status; **Set A / Set B columns** whose cards **stream in** (checking → verdict) with a
  collapsible source panel; the human **accept panel**; and a **“Ready for the rubric phase”** summary
  showing accepted/dropped counts and learned rules (the structured files are emitted in the final phase).
- `pages/History.jsx` (`/history`) — past runs (course · session · status · time); Open → `/run/:id`
  replays the completed pipeline + result.
- `hooks/useAgentRun.js` — subscribes to the SSE stream; accumulates per-set questions and surfaces
  the gate; `lib/api.js` — `startRun/streamRun/resumeRun/getRun/listRuns` + content/rubric helpers.

LLM = `anthropic/claude-haiku-4-5` via OpenRouter (`settings.openrouter_*`). Vite proxies `/api` → :5001.

## Verification (as run)

- **CLI** `python -m backend.agent.run --course building_llm_applications --session integrating_mcp`:
  full-text split intact (`set_a.text+set_b.text == whole`), one MCQ per outcome, ≥2 concept rounds;
  **no files written** to `generated_quizzes/` (deferred to the final phase).
- **API**: run → stream → `awaiting_human` → resume → `done`; `GET /runs` lists history; reopening a
  past run works (pooled saver).
- **UI (headless-Chrome)**: sidebar shared picker drives every view; selecting updates the URL and a
  reload keeps it; the graph shows the per-set **Check ⟲ Refine loop** (round-count badges like
  “×3 rounds”, a dashed “↺ retry” arc, and a “none needed” Refine when a set passes) and lights up
  live; cards stream in then settle to verdicts; History lists + reopens runs.

## Out of scope (next phase)

30-checkpoint **rubric critic**, **variants** (`classroom_quiz_prompt.md`), category-grouped
feedback→checkpoint promotion, and the portal **zip** bundle. Ingestion, content/rubric API, and
`domain/{scoring,rubric_seed}.py` are unchanged.
