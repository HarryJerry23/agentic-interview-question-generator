"""Build + compile the full workflow graph, with a long-lived Postgres checkpointer.

Topology:
  START → assemble → split → (process_set ×2 via Send) → human_gate          (generation gate)
        → collect_accepted → rubric_score → rubric_gate                       (rubric gate)
        → finalize → variants_generate → variants_score → variants_gate       (variants gate)
        → export_finalize → END

Three human gates per run (generation, rubric, variants), each a separate interrupt/resume cycle on
the same thread_id = run_id. The checkpointer persists state across all three. The saver is opened
once and kept alive (its context-manager retained) so the pool isn't GC-closed — like
`memory.app_store()`.
"""
from __future__ import annotations

from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph import END, START, StateGraph

from backend.agent.module import generate_module
from backend.agent.mock_interview import export_md, extract_outcomes, harvest, interview_gate, verify
from backend.agent.nodes import (
    assemble, collect_accepted, human_gate, process_set, split, split_fanout,
)
from backend.agent.practice import generate_practice_pool, practice_export, practice_gate
from backend.agent.rubric import finalize, rubric_gate, rubric_score
from backend.agent.variants import export_finalize, variants_gate, variants_generate, variants_score
from backend.domain.state import QuizState
from backend.memory import make_neon_pool
from backend.settings import settings

_SAVER: PostgresSaver | None = None
_GRAPH = None


def _saver() -> PostgresSaver:
    """A pooled checkpointer. A single connection (from_conn_string) gets closed by Neon when idle,
    which 500s any later resume/history-reopen; a ConnectionPool reconnects transparently — same
    reasoning as the pooled `memory.app_store()`. PostgresSaver needs autocommit + dict_row +
    prepare_threshold=0 on its connections."""
    global _SAVER
    if _SAVER is None:
        pool = make_neon_pool(settings.checkpoint_dsn)
        _SAVER = PostgresSaver(pool)
        _SAVER.setup()  # idempotent: creates checkpoint tables
    return _SAVER


def _route_after_assemble(state) -> str:
    """Fork by product workflow: mcq_practice → single pool; module_quiz → merged body (no split,
    keeps variants); else classroom split (Feature 8/9)."""
    wf = state.get("workflow")
    if wf == "mcq_practice":
        return "generate_practice_pool"
    if wf == "module_quiz":
        return "generate_module"
    if wf == "mock_interview":
        return "extract_outcomes"
    return "split"


def _route_after_finalize(state) -> str:
    """After the rubric gate: practice exports the pool (no variants); classroom builds variants."""
    return "practice_export" if state.get("workflow") == "mcq_practice" else "variants_generate"


def build_graph():
    """Compile once and cache. Returns a graph ready for .invoke(..., config={thread_id})."""
    global _GRAPH
    if _GRAPH is not None:
        return _GRAPH

    g = StateGraph(QuizState)
    g.add_node("assemble", assemble)
    g.add_node("split", split)
    g.add_node("process_set", process_set)
    g.add_node("human_gate", human_gate)
    g.add_node("generate_practice_pool", generate_practice_pool)   # Feature 8 (practice branch)
    g.add_node("practice_gate", practice_gate)
    g.add_node("generate_module", generate_module)                 # Feature 9 (module branch)
    g.add_node("collect_accepted", collect_accepted)
    g.add_node("rubric_score", rubric_score)
    g.add_node("rubric_gate", rubric_gate)
    g.add_node("finalize", finalize)
    g.add_node("variants_generate", variants_generate)
    g.add_node("variants_score", variants_score)
    g.add_node("variants_gate", variants_gate)
    g.add_node("export_finalize", export_finalize)
    g.add_node("practice_export", practice_export)                 # Feature 8 (practice branch)
    # Feature 11 (mock_interview branch) — harvest+verify REAL interview questions, never generated.
    g.add_node("extract_outcomes", extract_outcomes)
    g.add_node("harvest", harvest)
    g.add_node("verify", verify)
    g.add_node("interview_gate", interview_gate)   # Part 3 — exception-only human review queue
    g.add_node("export_md", export_md)

    g.add_edge(START, "assemble")
    # Fork on the product workflow: classroom splits into Set 1/Set 2; practice keeps one pool;
    # module_quiz merges sessions for variants; mock_interview merges sessions then harvests questions.
    g.add_conditional_edges("assemble", _route_after_assemble,
                            ["split", "generate_practice_pool", "generate_module", "extract_outcomes"])

    # ── Classroom branch ──
    g.add_conditional_edges("split", split_fanout, ["process_set"])
    g.add_edge("process_set", "human_gate")   # barrier: runs once after both sets finish
    g.add_edge("human_gate", "collect_accepted")   # generation gate resumes here

    # ── Practice branch ──
    g.add_edge("generate_practice_pool", "practice_gate")
    g.add_edge("practice_gate", "collect_accepted")   # practice generation gate resumes here

    # ── Module branch ── merged body → same generation gate, then the shared rubric + variants tail.
    g.add_edge("generate_module", "human_gate")

    # ── Shared rubric middle ──
    g.add_edge("collect_accepted", "rubric_score")
    g.add_edge("rubric_score", "rubric_gate")
    g.add_edge("rubric_gate", "finalize")          # rubric gate resumes here
    # Fork again: classroom continues to variants; practice exports the pool and ends.
    g.add_conditional_edges("finalize", _route_after_finalize, ["variants_generate", "practice_export"])

    # ── Classroom variants tail ──
    g.add_edge("variants_generate", "variants_score")
    g.add_edge("variants_score", "variants_gate")
    g.add_edge("variants_gate", "export_finalize")  # variants gate resumes here
    g.add_edge("export_finalize", END)

    # ── Practice tail ──
    g.add_edge("practice_export", END)

    # ── Mock-interview branch (Feature 11) ── harvest+verify real questions → export the md table.
    # Part 1 is gateless (auto-publish); the exception-only human gate is added in Part 3.
    g.add_edge("extract_outcomes", "harvest")
    g.add_edge("harvest", "verify")
    g.add_edge("verify", "interview_gate")     # auto-publish corroborated; queue under-evidenced for review
    g.add_edge("interview_gate", "export_md")  # gate resumes here (or passes straight through if nothing queued)
    g.add_edge("export_md", END)

    _GRAPH = g.compile(checkpointer=_saver())
    return _GRAPH


def warm_agent() -> None:
    """Startup warm-up: enable tracing + create operational tables + compile the graph (and its
    Postgres checkpointer) once, so the first /api/agent/run isn't a cold init."""
    from backend.agent.observability import init_tracing
    from backend.agent.storage import ensure_schema, reconcile_stalled
    from backend.memory import app_store, ensure_rubric_checkpoints
    init_tracing()
    ensure_schema()
    ensure_rubric_checkpoints(app_store())  # backfill new (e.g. Feature 7 code 6.x) checkpoints
    reconcile_stalled()   # orphaned 'running' rows from a previous process → 'stalled' (Feature 5.2)
    build_graph()
