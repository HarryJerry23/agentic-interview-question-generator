"""Flask web app — JSON API + React SPA (frontend/dist/) + legacy Jinja templates fallback."""

import json
import os
import uuid
import threading
from flask import Flask, render_template, request, redirect, url_for, session, flash, Response, send_from_directory, jsonify
from src.orchestrator import (
    run_pipeline,
    get_progress_queue, cleanup_progress,
)
from src.agent import PipelineResult
from src.models import GenerationConfig
from src.data_loader import get_data_store
from src import memory

# Serve React build from frontend/dist/ when it exists
REACT_DIST = os.path.join(os.path.dirname(__file__), "frontend", "dist")
_has_react = os.path.isdir(REACT_DIST)

app = Flask(__name__,
            static_folder=REACT_DIST if _has_react else "static",
            static_url_path="")
app.secret_key = "iqg-dev-secret-key-change-in-production"

# In-memory store for pipeline results (keyed by run_id)
_results: dict[str, PipelineResult] = {}
# Track running pipelines
_running: dict[str, threading.Thread] = {}


def _payload(result: "PipelineResult", run_id: str) -> dict:
    """Build the /api/result response shape from a PipelineResult."""
    ctx = result.context
    return {
        "run_id": run_id,
        "context": ctx.model_dump() if ctx else None,
        "output": result.curated_output.model_dump() if result.curated_output else None,
        "report": result.quality_report.model_dump() if result.quality_report else None,
    }


def _persist_result(run_id: str, result: "PipelineResult"):
    """Persist a completed run so Review + re-export survive server restarts,
    and surface it in History immediately (approved=0)."""
    try:
        if not result or result.error or not result.curated_output:
            return
        memory.save_run_result(run_id, _payload(result, run_id))
        total_q = (len(result.curated_output.question_details)
                   + len(result.curated_output.coding_questions))
        memory.save_run(
            run_id=run_id,
            session_name=result.context.session_name if result.context else "Unknown",
            question_count=total_q,
            composite_score=result.quality_report.composite_score if result.quality_report else 0,
            loops_used=result.quality_report.loops_used if result.quality_report else 0,
            approved=False,
            api_usage=dict(result.quality_report.api_usage) if result.quality_report else None,
        )
    except Exception:
        pass


def _load_result(run_id: str) -> "PipelineResult | None":
    """In-memory result, or reconstruct one from the persisted payload."""
    result = _results.get(run_id)
    if result:
        return result
    payload = memory.get_run_result(run_id)
    if not payload:
        return None
    from src.models import CuratedOutput, SessionContext, QualityReport
    r = PipelineResult()
    r.run_id = run_id
    r.context = SessionContext.model_validate(payload["context"]) if payload.get("context") else None
    r.curated_output = CuratedOutput.model_validate(payload["output"]) if payload.get("output") else None
    r.quality_report = QualityReport.model_validate(payload["report"]) if payload.get("report") else None
    return r


# ── Legacy Jinja routes (active only when React is NOT built) ─────────────────

if not _has_react:
    @app.route("/", methods=["GET"])
    def index():
        data_store = get_data_store()
        sessions = data_store.get_session_names()
        return render_template("index.html", sessions=sessions)


