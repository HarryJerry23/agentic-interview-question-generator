"""Drive the generation graph — shared by the API and the CLI.

`start_run` kicks a graph run in a background thread (runs until the human-gate interrupt, then
parks). `resume_run` applies the reviewer's decisions and runs to completion. Both stream progress
through the event bus. The CLI (`python -m backend.agent.run`) runs headless and auto-accepts.
"""
from __future__ import annotations

import argparse
import threading
import uuid
from typing import Any, Dict, List, Optional

from langgraph.types import Command

from backend.agent.events import emit, get_bus
from backend.agent.graph import build_graph
from backend.agent.storage import ensure_schema, record_run, set_run_status


# Run-ids with a live driver thread attached. A run NOT in this set whose status is still
# "running" is stalled (its driver died, e.g. a server restart) and can be recovered from the
# LangGraph checkpointer via `recover_run`. Single-process Flask → a module set is sufficient.
_ACTIVE: set[str] = set()

# Reviewer-requested stops (Feature 10). run_id → "pause" | "cancel". `_drive` checks this after each
# super-step and breaks at the node boundary; the last checkpoint is already committed, so a "pause"
# is resumable via `recover_run` and a "cancel" is abandoned (`dismissed`).
_STOP: dict[str, str] = {}


def is_live(run_id: str) -> bool:
    """True iff a driver thread is currently attached to this run."""
    return run_id in _ACTIVE


def request_stop(run_id: str, intent: str) -> Dict[str, Any]:
    """Ask a **live** run to stop at the next node boundary (Feature 10). No-op if it isn't live
    (already parked at a gate, stalled, or terminal → nothing to signal)."""
    if not is_live(run_id):
        return {"stopping": False, "live": False}
    _STOP[run_id] = intent
    emit(run_id, "stopping", {"intent": intent})
    return {"stopping": True, "intent": intent, "live": True}


def _close_bus(run_id: str) -> None:
    bus = get_bus(run_id, create=False)
    if bus:
        bus.close()


def _is_interrupted(snap: Any) -> bool:
    """True if the run is parked at a human-gate interrupt (a pending task carries interrupts)."""
    for task in getattr(snap, "tasks", None) or []:
        if getattr(task, "interrupts", None):
            return True
    return False


def _config(run_id: str) -> Dict[str, Any]:
    return {"configurable": {"thread_id": run_id}}


def _drive(run_id: str, payload: Any) -> None:
    """Run the graph (fresh input, a resume Command, or None to continue from the last checkpoint)
    until it pauses, finishes, or a reviewer stop is observed. Liveness is marked by the caller
    (start/resume/recover) BEFORE the thread starts, so `is_live` is accurate the instant a run is
    kicked off (no recover race).

    Driven via `graph.stream(...)` (not `invoke`) so the loop can check `_STOP` between super-steps
    and break at a node boundary (Feature 10). Each streamed chunk is a committed super-step, so a
    break never leaves a half-written checkpoint — a paused run resumes cleanly from the last one.
    """
    graph = build_graph()
    cfg = _config(run_id)
    before = _cost_before()   # OpenRouter cumulative usage snapshot (Feature 5.2)
    try:
        for _ in graph.stream(payload, cfg, stream_mode="updates"):
            if _STOP.get(run_id):        # reviewer pause/cancel → stop at this node boundary
                break
        _accumulate_cost(run_id, before)   # add this segment's exact $ to the run total
        intent = _STOP.pop(run_id, None)
        if intent == "pause":              # resumable: keep the checkpoint, drop the live thread
            set_run_status(run_id, "paused")
            emit(run_id, "paused", {})
            _close_bus(run_id)
        elif intent == "cancel":           # abandon the run
            set_run_status(run_id, "dismissed", finished=True)
            emit(run_id, "cancelled", {})
            _close_bus(run_id)
        else:
            snap = graph.get_state(cfg)    # read the committed checkpoint once
            if _is_interrupted(snap):
                set_run_status(run_id, "awaiting_human")      # parked at a gate; bus stays open
            else:
                status = (snap.values or {}).get("status", "done")
                set_run_status(run_id, status, finished=True)
                # Emit AFTER the final checkpoint is committed, so a client that fetches the result
                # on this event sees the persisted accepted/dropped/feedback.
                emit(run_id, "complete", {"status": status})
                _close_bus(run_id)
    except Exception as exc:  # noqa: BLE001 — surface any failure to the stream + DB
        _accumulate_cost(run_id, before)
        emit(run_id, "error", {"message": str(exc)}, level="error")
        set_run_status(run_id, "error", finished=True)
        _close_bus(run_id)
    finally:
        _STOP.pop(run_id, None)
        _ACTIVE.discard(run_id)


