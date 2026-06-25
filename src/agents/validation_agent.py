"""ValidationAgent — filters off-topic questions and deduplicates."""

from __future__ import annotations
from typing import TYPE_CHECKING

from src.agents.base_agent import BaseAgent
from src.tools import TOOL_DISPATCH, TOOL_SCHEMAS

if TYPE_CHECKING:
    from src.agent import AgentState


_TOOL_NAMES = {"validate_relevance", "deduplicate_questions", "remove_question"}
_SCHEMAS = [s for s in TOOL_SCHEMAS if s["function"]["name"] in _TOOL_NAMES]
_DISPATCH = {k: TOOL_DISPATCH[k] for k in _TOOL_NAMES}


class ValidationAgent(BaseAgent):
    name = "validation"
    display_name = "Validating Questions"
    max_tool_calls = 5

    def get_tool_schemas(self) -> list[dict]:
        return _SCHEMAS

    def get_tool_dispatch(self) -> dict:
        return _DISPATCH

    def get_system_prompt(self, state: AgentState) -> str:
        ctx = state.session_context
        session_label = ctx.session_name if ctx else state.config.session_name
        q_count = len(state.questions) + len(state.coding_questions)

        return f"""You are a quality filter for interview questions. Remove off-topic and duplicate questions.

## Session: {session_label}
## Current question count: {q_count}

## Workflow (in this order)
1. Call `validate_relevance` — removes questions that don't match session outcomes
2. Call `deduplicate_questions` — removes near-identical questions

Only call `remove_question` if you spot a specific question that clearly doesn't belong after those two passes.

## Rules
- Always call validate_relevance FIRST
- Always call deduplicate_questions AFTER validate_relevance
- If the set is already small (< 5 questions), do NOT remove anything extra
- Your goal is to keep the BEST questions, not the most questions"""

    def get_user_prompt(self, state: AgentState) -> str:
        q_count = len(state.questions) + len(state.coding_questions)
        return (
            f"Filter the {q_count} accumulated questions.\n"
            f"Call validate_relevance first, then deduplicate_questions."
        )

    def _should_stop_after(self, tool_name: str, tool_result: dict, state: AgentState) -> bool:
        # Stop after dedup — the evaluation agent handles everything after
        return tool_name == "deduplicate_questions"
