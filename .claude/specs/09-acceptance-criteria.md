# 09 — Acceptance Criteria & Traceability (as-built)

> Every requirement → the spec section that defines it → a concrete acceptance check. ✅ = shipped (the `classroom_quiz` workflow); 🛠 = specified & planned for the current increment (Feature 10, not yet merged); 🔭 = future scope (`00 §E`), documented but not yet built.

## 1. Requirements traceability matrix

| # | Requirement | Status | Spec | Acceptance check (Given/When/Then) |
|---|---|---|---|---|
| R1 | **Classroom quiz**: split a session into Set 1 / Set 2; each approved base + its **typed variant set** | ✅ | 05, 06 | Given an ingested session, when a run completes, then `set_01/` + `set_02/` each export approved base questions, each with its variant set — 9 text types (`_v2/_tf_true/_tf_false/_sb_two/_fill/_multi/_all/_none/_match`), or for a code-related base in a coding session the 8 code types (`_co/_cotf/_cerr/_cfix/_cfun/_clogic/_ctxt/_cfib`) |
| R2 | **Three human gates** (generation, rubric, variants), mandatory reject reasons | ✅ | 05, 06, 07 | When a run reaches each gate, then it pauses `awaiting_human` with the right cards; resume applies accept/approve, improve, or (reject\|delete); reject/delete is blocked until a reason is given |
| R3 | **Ingest Markdown → session-keyed memory** | ✅ | 03 | When `cli --tree reading_materials/` runs, then `("content"/"source"/"outcomes", course, session)` are populated; `GET /api/content/sessions` lists them; selecting one loads its full source |
| R4 | Every question scored vs the **rubric** (35 checkpoints; code ones scoped to code questions) + concept coverage | ✅ | 04, 05 | Then each question gets a `CriticScore` (failures-only critic → Python category points → 🟢/🔴 + pass); concept-check ensures each outcome is covered |
| R5 | **Self-correction loops** (concept-check⟲refine ≤3; rubric/variant evaluate⟲optimize ≤2) | ✅ | 01, 05 | Given failures, then refine/optimize re-run up to the cap, re-scoring only the changed subset, before the gate |
| R6 | **Portal output** (existing MCQ-set shape) | ✅ | 02, 06 | When export runs, then per-set `classroom_quiz.{md,json}` + `reading_material.md` + the portal zip (`Default_new/…json`) are written with UUID ids, `is_correct`, `explanation_for_answer`; a re-run replaces |
| R7 | **Learning loop** → category feedback rule → checkpoint promotion | ✅ | 03, 04, 05 | When a reviewer rejects with a reason, it is distilled into a category-tagged rule in `("feedback",)` and injected next run; recurring rules (`hit_count ≥ threshold`) promote that checkpoint's `met_when`; generated questions are exported, not stored |
| R8 | **Real per-run cost in ₹/$** + balance badge | ✅ | 01, 06, 07 | On done, `get_result` returns `cost_usd`/`cost_inr` (exact OpenRouter usage diff, or token estimate when >1 driver live); the done summary + sidebar badge show ₹ |
| R9 | **Bounded parallelism** (latency) | ✅ | 01, 05 | Independent LLM calls run via `pmap` (≤ `llm_max_concurrency`); telemetry batched off the critical path; measured ~−65% wall-time |
| R10 | **Resilience + lifecycle** | ✅ | 01, 08 | Pools survive Neon idle drops (`check_connection` + `max_idle`); on restart orphaned `running` runs reconcile to `stalled` with Resume/Dismiss; recover re-drives from checkpoint |
| R11 | **Observability** (LangSmith, optional) | ✅ | 01, 08 | With `LANGSMITH_TRACING=true` + key, a run is a full trace tree; off = silent no-op |
| R12 | **Frontend for the whole flow**, never blank, live SSE | ✅ | 06, 07 | Content → Generate → live run (Set 1/Set 2, streaming) → 3 gates → done summary works in the browser; one clear action banner per gate |
| R13 | One evaluator, in memory, **no gold dataset** | ✅ | 04, 02 | The in-memory rubric (35 checkpoints) is the only evaluator; the critic returns failures-only; no few-shot/gold/eval-harness/xlsx/`eval_schema.json` exists |
| R16 | **Improve** action (Feature 6) replaces Edit at all 3 gates | ✅ | 05, 06, 07 | At any gate, Improve → reviewer feedback → `POST /improve` rewrites that question (P14, preview) → on `/resume` the rewrite is applied and the feedback is distilled into `("feedback",)`; manual Edit is gone |
| R17 | **Download** the result zip (Feature 6) | ✅ | 06, 07 | On a finished run, a ⬇ Download zip per set hits `GET /api/agent/download/<run_id>?set=`; bad set → 404 |
| R18 | **Pipeline graph** renders + single-set tidy (Feature 6) | ✅ | 06, 07 | The graph is visible and fits on screen (re-fits on show); a small/single-section session shows one set + a note, and the empty half is marked skipped |
| R19 | **"Already generated" warning** before regenerating (Feature 6) | ✅ | 07 | Clicking Generate for a session that already has exports/a done run shows a modal: Update — regenerate · Open existing run · Cancel (`GET /api/agent/exists`) |
| R20 | **Pause / Cancel a running run** (Feature 10) | 🛠 | 01, 02, 07 | While a run is automated (`running` + `live`), `POST /pause` stops it at the next node boundary → `status=paused`, no further spend; `POST /recover` resumes from the last checkpoint (no restart from `assemble`). `POST /cancel` stops + marks `dismissed` (no resume). At a gate, pause is a no-op; cancel discards directly |
| R14 | **Module Quiz** (2–3 sessions, pooled) | 🔭 | 00 §E, 05 §Future, 03 §Future | *Future:* a multi-session assembler + `source_label`; the rest of the pipeline reused |
| R15 | **MCQ Practice** (standalone, no variants) | 🔭 | 00 §E, 05 §Future | *Future:* larger target, variants phase + Gate 3 skipped |
| R16 | Cross-run batch / parallel Start; per-student pools; auth | 🔭 | 00 §E | Deferred — documented, not blocked |

