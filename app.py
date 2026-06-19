"""Flask web app — input page + review page with live progress tracking."""

import json
import uuid
import threading
from flask import Flask, render_template, request, redirect, url_for, session, flash, Response
from src.orchestrator import (
    run_pipeline,
    get_progress_queue, cleanup_progress,
)
from src.agent import PipelineResult
from src.models import GenerationConfig
from src.data_loader import get_data_store
from src import memory

app = Flask(__name__)
app.secret_key = "iqg-dev-secret-key-change-in-production"

# In-memory store for pipeline results (keyed by run_id)
_results: dict[str, PipelineResult] = {}
# Track running pipelines
_running: dict[str, threading.Thread] = {}


@app.route("/", methods=["GET"])
def index():
    data_store = get_data_store()
    sessions = data_store.get_session_names()
    return render_template("index.html", sessions=sessions)


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
    get_progress_queue(run_id)  # Create queue before thread starts

    def _run():
        result = run_pipeline(config, run_id=run_id)
        _results[run_id] = result

    thread = threading.Thread(target=_run, daemon=True)
    _running[run_id] = thread
    thread.start()

    return render_template("progress.html",
                           run_id=run_id,
                           session_name=config.session_name)


@app.route("/progress-stream/<run_id>")
def progress_stream(run_id: str):
    """Server-Sent Events endpoint for live pipeline progress."""
    q = get_progress_queue(run_id)

    def generate_events():
        while True:
            try:
                event = q.get(timeout=120)
                yield f"data: {json.dumps(event)}\n\n"
                # If pipeline is done or errored, stop streaming
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
    # Wait for thread to finish if still running
    thread = _running.get(run_id)
    if thread and thread.is_alive():
        thread.join(timeout=120)

    result = _results.get(run_id)
    if not result:
        flash("Run not found or still processing.", "error")
        return redirect(url_for("index"))

    if result.error:
        flash(f"Pipeline error: {result.error}", "error")
        return redirect(url_for("index"))

    return render_template(
        "review.html",
        result=result,
        run_id=run_id,
        context=result.context,
        output=result.curated_output,
        report=result.quality_report,
    )


@app.route("/approve/<run_id>", methods=["POST"])
def approve(run_id: str):
    result = _results.get(run_id)
    if not result:
        flash("Run not found.", "error")
        return redirect(url_for("index"))

    action = request.form.get("action", "")

    accepted_ids = []
    rejected_feedback = {}
    for key, value in request.form.items():
        if key.startswith("status_") and value == "accepted":
            q_id = key.replace("status_", "")
            accepted_ids.append(q_id)
        elif key.startswith("status_") and value == "rejected":
            q_id = key.replace("status_", "")
            fb = request.form.get(f"feedback_{q_id}", "")
            rejected_feedback[q_id] = fb

    global_feedback = request.form.get("global_feedback", "")

    if action == "approve":
        if accepted_ids:
            result.curated_output.question_details = [
                q for q in result.curated_output.question_details
                if q.question_id in accepted_ids or q.question_id not in rejected_feedback
            ]
            result.curated_output.coding_questions = [
                q for q in result.curated_output.coding_questions
                if q.id in accepted_ids or q.id not in rejected_feedback
            ]

        result.approved = True
        total_q = len(result.curated_output.question_details) + len(result.curated_output.coding_questions)
        memory.save_run(
            run_id=run_id,
            session_name=result.context.session_name,
            question_count=total_q,
            composite_score=result.quality_report.composite_score,
            loops_used=result.quality_report.loops_used,
            approved=True,
        )

        rejected_count = len(rejected_feedback)
        msg = f"Approved! {total_q} questions saved."
        if rejected_count:
            msg += f" ({rejected_count} rejected questions removed.)"
        flash(msg, "success")
        return redirect(url_for("review", run_id=run_id))

    elif action == "reject":
        # Re-generate with the same sessions instead of going to homepage
        old_config = result.curated_output  # preserve for reference
        session_names = result.context.session_name.split(" + ")
        max_q = result.quality_report.metric_scores.get("set_size", 15)

        config = GenerationConfig(
            session_names=session_names,
            max_questions=15,
        )

        # Clear cache so session understanding re-runs fresh
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
            new_result = run_pipeline(config, run_id=new_run_id)
            _results[new_run_id] = new_result

        thread = threading.Thread(target=_rerun, daemon=True)
        _running[new_run_id] = thread
        thread.start()

        flash("Rejected — re-generating with fresh questions.", "warning")
        return render_template("progress.html",
                               run_id=new_run_id,
                               session_name=config.session_name)

    return redirect(url_for("review", run_id=run_id))


if __name__ == "__main__":
    app.run(debug=True, port=5000, threaded=True)
