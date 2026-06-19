"""Agentic workflow — single agent with tools that autonomously curates interview questions.

The agent drives the workflow via OpenRouter tool_use. Python code only
executes tools and manages state — it doesn't make workflow decisions.
"""

from __future__ import annotations
import json
import uuid
from dataclasses import dataclass, field
from typing import Callable

from src.models import (
    GenerationConfig, SessionContext, QuestionDetail, CodingQuestion, CodeSnippet,
    CuratedOutput, CurationMetadata, QualityReport, FlaggedQuestion,
)
from src.data_loader import DataStore, get_data_store
from src.llm_client import get_client, chat_completion_json
from src.config import LLM_MODEL, MAX_TOOL_CALLS, MIN_QUESTIONS, MAX_QUESTIONS
from src.prompts import build_system_prompt, build_user_prompt
from src.tools import TOOL_SCHEMAS, TOOL_DISPATCH

MAX_REVISION_ROUNDS = 2


# ── Agent State ─────────────────────────────────────────────────────────────

@dataclass
class AgentState:
    """Mutable state accumulated across tool calls."""
    config: GenerationConfig
    data_store: DataStore
    questions: dict[str, QuestionDetail] = field(default_factory=dict)
    coding_questions: dict[str, CodingQuestion] = field(default_factory=dict)
    code_snippets: dict[str, CodeSnippet] = field(default_factory=dict)
    learning_outcomes: list[str] = field(default_factory=list)
    session_context: SessionContext | None = None
    submitted: bool = False
    dedup_removed: int = 0
    tool_log: list[dict] = field(default_factory=list)

    @property
    def total_questions(self) -> int:
        return len(self.questions) + len(self.coding_questions)

    @property
    def remaining_capacity(self) -> int:
        return self.config.max_questions - self.total_questions

    @property
    def source_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for q in self.questions.values():
            counts[q.source] = counts.get(q.source, 0) + 1
        for q in self.coding_questions.values():
            counts[q.source] = counts.get(q.source, 0) + 1
        return counts

    @property
    def difficulty_counts(self) -> dict[str, int]:
        counts = {"Easy": 0, "Medium": 0, "Hard": 0}
        for q in self.questions.values():
            d = q.difficulty or "Medium"
            counts[d] = counts.get(d, 0) + 1
        for q in self.coding_questions.values():
            d = q.difficulty or "Medium"
            counts[d] = counts.get(d, 0) + 1
        return counts

    def to_curated_output(self) -> CuratedOutput:
        return CuratedOutput(
            question_details=list(self.questions.values()),
            coding_questions=list(self.coding_questions.values()),
            code_snippets=list(self.code_snippets.values()),
            metadata=CurationMetadata(
                total_candidates=self.total_questions,
                dedup_removed=self.dedup_removed,
                source_counts=self.source_counts,
                questions_from_web=sum(1 for q in self.questions.values() if q.source == "web"),
            ),
        )


# ── Pipeline Result ─────────────────────────────────────────────────────────

class PipelineResult:
    def __init__(self):
        self.run_id: str = str(uuid.uuid4())
        self.context: SessionContext | None = None
        self.local_pool = None
        self.web_pool = None
        self.curated_output: CuratedOutput | None = None
        self.quality_report: QualityReport | None = None
        self.approved: bool = False
        self.error: str | None = None


EmitFn = Callable[[str, str, str, str], None]


# ── Critique Gate ───────────────────────────────────────────────────────────

def _critique_question_set(state: AgentState) -> dict:
    """LLM critiques the final set. Returns pass/fail + must_fix list."""
    if not state.session_context:
        return {"pass": True, "must_fix": []}

    outcomes = "\n".join(f"- {o}" for o in state.session_context.learning_outcomes)
    q_list = [{"id": q.question_id, "content": q.content[:200], "difficulty": q.difficulty}
              for q in state.questions.values()]
    cq_list = [{"id": q.id, "title": q.title, "difficulty": q.difficulty}
               for q in state.coding_questions.values()]

    result = chat_completion_json(
        system_prompt=f"""You are a strict quality gate for interview question sets.

Session: {state.session_context.session_name}
Learning Outcomes:
{outcomes}

Check ALL of these:
1. Every question directly tests one of the learning outcomes (not generic)
2. Difficulty distribution is roughly 30% Easy, 50% Medium, 20% Hard
3. No two questions are near-duplicates
4. Set has {MIN_QUESTIONS}-{MAX_QUESTIONS} questions total

Respond in JSON:
{{
    "pass": true/false,
    "must_fix": [
        {{"id": "...", "issue": "off-topic / duplicate / wrong-difficulty", "suggestion": "..."}}
    ],
    "summary": "One-line overall verdict"
}}

Be strict but fair. Only flag clear problems.""",
        user_prompt=f"Theory questions:\n{json.dumps(q_list)}\n\nCoding questions:\n{json.dumps(cq_list)}",
        max_tokens=1500,
        temperature=0.0,  # deterministic critic
    )

    return result


