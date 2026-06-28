# Feature 10 — Pause / Cancel / Resume a running run

**Status:** planned (current increment). Spec touch-points: `01 §2/§4/§5/§6`, `02 §1/§5`, `07 §A.1/§A.3/§B.2/§B.3/§B.4`, `09 R20`.

## Why
Once a run starts there is no way to stop it. The driver (`backend/agent/run.py::_drive`)
calls `graph.invoke(payload, cfg)` — one blocking call that runs every node until the next
gate. A reviewer who realises mid-run they don't want this quiz can only let it finish
(burning OpenRouter money) or kill the server. Add two reviewer controls during an active run:
**Pause** (stop now, resume later from the last checkpoint) and **Cancel** (stop + abandon).

The *resume* half already exists: `PostgresSaver` checkpoints after every super-step and
`recover_run()` already replays a stalled run from its last checkpoint. The only new primitive
is signalling a **live** driver thread to stop — which requires `graph.invoke` → `graph.stream`.

## Key constraint (surfaced in the UI)
Cancellation lands at the **next node (super-step) boundary**, not mid-LLM-call. A node already
in flight (e.g. a set's `pmap` generation) finishes before the stop is observed; LLM calls
already paid for are sunk cost. Instant mid-LLM abortion is **out of scope**.

## Backend
1. **`agent/run.py`** — add `_STOP: dict[str, str]` (run_id → `"pause"|"cancel"`) and
   `request_stop(run_id, intent)` (no-op if not `is_live`). Refactor `_drive` from
   `graph.invoke(...)` to a `for chunk in graph.stream(..., stream_mode="updates")` loop that
   breaks when `_STOP.get(run_id)` is set. After the loop: pop intent →
   `paused` (resumable) / `dismissed` (cancel) / `awaiting_human` (interrupt detected via
   `graph.get_state(cfg)` pending tasks) / finished (read final status via `graph.get_state(cfg).values`).
   Accumulate cost on every exit path; `_STOP.pop` + `_ACTIVE.discard` in `finally`. CLI `_cli()`
   keeps `invoke`. `recover_run()` is unchanged (a `paused` run falls through to
   `_drive(run_id, None)` → `graph.stream(None, …)`, continuing from the last checkpoint).
2. **`api/agent.py`** — `POST /pause/<id>` → `request_stop(id,"pause")`; `POST /cancel/<id>` →
   if live `request_stop(id,"cancel")` else `set_run_status(id,"dismissed",finished=True)`.
3. **`agent/storage.py`** — no schema change (`paused` is just a status string); ensure
   `reconcile_stalled` only touches orphaned `running` rows, not `paused`.

## Frontend
4. **`lib/api.js`** — add `pauseRun`, `cancelRun`.
5. **`hooks/useAgentRun.js`** — handle `paused`/`cancelled`/`stopping` SSE events; expose
   `pause()`/`cancel()`. Resume of a paused run reuses the existing `recover()`.
6. **`pages/Generate.jsx`** — Pause / Cancel controls when `running && live && !awaitingHuman`;
   extend the stalled-resume block to also fire for `status==="paused"` (Resume ▸ + Discard).
7. **`pages/History.jsx`** — add `paused` to the badge map + resumable predicate (Resume/Dismiss).
8. **`styles/theme.css`** — `.status-paused` pill + `.run-status-paused` badge (mirror `stalled`).

## Verification
- `POST /pause` during generation → `status=paused` within a node, balance stops dropping;
  `POST /recover` continues from checkpoint (no restart from `assemble`).
- `POST /cancel` → `dismissed`, no resume offered. Pause at a gate → no-op.
- Regression: a normal run still reaches all 3 gates + exports (invoke→stream is behaviour-preserving).

See the full implementation plan at
`/home/nxtwave/.claude/plans/observe-the-folder-structure-kind-beaver.md`.
