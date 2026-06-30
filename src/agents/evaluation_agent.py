"""EvaluationAgent — balances difficulty, checks coverage, submits."""

from __future__ import annotations
from typing import TYPE_CHECKING

from src.agents.base_agent import BaseAgent
from src.tools import TOOL_DISPATCH, TOOL_SCHEMAS

if TYPE_CHECKING:
    from src.agent import AgentState


_TOOL_NAMES = {
    "check_difficulty_balance",
    "check_outcome_coverage",
    "generate_coding_questions",
    "remove_question",
    "submit_question_set",
}
_SCHEMAS = [s for s in TOOL_SCHEMAS if s["function"]["name"] in _TOOL_NAMES]
_DISPATCH = {k: TOOL_DISPATCH[k] for k in _TOOL_NAMES}


class EvaluationAgent(BaseAgent):
    name = "evaluation"
    display_name = "Evaluating & Finalizing"
    max_tool_calls = 12  # extra budget for revision rounds

    def get_tool_schemas(self) -> list[dict]:
        return _SCHEMAS

    def get_tool_dispatch(self) -> dict:
        return _DISPATCH

    def get_system_prompt(self, state: AgentState) -> str:
        ctx = state.session_context
        session_label = ctx.session_name if ctx else state.config.session_name
        session_type = ctx.session_type if ctx else "mixed"
        min_q = state.config.min_questions
        max_q = state.config.max_questions
        q_count = len(state.questions) + len(state.coding_questions)

        revision_section = ""
        if state.revision_notes:
            issues = "\n".join(
                f"  - {item.get('id', '?')}: {item.get('issue', '')} → {item.get('suggestion', '')}"
                for item in state.revision_notes
            )
            revision_section = f"""
## REVISION MODE — Fix These Issues First
{issues}

Use `remove_question` for flagged IDs, then re-check and submit.
"""

        coding_section = (
            "- Call `generate_coding_questions` (2–3 Qs) — session is code_heavy"
            if session_type == "code_heavy"
            else "- DO NOT call `generate_coding_questions` (not a code-heavy session)"
        )

        return f"""You are the final evaluator for an interview question set.

## Session: {session_label}  |  Type: {session_type}
## Current questions: {q_count}  |  Target: {min_q}–{max_q}
{revision_section}
## Workflow (in order)
1. `check_difficulty_balance` — check Easy/Medium/Hard distribution
2. `check_outcome_coverage` — check outcome coverage
3. {coding_section}
4. `submit_question_set` — LAST step, ends this agent's run

Do NOT generate expected answers — answers are not produced.

## Rules
- Target difficulty: 30% Easy, 50% Medium, 20% Hard
- Use `remove_question` ONLY to fix clear balance issues (e.g., too many Hard)
- Always call `submit_question_set` at the end — even if the set is imperfect"""

    def get_user_prompt(self, state: AgentState) -> str:
        q_count = len(state.questions) + len(state.coding_questions)
        ctx = state.session_context
        session_type = ctx.session_type if ctx else "mixed"

        if state.revision_notes:
            return (
                f"REVISION: fix {len(state.revision_notes)} flagged issue(s), then submit.\n"
                f"Current count: {q_count}"
            )
        return (
            f"Evaluate and finalize {q_count} questions for {state.config.session_name}.\n"
            f"Session type: {session_type}. Run checks, then submit."
        )

    def _should_stop_after(self, tool_name: str, tool_result: dict, state: AgentState) -> bool:
        return tool_name == "submit_question_set" and not tool_result.get("error")