def _cost_before() -> Optional[float]:
    try:
        from backend.agent.cost import snapshot
        return snapshot()
    except Exception:
        return None


def _accumulate_cost(run_id: str, before: Optional[float]) -> None:
    """Add (usage_after − before) to the run's accumulated cost. Flags it inexact if other runs were
    live at the same time (they share the key, so the diff would double-count)."""
    try:
        from backend.agent.cost import run_cost, snapshot
        from backend.memory import app_store, get_run_cost, put_run_cost
        seg = run_cost(before, snapshot())
        if seg is None:
            return
        store = app_store()
        cur = get_run_cost(store, run_id) or {"usd": 0.0, "exact": True}
        cur["usd"] = round(float(cur.get("usd", 0.0)) + seg, 6)
        if len(_ACTIVE) > 1:
            cur["exact"] = False   # concurrent runs share the key → diff is an over-count
        put_run_cost(store, run_id, cur)
    except Exception:
        pass


def start_run(course: str, session: str, workflow: str = "classroom_quiz",
              sessions: List[str] | None = None, module_name: str = "",
              topic_name: str = "") -> str:
    ensure_schema()
    run_id = uuid.uuid4().hex
    record_run(run_id, course, session, "running", workflow)
    get_bus(run_id)  # create the bus before the thread emits
    payload = {"run_id": run_id, "course": course, "session": session,
               "workflow": workflow, "status": "running"}
    if workflow == "module_quiz":
        # `session` is the slugified module identity; `sessions` are the ids to merge (Feature 9).
        payload["sessions"] = list(sessions or [])
        payload["module_name"] = module_name
    elif workflow == "mock_interview":
        # `session` is the slugified topic identity; `sessions` are the ids to merge (Feature 11).
        payload["sessions"] = list(sessions or [])
        payload["topic_name"] = topic_name
    _ACTIVE.add(run_id)  # mark live synchronously → no recover race
    threading.Thread(target=_drive, args=(run_id, payload), daemon=True).start()
    return run_id


def resume_run(run_id: str, decisions: List[Dict[str, Any]]) -> None:
    set_run_status(run_id, "running")
    _ACTIVE.add(run_id)
    threading.Thread(target=_drive, args=(run_id, Command(resume=decisions)), daemon=True).start()


def recover_run(run_id: str) -> Dict[str, Any]:
    """Re-drive a stalled **or reviewer-paused** run from its last LangGraph checkpoint (Feature 10).

    Safe + idempotent: if a driver is already attached, this is a no-op. Otherwise we re-open the
    event bus and drive the graph with `None`, which replays from the last committed super-step —
    a thread still parked at an interrupt re-emits its gate; a thread that died mid-run (or was
    paused) continues. A `paused` run is non-terminal + non-`awaiting_human`, so it falls through
    the guards below and resumes here.
    """
    if is_live(run_id):
        return {"recovered": False, "live": True}
    status = get_result(run_id).get("status")
    # Don't re-drive a finished run — its checkpoint is terminal; recovery is only for stalled ones.
    if status in ("done", "error"):
        return {"recovered": False, "live": False}
    # A run parked at a human gate is NOT stalled — it is waiting for the reviewer's decisions. Re-driving
    # it (graph.invoke(None)) would re-run the gate node and race the eventual resume, breaking the
    # review→export flow. It resumes only via resume_run(Command(resume=decisions)). Leave it parked.
    if status == "awaiting_human":
        return {"recovered": False, "live": False, "awaiting_human": True}
    ensure_schema()
    get_bus(run_id)  # (re)create the bus before the thread emits
    set_run_status(run_id, "running")
    _ACTIVE.add(run_id)
    threading.Thread(target=_drive, args=(run_id, None), daemon=True).start()
    return {"recovered": True, "live": True}