# ── Context Trimming ────────────────────────────────────────────────────────

def _compact_tool_content(content: str, max_len: int = 1500) -> str:
    """Trim tool result content to keep conversation context small."""
    if len(content) <= max_len:
        return content
    return content[:max_len] + '..."}'


def _trim_history(messages: list[dict], keep_system: bool = True, max_turns: int = 20):
    """Keep only recent turns to prevent context overflow. Always keep system + first user message."""
    if len(messages) <= max_turns + 2:
        return messages

    # Keep: system message + first user message + last max_turns messages
    preserved = []
    if keep_system and messages and messages[0]["role"] == "system":
        preserved.append(messages[0])
    if len(messages) > 1 and messages[1]["role"] == "user":
        preserved.append(messages[1])

    preserved.extend(messages[-(max_turns):])
    return preserved


# ── Main Agent Loop ─────────────────────────────────────────────────────────

def run_agent(
    config: GenerationConfig,
    run_id: str,
    emit_fn: EmitFn,
) -> PipelineResult:
    """Run the agentic tool-use loop. The LLM drives the workflow."""
    data_store = get_data_store()
    state = AgentState(config=config, data_store=data_store)
    result = PipelineResult()
    result.run_id = run_id

    system_prompt = build_system_prompt(
        session_name=config.session_name,
        min_q=config.min_questions,
        max_q=config.max_questions,
        curated_urls=data_store.curated_urls,
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": build_user_prompt(config.session_names)},
    ]

    client = get_client()
    tool_call_count = 0
    revision_round = 0

    emit_fn(run_id, "agent", "running", "Agent starting — planning approach...")

    try:
        while tool_call_count < MAX_TOOL_CALLS:
            # Trim history to keep context manageable
            messages = _trim_history(messages, max_turns=24)

            response = client.chat.completions.create(
                model=LLM_MODEL,
                messages=messages,
                tools=TOOL_SCHEMAS,
                tool_choice="auto",
                temperature=0.3,
                max_tokens=4096,
            )

            msg = response.choices[0].message
            messages.append(_msg_to_dict(msg))

            # No tool calls = agent done reasoning
            if not msg.tool_calls:
                emit_fn(run_id, "agent", "done", "Agent finished reasoning")
                break

            for tool_call in msg.tool_calls:
                tool_call_count += 1
                name = tool_call.function.name

                # Parse args safely
                try:
                    args = json.loads(tool_call.function.arguments) if tool_call.function.arguments else {}
                except json.JSONDecodeError:
                    args = {}
                    emit_fn(run_id, name, "warning", f"Bad arguments for {name}, using defaults")

                emit_fn(run_id, name, "running", f"Calling {name}...")

                # Execute tool
                try:
                    handler = TOOL_DISPATCH.get(name)
                    if handler:
                        tool_result = handler(state, **args)
                    else:
                        tool_result = {"error": f"Unknown tool: {name}"}
                except Exception as e:
                    tool_result = {"error": str(e)}

                # Track tool call
                state.tool_log.append({"tool": name, "args_keys": list(args.keys()), "has_error": "error" in tool_result})

                # Track dedup removals
                if name == "deduplicate_questions" and "removed" in tool_result:
                    state.dedup_removed += tool_result.get("removed", 0)

                result_str = json.dumps(tool_result, default=str)
                summary = _summarize_result(name, tool_result)
                emit_fn(run_id, name, "done", summary)

                # Append compacted tool result to conversation
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": _compact_tool_content(result_str),
                })

                # Submit gate: critique before finalizing
                if name == "submit_question_set":
                    emit_fn(run_id, "critique", "running", "Quality gate — critiquing final set...")
                    critique = _critique_question_set(state)
                    critique_pass = critique.get("pass", True)
                    must_fix = critique.get("must_fix", [])
                    critique_summary = critique.get("summary", "")

                    if critique_pass or revision_round >= MAX_REVISION_ROUNDS:
                        state.submitted = True
                        status = "Passed" if critique_pass else f"Force-passed after {revision_round} revisions"
                        emit_fn(run_id, "critique", "done", f"{status}: {critique_summary}")
                        break
                    else:
                        # Feed must_fix back to agent for revision
                        revision_round += 1
                        fix_msg = f"Quality gate FAILED (round {revision_round}/{MAX_REVISION_ROUNDS}). Fix these issues:\n"
                        for item in must_fix:
                            fix_msg += f"- {item.get('id', '?')}: {item.get('issue', '')} → {item.get('suggestion', '')}\n"
                        fix_msg += "\nFix the issues using remove_question/search_question_bank, then call submit_question_set again."

                        emit_fn(run_id, "critique", "retry", f"Failed — {len(must_fix)} issues, revision {revision_round}")

                        messages.append({"role": "user", "content": fix_msg})
                        # Don't mark submitted — loop continues
                        break

                # Budget warning
                if tool_call_count >= MAX_TOOL_CALLS - 2:
                    emit_fn(run_id, "budget", "warning", f"Budget: {tool_call_count}/{MAX_TOOL_CALLS} tool calls used")

            if state.submitted:
                break

        # ── Build final output ──────────────────────────────────────────

        result.curated_output = state.to_curated_output()

        # Quality report with real metrics
        total_q = state.total_questions
        diff = state.difficulty_counts
        sources = state.source_counts

        # Four weighted metrics
        size_score = 1.0 if MIN_QUESTIONS <= total_q <= MAX_QUESTIONS else max(0.0, 1.0 - abs(total_q - 10) / 10)
        diversity_score = min(1.0, len(sources) / 2)
        diff_target = {"Easy": 0.3, "Medium": 0.5, "Hard": 0.2}
        diff_score = 1.0 - sum(abs(diff.get(k, 0) / max(total_q, 1) - v) for k, v in diff_target.items()) / 2 if total_q > 0 else 0
        answer_score = sum(1 for q in state.questions.values() if q.expected_answer) / max(len(state.questions), 1) if state.questions else 0

        composite = round(0.30 * size_score + 0.25 * diversity_score + 0.25 * diff_score + 0.20 * answer_score, 3)
        # Hard floor: if below min questions, cap at 0.4
        if total_q < MIN_QUESTIONS:
            composite = min(composite, 0.4)

        result.quality_report = QualityReport(
            composite_score=composite,
            metric_scores={
                "set_size": round(size_score, 2),
                "source_diversity": round(diversity_score, 2),
                "difficulty_balance": round(diff_score, 2),
                "answer_coverage": round(answer_score, 2),
            },
            pass_fail="pass" if composite >= 0.6 and total_q >= MIN_QUESTIONS else "fail",
            loops_used=revision_round,
        )

        # Session context
        if state.session_context:
            result.context = state.session_context
        else:
            result.context = SessionContext(
                session_name=config.session_name,
                learning_outcomes=state.learning_outcomes,
                key_concepts=[], scope_in=[], scope_out=[],
                session_type="mixed", matched_kp_ids=[],
                matched_csv_topics=[], prerequisite_kp_chain=[],
                difficulty_distribution={"easy": 0.3, "medium": 0.5, "hard": 0.2},
            )

        emit_fn(run_id, "complete", "done",
                f"Done! {total_q} questions in {tool_call_count} calls, {revision_round} revisions")

    except Exception as e:
        result.error = str(e)
        emit_fn(run_id, "error", "error", str(e))

    return result