## 2. End-to-end smoke scenarios (built)

1. **Rubric seed** — on first ingest/boot `seed_rubric_if_empty()` loads the checkpoints + per-category mins (`ensure_rubric_checkpoints()` backfills new ids) into `("rubric_checkpoints",)`/`("rubric_config",)`; `GET /api/rubric` returns them. No xlsx, no `eval_schema.json`.
2. **Ingest** — `cli --tree reading_materials/` ⇒ sessions populated; `GET /api/content/sessions?course=…` lists them; selecting one loads its full source.
3. **Classroom run** — pick a session → Generate ⇒ assemble → split → process_set ×2 (plan→generate→concept-check⟲refine) → **Gate 1** → rubric ⟲ optimize → **Gate 2** → variants ⟲ optimize → **Gate 3** → export; `set_01/` + `set_02/` + zips written; JSON valid. A re-run replaces the folders.
4. **Gates + learning** — at each gate the run pauses with the right cards; resume with accept/approve completes; a **reject with a reason** OR an **improve** (feedback → P14 rewrite → confirm) writes a category-tagged rule (rule count increments) and, on recurrence, promotes the checkpoint's `met_when`. ⬇ Download zip works on the done screen; a small session shows a single set.
5. **Cost** — `GET /api/agent/cost` returns the balance; on done `get_result.cost_inr` is a small ₹ amount ≈ the token estimate; a bad key degrades gracefully (badge hides).
6. **Lifecycle** — restart the API ⇒ a previously-`running` run shows as **stalled** in History with Resume/Dismiss; a live run shows ⏵ running; Resume re-drives from the checkpoint.
7. **Live UI** — starting a run streams SSE and renders questions into Set 1 / Set 2 as they arrive; each gets its band chip the moment its evaluation lands; exactly one `GateBanner` shows at each gate.
8. **Traces** — with tracing on, the run appears as a LangSmith trace tree.
9. **Pause / cancel (Feature 10)** — start a run; during generation `POST /pause` ⇒ `status` flips to `paused` within one node and the OpenRouter balance stops dropping; `POST /recover` continues from the checkpoint (already-generated questions remain — no restart from `assemble`). A second run + `POST /cancel` ⇒ `dismissed`, no resume offered. Pausing a run already parked at a gate is a no-op.

## 3. Definition of Done

- [ ] The rubric self-seeds into memory from `backend/domain/rubric_seed.py` (35 checkpoints: 30 base + 5 code-scoped, pydantic `Checkpoint`); no xlsx, no `eval_schema.json`.
- [ ] Bulk ingest loads the `reading_materials/` tree into session-keyed memory.
- [ ] A **classroom_quiz** run completes end-to-end from the browser and exports valid portal files (md+json+zip per set) matching the existing MCQ-set shape.
- [ ] Every question is scored against the rubric (failures-only critic → Python category points; pass = **every applicable checkpoint met**, strict binary) → 🟢/🔴; per-set checkpoints score the variant set.
- [ ] All three gates pause + resume; reject/delete requires a reason; a rejection distills a category-tagged rule used next run; recurring feedback promotes a checkpoint.
- [ ] Exact ₹/$ cost is captured; bounded parallelism is in place; pools survive Neon idle drops; stalled runs reconcile; LangSmith traces when enabled.
- [ ] **No gold dataset / few-shot / offline harness / xlsx eval exists** (R13).
- [ ] The frontend exercises the full path (content → generate → live → 3 gates → download) and is never blank.
- [ ] *(Feature 10 — this increment)* A running run can be **paused** (stop at the next node boundary, resumable from checkpoint via `/recover`) and **cancelled** (stop + `dismissed`); a paused run resumes without restarting from `assemble`.
- [ ] *(Future)* `module_quiz` + `mcq_practice` are specified (`00 §E`, `05 §Future`) but not yet implemented.
