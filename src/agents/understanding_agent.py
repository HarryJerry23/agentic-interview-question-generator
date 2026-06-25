"""UnderstandingAgent — maps session material to KPs, outcomes, and search queries."""

from __future__ import annotations
from typing import TYPE_CHECKING

from src.agents.base_agent import BaseAgent
from src.tools import TOOL_DISPATCH, TOOL_SCHEMAS

if TYPE_CHECKING:
    from src.agent import AgentState


_TOOL_NAMES = {"understand_session"}
_SCHEMAS = [s for s in TOOL_SCHEMAS if s["function"]["name"] in _TOOL_NAMES]
_DISPATCH = {k: TOOL_DISPATCH[k] for k in _TOOL_NAMES}


class UnderstandingAgent(BaseAgent):
    name = "understanding"
    display_name = "Understanding Session"
    max_tool_calls = 3

    def get_tool_schemas(self) -> list[dict]:
        return _SCHEMAS

    def get_tool_dispatch(self) -> dict:
        return _DISPATCH

    def get_system_prompt(self, state: AgentState) -> str:
        return f"""You are a session analyst for an interview question curation system.

## Your Job
Call `understand_session` ONCE to extract:
- Learning outcomes (what students must know after this session)
- Knowledge Points (KPs) from the curriculum knowledge graph
- Session type (theory_heavy / code_heavy / mixed)
- Suggested search queries for the retrieval stage

## Rules
- Call `understand_session` exactly once — no other tools are available
- After the call returns, summarize the key findings in a brief sentence

Session: {state.config.session_name}"""

    def get_user_prompt(self, state: AgentState) -> str:
        names = ", ".join(f'"{s}"' for s in state.config.session_names)
        return f"Analyze: {names}. Call understand_session now."

    def _should_stop_after(self, tool_name: str, tool_result: dict, state: AgentState) -> bool:
        # Store suggested queries on state so RetrievalAgent can access them
        if tool_name == "understand_session":
            state.suggested_queries = tool_result.get("suggested_search_queries", [])
        return tool_name == "understand_session"
