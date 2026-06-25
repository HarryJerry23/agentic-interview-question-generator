"""Base agent — each specialized agent runs its own LLM loop over a focused tool subset."""

from __future__ import annotations
import json
from typing import Callable, TYPE_CHECKING

from src.config import LLM_MODEL
from src.llm_client import get_client

if TYPE_CHECKING:
    from src.agent import AgentState

EmitFn = Callable[[str, str, str], None]   # (step_id, status, detail)


class BaseAgent:
    name: str = "base"
    display_name: str = "Base Agent"
    max_tool_calls: int = 10

    # ── Subclass API ─────────────────────────────────────────────────────────

    def get_tool_schemas(self) -> list[dict]:
        raise NotImplementedError

    def get_tool_dispatch(self) -> dict:
        raise NotImplementedError

    def get_system_prompt(self, state: AgentState) -> str:
        raise NotImplementedError

    def get_user_prompt(self, state: AgentState) -> str:
        raise NotImplementedError

    def _should_stop_after(self, tool_name: str, tool_result: dict, state: AgentState) -> bool:
        """Override to define early-exit after a specific tool result."""
        return False

    # ── Main Loop ─────────────────────────────────────────────────────────────

    def run(self, state: AgentState, emit: EmitFn) -> None:
        """Run this agent's LLM loop. Calls emit(step_id, status, detail) on each event."""
        from src.agent import _compact_tool_content, _msg_to_dict, _summarize_result

        emit(f"phase:{self.name}", "running", f"Starting {self.display_name}...")

        client = get_client()
        tool_schemas = self.get_tool_schemas()
        tool_dispatch = self.get_tool_dispatch()

        messages = [
            {"role": "system", "content": self.get_system_prompt(state)},
            {"role": "user", "content": self.get_user_prompt(state)},
        ]

        tool_call_count = 0
        stop_requested = False

        while tool_call_count < self.max_tool_calls and not stop_requested:
            response = client.chat.completions.create(
                model=LLM_MODEL,
                messages=messages,
                tools=tool_schemas,
                tool_choice="auto",
                temperature=0.3,
                max_tokens=4096,
            )

            msg = response.choices[0].message
            messages.append(_msg_to_dict(msg))

            if not msg.tool_calls:
                break

            for tool_call in msg.tool_calls:
                tool_call_count += 1
                name = tool_call.function.name

                try:
                    args = json.loads(tool_call.function.arguments) if tool_call.function.arguments else {}
                except json.JSONDecodeError:
                    args = {}
                    emit(name, "warning", f"Bad JSON args for {name}")

                emit(name, "running", f"{self.display_name}: calling {name}...")

                try:
                    handler = tool_dispatch.get(name)
                    tool_result = handler(state, **args) if handler else {"error": f"Unknown tool: {name}"}
                except Exception as exc:
                    tool_result = {"error": str(exc)}

                state.tool_log.append({
                    "agent": self.name,
                    "tool": name,
                    "args_keys": list(args.keys()),
                    "has_error": "error" in tool_result,
                })

                if name == "deduplicate_questions" and "removed" in tool_result:
                    state.dedup_removed += tool_result.get("removed", 0)

                summary = _summarize_result(name, tool_result)
                emit(name, "done", summary)

                result_str = json.dumps(tool_result, default=str)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": _compact_tool_content(result_str),
                })

                if self._should_stop_after(name, tool_result, state):
                    stop_requested = True
                    break

        q_count = len(state.questions) + len(state.coding_questions)
        emit(f"phase:{self.name}", "done",
             f"{self.display_name} complete — {q_count} questions, {tool_call_count} calls")