if not _has_react:
    @app.route("/generate", methods=["POST"])
    def generate():
        selected_sessions = request.form.getlist("session_names")
        custom_topic = request.form.get("custom_topic", "").strip()
        max_questions = int(request.form.get("max_questions", 15))
        dry_run = request.form.get("dry_run") == "on"

        session_names = [s for s in selected_sessions if s]
        if custom_topic:
            session_names.append(custom_topic)

        if not session_names:
            flash("Please select at least one session or enter a custom topic.", "error")
            return redirect(url_for("index"))

        config = GenerationConfig(
            session_names=session_names,
            max_questions=min(max_questions, 15),
            dry_run=dry_run,
        )

        run_id = str(uuid.uuid4())
        get_progress_queue(run_id)

        def _run():
            result = run_pipeline(config, run_id=run_id)
            _results[run_id] = result
            _persist_result(run_id, result)

        thread = threading.Thread(target=_run, daemon=True)
        _running[run_id] = thread
        thread.start()

        return render_template("progress.html",
                               run_id=run_id,
                               session_name=config.session_name)

    @app.route("/progress-stream/<run_id>")
    def progress_stream(run_id: str):
        """Legacy SSE for Jinja templates."""
        q = get_progress_queue(run_id)

        def generate_events():
            while True:
                try:
                    event = q.get(timeout=300)
                    yield f"data: {json.dumps(event)}\n\n"
                    if event.get("step") in ("review", "error", "complete"):
                        break
                except Exception:
                    yield f"data: {json.dumps({'step': 'timeout', 'status': 'error', 'detail': 'Timeout'})}\n\n"
                    break
            cleanup_progress(run_id)

        return Response(generate_events(), mimetype="text/event-stream",
                        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

    @app.route("/review/<run_id>", methods=["GET"])
    def review(run_id: str):
        thread = _running.get(run_id)
        if thread and thread.is_alive():
            thread.join(timeout=300)
        result = _results.get(run_id)
        if not result:
            flash("Run not found or still processing.", "error")
            return redirect(url_for("index"))
        if result.error:
            flash(f"Pipeline error: {result.error}", "error")
            return redirect(url_for("index"))
        return render_template("review.html", result=result, run_id=run_id,
                               context=result.context, output=result.curated_output,
                               report=result.quality_report)

    @app.route("/approve/<run_id>", methods=["POST"])
    def approve(run_id: str):
        result = _results.get(run_id)
        if not result:
            flash("Run not found.", "error")
            return redirect(url_for("index"))
        flash("Please use the React UI for approvals.", "info")
        return redirect(url_for("index"))


# ── JSON API ─────────────────────────────────────────────────────────────────

@app.route("/api/meta")
def api_meta():
    """Runtime info for the UI: active model, selectable models, credit balance."""
    from src.config import MODEL_OPTIONS
    from src.llm_client import get_credit_balance, get_active_model
    return jsonify({
        "model": get_active_model(),
        "models": MODEL_OPTIONS,
        "credits": get_credit_balance(),
    })


@app.route("/api/sessions")
def api_sessions():
    data_store = get_data_store()
    return jsonify({"sessions": data_store.get_session_names()})


@app.route("/api/topics")
def api_topics():
    path = os.path.join(os.path.dirname(__file__), "data", "course_structure.json")
    try:
        with open(path) as f:
            topics = json.load(f)
        return jsonify({"topics": topics})
    except FileNotFoundError:
        return jsonify({"topics": {}})


@app.route("/api/generate", methods=["POST"])
def api_generate():
    body = request.get_json(force=True) or {}
    session_names = body.get("session_names", [])
    max_questions = int(body.get("max_questions", 7))
    custom_topic = body.get("custom_topic", "").strip()
    model = (body.get("model") or "").strip() or None

    if custom_topic:
        session_names.append(custom_topic)
    if not session_names:
        return jsonify({"error": "No sessions provided"}), 400

    config = GenerationConfig(
        session_names=session_names,
        max_questions=min(max_questions, 15),
        model=model,
    )
    run_id = str(uuid.uuid4())
    get_progress_queue(run_id)

    def _run():
        from src.llm_client import set_active_model
        set_active_model(config.model)
        result = run_pipeline(config, run_id=run_id)
        _results[run_id] = result
        _persist_result(run_id, result)

    t = threading.Thread(target=_run, daemon=True)
    _running[run_id] = t
    t.start()

    return jsonify({"run_id": run_id})


@app.route("/api/stream/<run_id>")
def api_stream(run_id: str):
    q = get_progress_queue(run_id)

    def generate_events():
        while True:
            try:
                event = q.get(timeout=120)
                yield f"data: {json.dumps(event)}\n\n"
                if event.get("step") in ("complete", "error"):
                    break
            except Exception:
                yield f"data: {json.dumps({'step': 'timeout', 'status': 'error', 'detail': 'Timeout'})}\n\n"
                break
        cleanup_progress(run_id)

    return Response(generate_events(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.route("/api/result/<run_id>")
def api_result(run_id: str):
    thread = _running.get(run_id)
    if thread and thread.is_alive():
        thread.join(timeout=300)

    result = _results.get(run_id)
    if not result:
        # Fall back to the persisted run (survives server restarts / history).
        payload = memory.get_run_result(run_id)
        if payload:
            return jsonify(payload)
        return jsonify({"error": "Run not found or still processing"}), 404
    if result.error:
        return jsonify({"error": result.error}), 500

    return jsonify(_payload(result, run_id))


@app.route("/api/approve/<run_id>", methods=["POST"])
def api_approve(run_id: str):
    result = _load_result(run_id)
    if not result:
        return jsonify({"error": "Run not found"}), 404

    body = request.get_json(force=True) or {}
    action = body.get("action", "approve")
    accepted_ids = body.get("accepted_ids", [])
    rejected_feedback = body.get("rejected_feedback", {})

    if action == "approve":
        if accepted_ids:
            result.curated_output.question_details = [
                q for q in result.curated_output.question_details
                if q.question_id in accepted_ids
            ]
            result.curated_output.coding_questions = [
                q for q in result.curated_output.coding_questions
                if q.id in accepted_ids
            ]
        result.approved = True
        total_q = len(result.curated_output.question_details) + len(result.curated_output.coding_questions)
        # Save accepted questions to cross-run bank for future dedup
        try:
            session_name = result.context.session_name if result.context else "Unknown"
            accepted_set = set(accepted_ids) if accepted_ids else None
            for q in result.curated_output.question_details:
                if accepted_set is None or q.question_id in accepted_set:
                    memory.save_question_to_bank(q.question_id, session_name, q.content, q.source)
        except Exception:
            pass
        try:
            memory.save_run(
                run_id=run_id,
                session_name=result.context.session_name,
                question_count=total_q,
                composite_score=result.quality_report.composite_score if result.quality_report else 0,
                loops_used=result.quality_report.loops_used if result.quality_report else 0,
                approved=True,
                api_usage=dict(result.quality_report.api_usage) if result.quality_report else None,
            )
        except Exception:
            pass
        # Export to Google Sheets
        sheet_url = None
        sheet_error = None
        try:
            from src.sheets_writer import write_to_sheets
            session_name = result.context.session_name if result.context else "Unknown"
            sheet_url = write_to_sheets(
                output=result.curated_output,
                report=result.quality_report,
                session_name=session_name,
                run_id=run_id,
            )
        except Exception as e:
            sheet_error = str(e)
        resp = {"status": "approved", "saved": total_q}
        if sheet_url:
            resp["sheet_url"] = sheet_url
        if sheet_error:
            resp["sheet_error"] = sheet_error
        return jsonify(resp)

    elif action == "reject":
        # Distil rejection reasons into learned rules (max 5 per run)
        reasons = [v for v in rejected_feedback.values() if isinstance(v, str) and v.strip()]
        for reason in reasons[:5]:
            try:
                rule = memory.distill_rule(
                    result.context.session_name if result.context else "Unknown", reason)
                if rule:
                    memory.append_learned_rule(rule)
            except Exception:
                pass

        session_names = result.context.session_name.split(" + ")
        from src.llm_client import get_active_model
        config = GenerationConfig(session_names=session_names, max_questions=15,
                                  model=get_active_model())
        try:
            conn = memory.get_connection()
            conn.execute("DELETE FROM session_resolutions WHERE session_name = ?",
                        (result.context.session_name,))
            conn.commit()
            conn.close()
        except Exception:
            pass

        new_run_id = str(uuid.uuid4())
        get_progress_queue(new_run_id)

        def _rerun():
            from src.llm_client import set_active_model
            set_active_model(config.model)
            new_result = run_pipeline(config, run_id=new_run_id)
            _results[new_run_id] = new_result
            _persist_result(new_run_id, new_result)

        t = threading.Thread(target=_rerun, daemon=True)
        _running[new_run_id] = t
        t.start()
        return jsonify({"status": "rejected", "run_id": new_run_id})

    return jsonify({"error": "Unknown action"}), 400


@app.route("/api/history")
def api_history():
    # Start from persisted SQLite runs (survive server restarts)
    db_runs = memory.get_run_history(limit=100)
    db_ids = {r["run_id"] for r in db_runs}
    # Prepend any in-memory runs not yet approved/persisted
    for run_id, result in list(_results.items()):
        if run_id not in db_ids:
            session_name = "Unknown"
            q_count = 0
            try:
                if result.context:
                    session_name = result.context.session_name
                if result.curated_output:
                    q_count = (len(result.curated_output.question_details) +
                               len(result.curated_output.coding_questions))
            except Exception:
                pass
            db_runs.insert(0, {"run_id": run_id, "session_name": session_name,
                                "question_count": q_count, "composite_score": None,
                                "approved": 0, "created_at": None, "api_usage": {}})
    # Annotate each run with its derived course topic for display
    from src.data_loader import get_topic_for_session
    for r in db_runs:
        r["topic"] = get_topic_for_session(r.get("session_name", "") or "")
    return jsonify({"runs": db_runs})


# ── React SPA catch-all ───────────────────────────────────────────────────────
# Flask's static_url_path="" intercepts unknown paths before the /<path> route,
# so we use a 404 handler to serve the SPA for all non-API client-side routes.

if _has_react:
    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def serve_react(path):
        if path and os.path.exists(os.path.join(REACT_DIST, path)):
            return send_from_directory(REACT_DIST, path)
        return send_from_directory(REACT_DIST, "index.html")

    @app.errorhandler(404)
    def spa_fallback(e):
        if request.path.startswith("/api/"):
            return jsonify({"error": "Not found"}), 404
        return send_from_directory(REACT_DIST, "index.html")


if __name__ == "__main__":
    app.run(debug=True, port=5000, threaded=True)
