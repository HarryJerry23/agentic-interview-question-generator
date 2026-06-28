"""Agent endpoints — start a generation run, stream its progress (SSE), resume the human gate,
and read the result. Runs execute in background threads; progress flows through the event bus.
"""
from __future__ import annotations

import json
import os
import queue
import time

from flask import Blueprint, Response, jsonify, request, send_file, stream_with_context

from backend.agent.cost import key_usage, usd_to_inr_rate
from backend.agent.events import get_bus, load_history
from backend.agent.improve import improve_question
from backend.agent.run import (
    get_interrupt_payload, get_result, is_live, recover_run, request_stop, resume_run, start_run,
)
from backend.agent.storage import list_runs, set_run_status
from backend.ingestion.parse import slugify
from backend.settings import settings

agent_bp = Blueprint("agent", __name__, url_prefix="/api/agent")


def _err(message: str, code: str, status: int):
    return jsonify({"error": message, "code": code}), status


WORKFLOWS = ("classroom_quiz", "mcq_practice", "module_quiz", "mock_interview")


@agent_bp.post("/run")
def run():
    body = request.get_json(silent=True) or {}
    # slugify matches how upload stores course/session ids (parse.slugify) and strips any path-
    # traversal characters before these reach get_source / the export file paths.
    course = slugify((body.get("course") or "").strip())
    workflow = (body.get("workflow") or "classroom_quiz").strip()
    if not course:
        return _err("course is required", "missing_params", 400)
    if workflow not in WORKFLOWS:
        return _err(f"workflow must be one of {WORKFLOWS}", "invalid_workflow", 400)
    if workflow == "module_quiz":
        # Merge several selected sessions; the reviewer-typed module_name is the run/export identity.
        sessions = [slugify(s) for s in (body.get("sessions") or []) if isinstance(s, str) and s.strip()]
        module_name = (body.get("module_name") or "").strip()
        session = slugify(module_name)
        if not sessions:
            return _err("sessions are required for a module quiz", "missing_params", 400)
        if not session:
            return _err("module_name is required for a module quiz", "missing_params", 400)
        run_id = start_run(course, session, workflow, sessions=sessions, module_name=module_name)
        return jsonify({"run_id": run_id}), 201
    if workflow == "mock_interview":
        # Merge several selected sessions of a topic; the reviewer-typed topic_name is the run/export
        # identity. Questions are HARVESTED + VERIFIED from real sources, never generated (Feature 11).
        sessions = [slugify(s) for s in (body.get("sessions") or []) if isinstance(s, str) and s.strip()]
        topic_name = (body.get("topic_name") or "").strip()
        session = slugify(topic_name)
        if not sessions:
            return _err("sessions are required for a mock interview", "missing_params", 400)
        if not session:
            return _err("topic_name is required for a mock interview", "missing_params", 400)
        run_id = start_run(course, session, workflow, sessions=sessions, topic_name=topic_name)
        return jsonify({"run_id": run_id}), 201
    session = slugify((body.get("session") or "").strip())
    if not session:
        return _err("course and session are required", "missing_params", 400)
    run_id = start_run(course, session, workflow)
    return jsonify({"run_id": run_id}), 201


@agent_bp.get("/exists")
def exists():
    """Has this (course, session) already been generated? Powers the pre-generate "already present"
    warning (Feature 6). Reports any prior **done** run (so the UI can open it) + zips on disk."""
    course = slugify((request.args.get("course") or "").strip())
    session = slugify((request.args.get("session") or "").strip())
    workflow = (request.args.get("workflow") or "classroom_quiz").strip()
    if not course or not session:
        return _err("course and session are required", "missing_params", 400)
    # For module_quiz the `session` arg is the slugified module identity (same as the export folder).
    sub = workflow if workflow in ("mcq_practice", "module_quiz", "mock_interview") else "classroom_quiz"
    # course/session are slugified above (no path separators), so this join stays under quizzes_dir.
    base = os.path.join(settings.quizzes_dir, course, session, sub)
    zips = sorted(f for f in os.listdir(base) if f.endswith(".zip")) if os.path.isdir(base) else []
    rows = list_runs(limit=20, course=course, session=session)
    done = next((r for r in rows
                 if r.get("status") == "done" and r.get("workflow", "classroom_quiz") == workflow), None)
    return jsonify({
        "exists": bool(zips) or done is not None,
        "zips": zips,
        "run_id": (done or {}).get("run_id"),
        "finished_at": (done or {}).get("finished_at"),
    })


@agent_bp.get("/stream/<run_id>")
def stream(run_id: str):
    """Server-Sent Events: replay persisted history, then live events until the run closes."""
    def _gen():
        seen = 0
        bus = get_bus(run_id, create=False)
        # 1) replay everything so far (durable history covers reconnects / late subscribers)
        history = bus.history if bus else load_history(run_id)
        for ev in history:
            yield f"data: {json.dumps(ev)}\n\n"
            seen += 1
        # 2) live tail
        if bus is None:
            yield f"data: {json.dumps({'node': 'stream', 'payload': {'note': 'no live bus'}})}\n\n"
            return
        while True:
            try:
                ev = bus.q.get(timeout=15)
            except queue.Empty:
                yield ": keepalive\n\n"
                if bus.closed:
                    break
                continue
            if ev is None:  # sentinel → run finished
                break
            yield f"data: {json.dumps(ev)}\n\n"
        yield f"data: {json.dumps({'node': 'stream', 'payload': {'done': True}})}\n\n"

    headers = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no", "Connection": "keep-alive"}
    return Response(stream_with_context(_gen()), mimetype="text/event-stream", headers=headers)