# ── Helpers ─────────────────────────────────────────────────────────────────

def _msg_to_dict(msg) -> dict:
    """Convert an OpenAI message object to a serializable dict."""
    d = {"role": msg.role}
    if msg.content:
        d["content"] = msg.content
    if msg.tool_calls:
        d["tool_calls"] = [
            {
                "id": tc.id,
                "type": "function",
                "function": {"name": tc.function.name, "arguments": tc.function.arguments},
            }
            for tc in msg.tool_calls
        ]
    return d


def _summarize_result(tool_name: str, result: dict) -> str:
    """Short summary of a tool result for the progress UI."""
    if "error" in result:
        return f"Error: {result['error'][:80]}"

    summaries = {
        "understand_session": lambda r: f"{r.get('session_type','')} session — {len(r.get('learning_outcomes',[]))} outcomes, {len(r.get('matched_kps',[]))} KPs",
        "search_question_bank": lambda r: f"Found {r.get('found', 0)} relevant (total: {r.get('total_accumulated', 0)}, remaining: {r.get('remaining_capacity', '?')})",
        "validate_relevance": lambda r: f"Kept {r.get('kept', 0)}, removed {r.get('removed', 0)} irrelevant",
        "deduplicate_questions": lambda r: f"Kept {r.get('kept', 0)}, removed {r.get('removed', 0)} duplicates",
        "check_difficulty_balance": lambda r: f"E:{r.get('counts',{}).get('Easy',0)} M:{r.get('counts',{}).get('Medium',0)} H:{r.get('counts',{}).get('Hard',0)} {'OK' if r.get('balanced') else 'Fix'}",
        "check_outcome_coverage": lambda r: f"{r.get('covered',0)}/{r.get('total_outcomes',0)} outcomes covered",
        "generate_expected_answers": lambda r: f"Generated {r.get('generated', 0)} answers",
        "generate_interview_questions": lambda r: f"Generated {r.get('generated', 0)} interview questions (total: {r.get('total_accumulated', '?')})",
        "generate_coding_questions": lambda r: f"Generated {r.get('generated', 0)} coding questions",
        "remove_question": lambda r: f"Removed — {r.get('remaining', '?')} left",
        "submit_question_set": lambda r: f"Submitted {r.get('total_questions',0)} ({r.get('theory',0)}T + {r.get('coding',0)}C)",
    }

    fn = summaries.get(tool_name)
    if fn:
        try:
            return fn(result)
        except Exception:
            pass
    return json.dumps(result)[:100]
