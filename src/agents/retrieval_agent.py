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

    def run(self, state: "AgentState", emit) -> None:
        """Run Tavily first (company questions), then the LLM loop (bank + GitHub fill remaining)."""
        from src.tools import tool_search_web_questions
        from src.agent import _summarize_result

        # Run Tavily before bank/GitHub — guaranteed company-attributed questions.
        # Running first ensures capacity is available before bank/GitHub fill up.
        outcomes = (state.session_context.learning_outcomes
                    if state.session_context else [])
        if outcomes:
            emit("search_web_questions", "running",
                 "Retrieving Questions: fetching company-attributed questions from Tavily...")
            result = tool_search_web_questions(state, outcomes)
            state.tool_log.append({"agent": "retrieval", "tool": "search_web_questions",
                                   "args_keys": ["outcomes"], "has_error": "error" in result})
            emit("search_web_questions", "done", _summarize_result("search_web_questions", result))

        # LLM loop fills remaining capacity with bank + GitHub questions
        super().run(state, emit)

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

## Retrieval Strategy (interview data first, then the web)
1. Call `search_question_bank` 3–5 times, once per query below — this is the provided interview data, always check it first
2. Call `search_web_questions` — always, to get real company-attributed questions from Glassdoor, AmbitionBox, Exponent etc.
   Pass SHORT topic keywords (2–4 words each), NOT full outcome sentences.
   Good: ["LangChain RAG", "AI agents memory", "RAG retrieval augmented generation"]
   Bad:  ["Implement LangChain RecursiveCharacterTextSplitter", "Build RAG pipelines using LangChain"]
3. Call `search_github_questions` — for additional structured technical questions from curated repos
4. Stop once you reach {max_q} questions or all queries are exhausted

## Queries to Use
{queries}

## Rules
- DO NOT generate questions — only retrieve from real sources (generation is disabled)
- Use the exact queries listed above; do not invent generic terms
- Do NOT repeat the same query twice
- {bank_hint}
- web search brings real company interview questions with attribution — always run it"""

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