@agent_bp.post("/resume/<run_id>")
def resume(run_id: str):
    body = request.get_json(silent=True) or {}
    decisions = body.get("decisions", [])
    if not isinstance(decisions, list):
        return _err("decisions must be a list", "bad_decisions", 400)
    # Every gate keys its decisions by `qid` (see the gate nodes' `{d["qid"]: d ...}`), so a decision
    # without a non-empty string qid would crash the graph at resume — reject it here instead.
    if any(not isinstance(d, dict) or not isinstance(d.get("qid"), str) or not d["qid"] for d in decisions):
        return _err("each decision must be an object with a non-empty 'qid'", "bad_decisions", 400)
    resume_run(run_id, decisions)
    return jsonify({"run_id": run_id, "resumed": True})


@agent_bp.post("/improve/<run_id>")
def improve(run_id: str):
    """Preview an LLM rewrite of ONE question from the reviewer's feedback (Feature 6).

    Synchronous + read-only on the run — safe to call while parked at a gate. No memory write happens
    here; the feedback is distilled into memory only when the reviewer accepts and submits the gate.
    """
    body = request.get_json(silent=True) or {}
    question = body.get("question")
    feedback = (body.get("feedback") or "").strip()
    if not isinstance(question, dict):
        return _err("question is required", "missing_question", 400)
    if not feedback:
        return _err("feedback is required", "missing_feedback", 400)
    # Ground the rewrite in the question's own set source (fall back to the whole session text).
    set_plan = (get_result(run_id).get("set_plan") or {})
    label = question.get("set_label") or ""
    set_text = (set_plan.get(label) or {}).get("text", "")
    if not set_text:
        set_text = "\n".join((sp or {}).get("text", "") for sp in set_plan.values())
    improved = improve_question(run_id, question, feedback, set_text)
    if improved is None:
        return _err("couldn't produce a valid improvement — try rephrasing", "improve_failed", 422)
    # Re-score the rewrite through the gate's own path so the card refreshes its band immediately
    # (e.g. a fixed code True/False flips red→green) instead of showing the stale pre-improve score.
    gate = (body.get("gate") or "").strip()
    payload = {"improved": improved.model_dump()}
    if gate in ("rubric", "variants"):
        try:
            from backend.agent.variants import score_improved
            sc = score_improved(run_id, improved, set_text, is_variant=(gate == "variants"))
            if sc:
                payload["score"] = {"band": sc.get("band"), "pass": sc.get("passed"),
                                    "points": sc.get("points"), "max_points": sc.get("max_points")}
        except Exception:
            pass   # band refresh is best-effort; the rewrite itself still returns
    return jsonify(payload)


@agent_bp.get("/download/<run_id>")
def download(run_id: str):
    """Download a finished run's portal zip for a set (Feature 6). Resolves the path from the run's
    recorded `exported` artifacts, so only a produced file can be served (no path traversal)."""
    set_name = request.args.get("set") or ""
    exported = get_result(run_id).get("exported", []) or []
    entry = next((e for e in exported if e.get("set") == set_name), None) or (exported[0] if exported else None)
    zip_path = (entry or {}).get("zip")
    if not zip_path or not os.path.exists(zip_path):
        return _err("export not found", "not_found", 404)
    return send_file(zip_path, as_attachment=True, download_name=os.path.basename(zip_path))


@agent_bp.post("/recover/<run_id>")
def recover(run_id: str):
    """Re-drive a stalled run from its last LangGraph checkpoint (Feature 4.1)."""
    return jsonify({"run_id": run_id, **recover_run(run_id)})


@agent_bp.post("/dismiss/<run_id>")
def dismiss(run_id: str):
    """Mark a stalled/abandoned run terminal so it leaves the active list (Feature 5.2)."""
    if is_live(run_id):
        return _err("run is live", "run_live", 409)
    set_run_status(run_id, "dismissed", finished=True)
    return jsonify({"run_id": run_id, "dismissed": True})


@agent_bp.post("/pause/<run_id>")
def pause(run_id: str):
    """Signal a live run to stop at the next node boundary → `paused`, resumable via /recover
    (Feature 10). No-op if the run isn't live (already parked at a gate, stalled, or terminal)."""
    return jsonify({"run_id": run_id, **request_stop(run_id, "pause")})


@agent_bp.post("/cancel/<run_id>")
def cancel(run_id: str):
    """Stop + abandon a run → `dismissed` (Feature 10). A live run is signalled to stop (the driver
    marks it dismissed at the next node boundary); a parked/stalled run is dismissed directly."""
    if is_live(run_id):
        return jsonify({"run_id": run_id, **request_stop(run_id, "cancel")})
    set_run_status(run_id, "dismissed", finished=True)
    return jsonify({"run_id": run_id, "stopping": False, "live": False, "dismissed": True})


@agent_bp.get("/cost")
def cost():
    """Live OpenRouter key balance/usage for the header badge (server-side key; Feature 5.2).
    Includes the live USD→INR rate so the UI can show ₹ (Feature 5.4)."""
    data = key_usage()
    if not data:
        return jsonify({"unavailable": True})
    return jsonify({**data, "usd_to_inr": usd_to_inr_rate()})


@agent_bp.get("/runs")
def runs():
    course = request.args.get("course") or None
    session = request.args.get("session") or None
    try:
        limit = min(int(request.args.get("limit", 50)), 200)
    except ValueError:
        limit = 50
    rows = list_runs(limit=limit, course=course, session=session)
    for r in rows:                       # mark which rows have a live driver thread (Feature 5.2)
        r["live"] = is_live(r["run_id"])
    return jsonify({"runs": rows})


@agent_bp.get("/run/<run_id>")
def result(run_id: str):
    data = get_result(run_id)
    gate = get_interrupt_payload(run_id)
    if gate is not None:
        data["gate"] = gate  # the two sets awaiting accept/edit/delete
    return jsonify(data)