def get_result(run_id: str) -> Dict[str, Any]:
    """Final/awaiting snapshot of a run, read from the checkpointer."""
    graph = build_graph()
    snap = graph.get_state(_config(run_id))
    v = snap.values or {}
    def _dump(items):
        return [q.model_dump() if hasattr(q, "model_dump") else q for q in items]

    # A snapshot parked at a gate still carries the last node's status ("running"); surface the real
    # "awaiting_human" so a reload/REST poll renders the gate (not a stuck "running"). Feature 11.
    status = "awaiting_human" if _is_interrupted(snap) else v.get("status", "unknown")

    return {
        "run_id": run_id,
        "status": status,
        "live": is_live(run_id),     # a driver is attached → not stalled (Feature 4.1)
        # The authoritative workflow for the UI's snapshot read (else module/practice runs mis-render
        # as classroom on reload until SSE replay arrives). Feature 8/9.
        "workflow": v.get("workflow", "classroom_quiz"),
        "session_title": v.get("session_title", ""),
        "set_plan": v.get("set_plan", {}),
        "questions": _dump(v.get("questions", [])),
        "outcome_checks": v.get("outcome_checks", {}),
        "accepted": v.get("accepted", []),
        "dropped": v.get("dropped", []),
        "needs_attention": v.get("needs_attention", []),
        "feedback_written": v.get("feedback_written", []),
        # Rubric phase (Feature 4)
        "rubric_questions": _dump(v.get("rubric_questions", [])),
        "critic_scores": v.get("critic_scores", {}),
        "rubric_approved": v.get("rubric_approved", []),
        "rubric_rejected": v.get("rubric_rejected", []),
        "rubric_summary": v.get("rubric_summary", {}),
        "promoted_checkpoints": v.get("promoted_checkpoints", []),
        # Variants phase (Feature 5)
        "variants": _dump(v.get("variants", [])),
        "variant_scores": v.get("variant_scores", {}),
        "set_variant_scores": v.get("set_variant_scores", {}),
        "variants_approved": v.get("variants_approved", []),
        "variants_rejected": v.get("variants_rejected", []),
        "variant_summary": v.get("variant_summary", {}),
        # MCQ Practice phase (Feature 8)
        "practice_summary": v.get("practice_summary", {}),
        # Mock Interview phase (Feature 11) — so a reload/REST poll can render the table + review queue.
        "topic_name": v.get("topic_name", ""),
        "interview_outcomes": v.get("interview_outcomes", []),
        "interview_candidates": v.get("interview_candidates", []),
        "interview_rows": v.get("interview_rows", []),
        "interview_queued": v.get("interview_queued", []),
        "interview_decisions": v.get("interview_decisions", {}),
        "interview_iteration": v.get("interview_iteration", 0),
        "exported": v.get("exported", []),
        **_cost_fields(run_id),
    }


def _cost_fields(run_id: str) -> Dict[str, Any]:
    """Exact run cost (OpenRouter usage diff) + a token-price estimate fallback, in $ and ₹ (5.2/5.4)."""
    from backend.agent.cost import usd_to_inr_rate
    rate = usd_to_inr_rate()
    out: Dict[str, Any] = {
        "cost_usd": None, "cost_exact": False, "cost_estimate": None,
        "cost_inr": None, "cost_estimate_inr": None, "usd_to_inr": rate,
    }
    try:
        from backend.agent.provenance import get_provenance
        from backend.agent.report import _cost_stats
        from backend.memory import app_store, get_run_cost
        rc = get_run_cost(app_store(), run_id)
        if rc is not None and rc.get("usd") is not None:
            out["cost_usd"] = rc.get("usd")
            out["cost_exact"] = bool(rc.get("exact", True))
            out["cost_inr"] = round(out["cost_usd"] * rate, 2)
        out["cost_estimate"] = round(_cost_stats(get_provenance(run_id))["est_cost"], 4)
        out["cost_estimate_inr"] = round(out["cost_estimate"] * rate, 2)
    except Exception:
        pass
    return out


def get_interrupt_payload(run_id: str) -> Optional[Any]:
    """If the run is parked at the human gate, return the interrupt payload (the two sets)."""
    graph = build_graph()
    snap = graph.get_state(_config(run_id))
    for task in snap.tasks or []:
        for intr in getattr(task, "interrupts", []) or []:
            return intr.value
    return None


