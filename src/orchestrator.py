"""Orchestrator — thin shim: manages progress queues and delegates to AgentPipeline."""

import uuid
import queue
from src.agent import PipelineResult
from src.pipeline import AgentPipeline


# Progress event queues keyed by run_id
_progress_queues: dict[str, queue.Queue] = {}


def _emit(run_id: str, step_id: str, status: str, detail: str = ""):
    q = _progress_queues.get(run_id)
    if q:
        q.put({"step": step_id, "status": status, "detail": detail})


def get_progress_queue(run_id: str) -> queue.Queue:
    if run_id not in _progress_queues:
        _progress_queues[run_id] = queue.Queue()
    return _progress_queues[run_id]


def cleanup_progress(run_id: str):
    _progress_queues.pop(run_id, None)


def run_pipeline(config, run_id: str | None = None) -> PipelineResult:
    """Run the 4-agent interview question generation pipeline."""
    actual_run_id = run_id or str(uuid.uuid4())
    get_progress_queue(actual_run_id)
    return AgentPipeline().run(config, actual_run_id, _emit)
