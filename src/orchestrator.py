"""Orchestrator — routes to the agentic workflow and manages progress events."""

import uuid
import queue
from src.agent import run_agent, PipelineResult


# Progress event infrastructure
_progress_queues: dict[str, queue.Queue] = {}


def _emit(run_id: str, step_id: str, status: str, detail: str = ""):
    """Emit a progress event for the given run."""
    q = _progress_queues.get(run_id)
    if q:
        q.put({"step": step_id, "status": status, "detail": detail})


def get_progress_queue(run_id: str) -> queue.Queue:
    """Get or create a progress queue for a run."""
    if run_id not in _progress_queues:
        _progress_queues[run_id] = queue.Queue()
    return _progress_queues[run_id]


def cleanup_progress(run_id: str):
    _progress_queues.pop(run_id, None)


def run_pipeline(config, run_id: str | None = None) -> PipelineResult:
    """Run the agentic interview question generation workflow."""
    actual_run_id = run_id or str(uuid.uuid4())
    get_progress_queue(actual_run_id)
    return run_agent(config, actual_run_id, _emit)
