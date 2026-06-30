"""AgentPipeline — coordinates four specialized agents in sequence.

Flow:
  UnderstandingAgent → RetrievalAgent → ValidationAgent → EvaluationAgent
                                                               ↓
                                               quality_gate (up to 2 revisions)
                                                               ↓
                                                       PipelineResult
"""

from __future__ import annotations
import uuid
from typing import Callable

from src.agent import AgentState, PipelineResult, _critique_question_set
from src.data_loader import get_data_store
from src.models import GenerationConfig, SessionContext, CurationMetadata, CuratedOutput, QualityReport
from src.config import MIN_QUESTIONS, MAX_QUESTIONS
from src.agents import UnderstandingAgent, RetrievalAgent, ValidationAgent, EvaluationAgent

MAX_REVISION_ROUNDS = 2

EmitFn = Callable[[str, str, str, str], None]   # (run_id, step_id, status, detail)


class AgentPipeline:

    def run(self, config: GenerationConfig, run_id: str, emit_fn: EmitFn) -> PipelineResult:
        state = AgentState(config=config, data_store=get_data_store())
        result = PipelineResult()
        result.run_id = run_id

        def emit(step_id: str, status: str, detail: str = ""):
            emit_fn(run_id, step_id, status, detail)

        emit("agent", "running", "Pipeline starting — 4-agent workflow...")

        try:
            # ── Stage 1: Understanding ────────────────────────────────────
            UnderstandingAgent().run(state, emit)

            # ── Stage 2: Retrieval ────────────────────────────────────────
            RetrievalAgent().run(state, emit)

            # ── Stage 3: Validation ───────────────────────────────────────
            ValidationAgent().run(state, emit)

            # ── Stage 4: Evaluation + quality gate loop ───────────────────
            eval_agent = EvaluationAgent()
            revision_round = 0

            while True:
                state.submitted = False
                eval_agent.run(state, emit)

                emit("critique", "running", "Quality gate — critiquing final set...")
                critique = _critique_question_set(state)
                critique_pass = critique.get("pass", True)
                must_fix = critique.get("must_fix", [])
                critique_summary = critique.get("summary", "")

                if critique_pass or revision_round >= MAX_REVISION_ROUNDS:
                    state.submitted = True
                    label = "Passed" if critique_pass else f"Force-passed after {revision_round} revision(s)"
                    emit("critique", "done", f"{label}: {critique_summary}")
                    break
                else:
                    revision_round += 1
                    state.revision_notes = must_fix
                    emit("critique", "retry",
                         f"Quality gate failed — {len(must_fix)} issue(s), revision {revision_round}/{MAX_REVISION_ROUNDS}")

            # ── Build result ──────────────────────────────────────────────
            result.curated_output = state.to_curated_output()
            result.quality_report = _build_quality_report(state, revision_round)
            result.quality_report.api_usage = dict(state.api_usage)
            result.context = state.session_context or _fallback_context(config, state)

            total_calls = len(state.tool_log)
            total_q = state.total_questions
            emit("complete", "done",
                 f"Done! {total_q} questions, {total_calls} total tool calls, {revision_round} revision(s)")

        except Exception as exc:
            import traceback
            traceback.print_exc()
            short = str(exc).split('\n')[0][:200]
            result.error = short
            emit("error", "error", f"Pipeline failed: {short}")

        return result


def _build_quality_report(state: AgentState, revision_round: int) -> QualityReport:
    total_q = state.total_questions
    diff = state.difficulty_counts
    sources = state.source_counts

    size_score = 1.0 if MIN_QUESTIONS <= total_q <= MAX_QUESTIONS else max(0.0, 1.0 - abs(total_q - 10) / 10)
    diversity_score = min(1.0, len(sources) / 2)
    diff_target = {"Easy": 0.3, "Medium": 0.5, "Hard": 0.2}
    diff_score = (
        1.0 - sum(abs(diff.get(k, 0) / max(total_q, 1) - v) for k, v in diff_target.items()) / 2
        if total_q > 0 else 0
    )

    # Three weighted metrics (answers are no longer generated)
    composite = round(0.40 * size_score + 0.25 * diversity_score + 0.35 * diff_score, 3)
    if total_q < MIN_QUESTIONS:
        composite = min(composite, 0.4)

    return QualityReport(
        composite_score=composite,
        metric_scores={
            "set_size": round(size_score, 2),
            "source_diversity": round(diversity_score, 2),
            "difficulty_balance": round(diff_score, 2),
        },
        pass_fail="pass" if composite >= 0.6 and total_q >= MIN_QUESTIONS else "fail",
        loops_used=revision_round,
    )


def _fallback_context(config: GenerationConfig, state: AgentState) -> SessionContext:
    return SessionContext(
        session_name=config.session_name,
        learning_outcomes=state.learning_outcomes,
        key_concepts=[], scope_in=[], scope_out=[],
        session_type="mixed", matched_kp_ids=[],
        matched_csv_topics=[], prerequisite_kp_chain=[],
        difficulty_distribution={"easy": 0.3, "medium": 0.5, "hard": 0.2},
    )