# ── CLI (headless: run, then auto-accept eligible questions) ─────────────────────

def _cli() -> None:
    ap = argparse.ArgumentParser(description="Run the agentic MCQ generation workflow.")
    ap.add_argument("--course", required=True)
    ap.add_argument("--session", required=True)
    args = ap.parse_args()

    from backend.agent.observability import init_tracing
    from backend.memory import app_store, ensure_rubric_checkpoints
    init_tracing()
    ensure_schema()
    ensure_rubric_checkpoints(app_store())  # backfill Feature 7 code checkpoints for CLI runs
    run_id = uuid.uuid4().hex
    record_run(run_id, args.course, args.session, "running")
    graph = build_graph()
    cfg = _config(run_id)
    payload = {"run_id": run_id, "course": args.course, "session": args.session, "status": "running"}

    print(f"\n=== run {run_id} :: {args.course} / {args.session} ===")
    result = graph.invoke(payload, cfg)

    # Two gates: generation, then rubric. Auto-accept each (empty decisions → keep everything).
    while result.get("__interrupt__"):
        result = graph.invoke(Command(resume=[]), cfg)
    set_run_status(run_id, result.get("status", "done"), finished=True)  # reflect in history

    sp = result.get("set_plan", {})
    full_text = "".join(s["text"] for s in result.get("sections", []))
    a_text = sp.get("set_a", {}).get("text", "")
    b_text = sp.get("set_b", {}).get("text", "")
    print(f"\nfull-text split intact: {(a_text + b_text) == full_text}  "
          f"(set_a {len(a_text)} chars + set_b {len(b_text)} chars = {len(full_text)})")

    scores = result.get("critic_scores", {})
    rubric_qs = result.get("rubric_questions", [])
    for label in ("set_a", "set_b"):
        entry = sp.get(label, {})
        qs = [q for q in rubric_qs if getattr(q, "set_label", "") == label]
        print(f"\n--- {label.upper()} :: topics={entry.get('topics')} ---")
        print(f"outcomes ({len(entry.get('outcomes', []))}): {entry.get('outcomes')}")
        print(f"scored questions: {len(qs)} (rubric rounds={result.get('rubric_iteration', '?')})")
        for q in qs:
            sc = scores.get(q.qid, {})
            cats = " ".join(f"{c.split()[0]}:{p}/{sc.get('category_min', {}).get(c, '?')}"
                            for c, p in sc.get("category_points", {}).items())
            print(f"  [{sc.get('band', '?').upper():5}] pts={sc.get('points', '?')}/{sc.get('max_points', '?')} "
                  f"{cats}  | {q.question_text[:70]}")

    summary = result.get("rubric_summary", {})
    print(f"\nrubric summary: {summary}")
    print(f"approved base questions: {len(result.get('rubric_approved', []))}")

    # ── Variants phase (Feature 5) ──
    variants = result.get("variants", [])
    vscores = result.get("variant_scores", {})
    set_v = result.get("set_variant_scores", {})
    by_base: Dict[str, list] = {}
    for v in variants:
        by_base.setdefault(getattr(v, "base_question_keys", "?"), []).append(v)
    print(f"\n=== variants ({len(variants)} across {len(by_base)} bases, "
          f"rounds={result.get('variant_iteration', '?')}) ===")
    for base_key, vs in by_base.items():
        print(f"\n  base: {base_key}")
        for v in vs:
            sc = vscores.get(v.qid, {})
            print(f"    [{sc.get('band', '?').upper():5}] {getattr(v, 'variant_type', ''):9} "
                  f"pts={sc.get('points', '?')}/{sc.get('max_points', '?')}  | {v.question_text[:60]}")
    print(f"\nper-set variant band: { {k: s.get('band') for k, s in set_v.items()} }")
    print(f"variant summary: {result.get('variant_summary', {})}")
    print(f"promoted checkpoints: {result.get('promoted_checkpoints', [])}")
    print(f"feedback rules written: {result.get('feedback_written', [])}")
    print("\nexported:")
    for e in result.get("exported", []):
        if e.get("report"):
            print(f"  report: {e['report']}")
        else:
            print(f"  {e.get('set')}: {e.get('count')} questions → {e.get('zip')}")
    print("=== done ===\n")


if __name__ == "__main__":
    _cli()
