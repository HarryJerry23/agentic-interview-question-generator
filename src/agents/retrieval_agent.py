"""RetrievalAgent — searches question bank + GitHub + web for real interview questions."""

from __future__ import annotations
from typing import TYPE_CHECKING

from src.agents.base_agent import BaseAgent
from src.tools import TOOL_DISPATCH, TOOL_SCHEMAS

if TYPE_CHECKING:
    from src.agent import AgentState


_TOOL_NAMES = {"search_question_bank", "search_github_questions", "search_web_questions"}
_SCHEMAS = [s for s in TOOL_SCHEMAS if s["function"]["name"] in _TOOL_NAMES]
_DISPATCH = {k: TOOL_DISPATCH[k] for k in _TOOL_NAMES}


class RetrievalAgent(BaseAgent):
    name = "retrieval"
    display_name = "Retrieving Questions"
    max_tool_calls = 10

    def get_tool_schemas(self) -> list[dict]:
        return _SCHEMAS

    def get_tool_dispatch(self) -> dict:
        return _DISPATCH

    def get_system_prompt(self, state: AgentState) -> str:
        if not state.session_context:
            return "No session context available — do not call any tools."

        ctx = state.session_context
        min_q = state.config.min_questions
        max_q = state.config.max_questions

        queries = "\n".join(f"  - {q}" for q in (state.suggested_queries or [ctx.session_name]))

        bank_hint = (
            "The question bank has matches for this session — start with search_question_bank."
            if state.has_bank_questions
            else "Bank may be thin for this topic — use all three sources."
        )

        return f"""You are a question retrieval specialist. Find REAL interview questions from verified sources.

## Session: {ctx.session_name}  |  Type: {ctx.session_type}
## Target: {min_q}–{max_q} questions

## Retrieval Strategy
1. Call `search_question_bank` 3–5 times, once per query below
2. If accumulated total < {min_q} after bank searches: call `search_github_questions`
3. If still < {min_q}: call `search_web_questions`

## Queries to Use
{queries}

## Rules
- DO NOT generate questions — only retrieve from real sources
- Use the exact queries listed above; do not invent generic terms
- Stop once you reach {max_q} questions OR all three sources are exhausted
- Do NOT repeat the same query twice
- {bank_hint}"""

    def get_user_prompt(self, state: AgentState) -> str:
        if not state.session_context:
            return "No session context — skip all searches."
        ctx = state.session_context
        queries = (state.suggested_queries or [ctx.session_name])[:3]
        q_hint = ", ".join(f'"{q}"' for q in queries)
        return (
            f"Retrieve questions for: {ctx.session_name}.\n"
            f"Queries: {q_hint}.\n"
            f"Start with search_question_bank."
        )
