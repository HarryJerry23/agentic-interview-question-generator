"""Tool definitions + implementations for the agentic workflow.

10 tools the agent calls autonomously via OpenRouter tool_use:
1. understand_session — extract outcomes, KPs, session type (MUST be first)
2. search_question_bank — TF-IDF search with session-aware relevance filtering
3. validate_relevance — LLM checks each question against session outcomes
4. deduplicate_questions — TF-IDF dedup
5. check_difficulty_balance — Easy/Medium/Hard distribution
6. check_outcome_coverage — which outcomes are covered
7. generate_expected_answers — LLM generates answer outlines
8. generate_coding_questions — LLM generates coding problems
9. remove_question — drop a specific question
10. submit_question_set — finalize and end the run
"""

from __future__ import annotations
import json
import uuid
from typing import TYPE_CHECKING
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src.models import QuestionDetail, CodingQuestion
from src.llm_client import chat_completion_json


def _usage_cb(state: "AgentState"):
    """Return an on_usage callback that accumulates LLM token stats into state.api_usage."""
    def _cb(usage):
        state.api_usage["llm_calls"] += 1
        state.api_usage["prompt_tokens"] += usage.prompt_tokens or 0
        state.api_usage["completion_tokens"] += usage.completion_tokens or 0
    return _cb


def _url_is_alive(url: str, timeout: float = 4.0) -> bool:
    """HEAD-check a URL; returns True if reachable (or no URL / network error)."""
    if not url:
        return True
    try:
        import requests
        r = requests.head(url, timeout=timeout, allow_redirects=True,
                          headers={"User-Agent": "nxtwave-iqg-bot/1.0"})
        # Anti-bot blocks mean the page exists
        if r.status_code in (401, 403, 429):
            return True
        return r.status_code < 400
    except Exception:
        return True  # network error ≠ dead


from src.config import DEDUP_THRESHOLD
from src.question_bank import get_retriever

if TYPE_CHECKING:
    from src.agent import AgentState


# ── Tool Schemas ────────────────────────────────────────────────────────────

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "understand_session",
            "description": "Analyze session reading material to extract learning outcomes, Knowledge Points (KPs), key concepts, scope boundaries, and session type. Returns structured context + suggested search queries. MUST be called FIRST before any search.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_question_bank",
            "description": "Search the pre-indexed question bank (~2000+ questions). Uses TF-IDF similarity + session-aware relevance filtering. Use the suggested_search_queries from understand_session as queries. Do NOT invent generic terms.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "A KP label or learning outcome from understand_session (e.g., 'Configure Gemini API authentication and key management'). Be specific."
                    },
                    "difficulty": {
                        "type": "string",
                        "enum": ["Easy", "Medium", "Hard"],
                        "description": "Optional difficulty filter"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max results (default 8)"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_github_questions",
            "description": "Search verified GitHub repositories for real interview questions matching the given learning outcomes. Use when the question bank is thin for a topic — returns questions as actually written in open-source interview prep repos.",
            "parameters": {
                "type": "object",
                "properties": {
                    "outcomes": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Learning outcome phrases to search for (e.g. ['rag evaluation metrics', 'prompt injection defense']). Use plain phrases, not snake_case."
                    }
                },
                "required": ["outcomes"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_web_questions",
            "description": "Search 45+ verified domains (Glassdoor, AmbitionBox, Exponent, GeeksforGeeks, LeetCode, etc.) for real interview questions with company attribution via Tavily. Requires TAVILY_API_KEY. Use when you need questions that came from actual company interviews.",
            "parameters": {
                "type": "object",
                "properties": {
                    "outcomes": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Learning outcome phrases to search for (e.g. ['RAG evaluation', 'LLM fine-tuning'])."
                    }
                },
                "required": ["outcomes"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "validate_relevance",
            "description": "LLM evaluates ALL accumulated questions against the session's learning outcomes. Removes questions that don't match any outcome. Call AFTER all searches, BEFORE submitting.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "deduplicate_questions",
            "description": "Remove near-duplicate questions (cosine similarity > 0.85).",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_difficulty_balance",
            "description": "Check current Easy/Medium/Hard distribution against target (30/50/20).",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_outcome_coverage",
            "description": "Check which learning outcomes are covered by current questions and which are missing.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_expected_answers",
            "description": "Generate 2-3 bullet answer outlines for questions that lack them.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_coding_questions",
            "description": "Generate coding interview problems. Only for code-heavy or mixed sessions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "count": {"type": "integer", "description": "Number of coding questions (1-4)"},
                    "topics": {
                        "type": "array", "items": {"type": "string"},
                        "description": "Specific topics from the session"
                    },
                    "language": {"type": "string", "description": "Programming language (default: Python)"}
                },
                "required": ["count"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_interview_questions",
            "description": "LLM generates theory/conceptual interview questions based on session learning outcomes. Use when the question bank doesn't have enough relevant questions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "count": {"type": "integer", "description": "Number of questions to generate (1-10)"},
                    "outcomes": {
                        "type": "array", "items": {"type": "string"},
                        "description": "Learning outcomes to generate questions for"
                    },
                    "difficulty_mix": {
                        "type": "string",
                        "description": "Difficulty distribution hint, e.g., '3 Easy, 4 Medium, 3 Hard'"
                    }
                },
                "required": ["count", "outcomes"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "remove_question",
            "description": "Remove a specific question from the set.",
            "parameters": {
                "type": "object",
                "properties": {
                    "question_id": {"type": "string"},
                    "reason": {"type": "string"}
                },
                "required": ["question_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "submit_question_set",
            "description": "Finalize and submit the question set for human review. THIS ENDS THE RUN. Only call when you have 5-15 relevant questions.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
]


# ── Tool Implementations ────────────────────────────────────────────────────

def tool_understand_session(state: AgentState) -> dict:
    """Step 1: LLM reads session RM, extracts outcomes, maps to KPs."""
    from src.session_understanding import understand_session

    context = understand_session(state.config.session_names, state.data_store)
    state.session_context = context
    state.learning_outcomes = context.learning_outcomes

    # Build KP-label queries; also add "interview"-suffixed variants for better TF-IDF recall
    kp_queries = [
        kp.kp_label for kp in context.matched_kp_ids if kp.relevance >= 0.5
    ]
    # Interview-phrased variants improve matching against company question content
    interview_queries = [f"{q} interview" for q in kp_queries[:3]]
    all_queries = (kp_queries + interview_queries)[:8]

    # Probe the bank with the top query to estimate coverage for this session
    has_bank_questions = False
    estimated_bank_count = 0
    if all_queries:
        retriever = get_retriever()
        probe = retriever.search(all_queries[0], limit=5)
        estimated_bank_count = len(probe) * min(len(all_queries), 5)
        has_bank_questions = len(probe) > 0

    state.has_bank_questions = has_bank_questions

    bank_hint = (
        f"Bank has ~{estimated_bank_count}+ potential matches for this session."
        if has_bank_questions
        else "Bank may have few/no questions for this topic — prioritise search_github_questions and search_web_questions after bank searches."
    )

    return {
        "session_name": context.session_name,
        "session_type": context.session_type,
        "learning_outcomes": context.learning_outcomes,
        "key_concepts": context.key_concepts,
        "scope_in": context.scope_in,
        "scope_out": context.scope_out,
        "matched_kps": [
            {"kp_id": kp.kp_id, "label": kp.kp_label, "relevance": kp.relevance}
            for kp in context.matched_kp_ids
        ],
        "suggested_search_queries": all_queries,
        "has_bank_questions": has_bank_questions,
        "estimated_bank_question_count": estimated_bank_count,
        "instruction": f"Use suggested_search_queries for search_question_bank. {bank_hint}",
    }


def tool_search_question_bank(state: AgentState, query: str, difficulty: str = None, limit: int = 8) -> dict:
    """Search question bank with TF-IDF + session-aware relevance filtering."""
    retriever = get_retriever()

    current = len(state.questions) + len(state.coding_questions)
    max_to_add = state.config.max_questions - current
    if max_to_add <= 0:
        return {"found": 0, "warning": f"Already at max ({state.config.max_questions}). Remove some or submit."}

    actual_limit = min(limit, max_to_add, 8)
    exclude_ids = set(state.questions.keys())

    results = retriever.search(
        query=query, difficulty=difficulty,
        limit=actual_limit + 5,  # fetch extra for filtering
        exclude_ids=exclude_ids,
    )

    # Session-aware post-retrieval relevance filter
    if state.session_context:
        scope_keywords = set()
        for term in (state.session_context.learning_outcomes +
                     state.session_context.key_concepts +
                     state.session_context.scope_in):
            scope_keywords.update(
                w.lower() for w in term.split()
                if len(w) >= 4 and w.lower() not in {
                    "with", "that", "this", "from", "what", "have", "will",
                    "about", "between", "their", "using", "should", "could",
                    "would", "does", "they", "been", "more", "than", "also",
                    "each", "when", "which", "into", "some", "other",
                }
            )

        filtered = []
        for qd in results:
            content_lower = qd.content.lower()
            matches = sum(1 for kw in scope_keywords if kw in content_lower)
            # Require at least 1 keyword match for short Qs, 2 for longer ones
            min_required = 1 if len(qd.content) < 100 else 2
            if matches >= min_required:
                filtered.append(qd)
        results = filtered[:actual_limit]

    added = []
    for qd in results:
        state.questions[qd.question_id] = qd
        added.append({
            "id": qd.question_id,
            "content": qd.content[:150],
            "difficulty": qd.difficulty,
            "topic": qd.topic,
            "source": qd.source,
        })

    total = len(state.questions) + len(state.coding_questions)
    return {
        "found": len(added),
        "questions": added,
        "total_accumulated": total,
        "remaining_capacity": state.config.max_questions - total,
    }


def tool_validate_relevance(state: AgentState) -> dict:
    """LLM evaluates each question's relevance to session outcomes."""
    if not state.session_context or not state.questions:
        return {"error": "Call understand_session first and gather questions"}

    from src import memory as _memory
    learned_rules = _memory.get_learned_rules()
    rules_block = ""
    if learned_rules:
        rules_block = (
            "## Learned rejection rules (apply these first):\n"
            + "\n".join(f"- {r}" for r in learned_rules[:20])
            + "\n\n"
        )

    outcomes_str = "\n".join(f"- {o}" for o in state.session_context.learning_outcomes)
    concepts_str = ", ".join(state.session_context.key_concepts)
    scope_out_str = ", ".join(state.session_context.scope_out) if state.session_context.scope_out else "none"

    q_list = []
    for q in state.questions.values():
        q_list.append({"id": q.question_id, "content": q.content[:250]})

    result = chat_completion_json(
        system_prompt=f"""{rules_block}You are evaluating interview questions for relevance to a specific session.

Session: {state.session_context.session_name}

Learning Outcomes:
{outcomes_str}

Key Concepts: {concepts_str}
Out of Scope: {scope_out_str}

For EACH question, decide:
- "keep" — related to this session's topic, concepts, or learning outcomes
- "remove" — clearly off-topic (tests a completely different technology or domain not covered in this session)

Respond in JSON:
{{"evaluations": [{{"id": "...", "verdict": "keep", "reason": "Tests outcome X"}}]}}

IMPORTANT: Be LENIENT. Keep a question if it touches any concept related to the session topic.
Only remove questions that are entirely unrelated (e.g. a SQL question in a React session).
Foundational questions about the session's core technology (e.g. "What is RAG?" for a RAG session) should always be KEPT.""",
        user_prompt=f"Questions to evaluate:\n{json.dumps(q_list)}",
        max_tokens=2048,
        on_usage=_usage_cb(state),
    )

    evaluations = result.get("evaluations", [])
    eval_map = {e.get("id", ""): e for e in evaluations}

    # Determine what to remove BEFORE mutating state
    to_remove = []
    for q_id, q in state.questions.items():
        ev = eval_map.get(q_id, {})
        if ev.get("verdict") == "remove":
            to_remove.append((q_id, q.content[:80], ev.get("reason", "")))

    # Safety floor: never remove more than 50% of questions,
    # and never leave 0 results — questions passed TF-IDF already.
    max_removable = max(0, len(state.questions) // 2)
    to_remove = to_remove[:max_removable]

    for q_id, content, reason in to_remove:
        state.questions.pop(q_id, None)

    kept = len(state.questions)
    removed = len(to_remove)

    return {
        "kept": kept,
        "removed": removed,
        "removed_questions": [{"id": q_id, "content": c, "reason": r} for q_id, c, r in to_remove],
        "remaining_total": len(state.questions) + len(state.coding_questions),
    }


def tool_deduplicate_questions(state: AgentState) -> dict:
    if len(state.questions) <= 1:
        return {"kept": len(state.questions), "removed": 0}

    questions = list(state.questions.values())
    texts = [q.content for q in questions]
    vectorizer = TfidfVectorizer(stop_words="english", max_features=5000)
    tfidf_matrix = vectorizer.fit_transform(texts)
    sim_matrix = cosine_similarity(tfidf_matrix)

    source_priority = {"interview_db": 0, "web": 1, "generated": 2}
    to_remove = set()
    for i in range(len(questions)):
        if i in to_remove:
            continue
        for j in range(i + 1, len(questions)):
            if j in to_remove:
                continue
            if sim_matrix[i][j] > DEDUP_THRESHOLD:
                pri_i = source_priority.get(questions[i].source, 9)
                pri_j = source_priority.get(questions[j].source, 9)
                to_remove.add(j if pri_i <= pri_j else i)

    for idx in to_remove:
        state.questions.pop(questions[idx].question_id, None)

    within_run_removed = len(to_remove)

    # Cross-run dedup: remove questions too similar to previously approved ones
    cross_run_removed = 0
    if state.session_context:
        try:
            from src import memory as _memory
            bank_qs = _memory.get_bank_questions(state.session_context.session_name)
            if bank_qs and state.questions:
                bank_texts = [b["content"] for b in bank_qs]
                current_qs = list(state.questions.values())
                current_texts = [q.content for q in current_qs]
                all_texts = bank_texts + current_texts
                vec2 = TfidfVectorizer(stop_words="english", max_features=5000)
                tfidf2 = vec2.fit_transform(all_texts)
                bank_mat = tfidf2[:len(bank_texts)]
                curr_mat = tfidf2[len(bank_texts):]
                cross_sim = cosine_similarity(curr_mat, bank_mat)
                for i, row in enumerate(cross_sim):
                    if row.max() > DEDUP_THRESHOLD:
                        state.questions.pop(current_qs[i].question_id, None)
                        cross_run_removed += 1
        except Exception:
            pass

    return {
        "kept": len(state.questions),
        "removed": within_run_removed,
        "cross_run_removed": cross_run_removed,
    }


def tool_check_difficulty_balance(state: AgentState) -> dict:
    counts = {"Easy": 0, "Medium": 0, "Hard": 0}
    for q in state.questions.values():
        counts[q.difficulty or "Medium"] = counts.get(q.difficulty or "Medium", 0) + 1
    for q in state.coding_questions.values():
        counts[q.difficulty or "Medium"] = counts.get(q.difficulty or "Medium", 0) + 1
    total = sum(counts.values())
    actual = {k: round(v / max(total, 1), 2) for k, v in counts.items()}
    balanced = total > 0 and all(abs(actual.get(k, 0) - v) < 0.25 for k, v in {"Easy": 0.30, "Medium": 0.50, "Hard": 0.20}.items())
    return {"total": total, "counts": counts, "actual_pct": actual, "balanced": balanced}


def tool_check_outcome_coverage(state: AgentState) -> dict:
    if not state.session_context:
        return {"error": "Call understand_session first"}
    outcomes = state.session_context.learning_outcomes
    all_content = " ".join(q.content.lower() for q in state.questions.values())
    all_content += " " + " ".join(q.content.lower() for q in state.coding_questions.values())

    covered, missing = [], []
    for outcome in outcomes:
        words = [w.lower() for w in outcome.split() if len(w) > 3]
        if any(w in all_content for w in words):
            covered.append(outcome)
        else:
            missing.append(outcome)
    return {
        "total_outcomes": len(outcomes), "covered": len(covered),
        "missing_count": len(missing), "missing": missing,
        "coverage_pct": round(len(covered) / max(len(outcomes), 1), 2),
    }


def tool_generate_expected_answers(state: AgentState) -> dict:
    needs_answers = [q for q in state.questions.values() if not q.expected_answer]
    if not needs_answers:
        return {"generated": 0, "message": "All questions already have answers"}
    batch = needs_answers[:15]
    q_list = "\n".join(f"{i+1}. {q.content[:250]}" for i, q in enumerate(batch))
    result = chat_completion_json(
        system_prompt="""Generate concise expected answer outlines for these interview questions.
For each, provide 2-3 bullet points as a SINGLE STRING with bullets separated by newlines.
Respond in JSON: {"answers": ["- point1\\n- point2", ...]}""",
        user_prompt=f"Questions:\n{q_list}", max_tokens=3000,
        on_usage=_usage_cb(state),
    )
    answers = result.get("answers", [])
    for i, q in enumerate(batch):
        if i < len(answers):
            ans = answers[i]
            q.expected_answer = "\n".join(str(a) for a in ans) if isinstance(ans, list) else str(ans) if ans else None
    return {"generated": min(len(answers), len(batch))}


def tool_generate_interview_questions(state: AgentState, count: int, outcomes: list[str], difficulty_mix: str = None) -> dict:
    """Blocked — only real company interview questions from the bank and live sources are used."""
    return {
        "generated": 0,
        "blocked": True,
        "reason": (
            "Question generation is disabled. Only real company interview questions are used. "
            "Try more searches with search_question_bank, search_github_questions, or search_web_questions. "
            "If all sources are exhausted, call submit_question_set with what you have."
        ),
    }


def tool_generate_coding_questions(state: AgentState, count: int, topics: list[str] = None, language: str = "Python") -> dict:
    """Generate coding questions in Nxtmock portal format: concise content + separate starter code."""
    from src.models import CodeSnippet

    count = min(count, 4)
    max_to_add = state.config.max_questions - len(state.questions) - len(state.coding_questions)
    count = min(count, max(0, max_to_add))
    if count <= 0:
        return {"generated": 0, "warning": "At max capacity"}

    topics_str = ", ".join(topics) if topics else state.config.session_name
    lang_upper = language.upper()

    result = chat_completion_json(
        system_prompt=f"""Generate {count} coding interview questions about: {topics_str}.

IMPORTANT FORMAT — match this exact style:

For each question provide:
- title: Short name (e.g., "Build a Gemini API Chat Function")
- content: Plain text problem description. Concise, 1-4 sentences describing what to build. Include sample input/output if applicable. Do NOT use markdown headers (no ## or **).
- difficulty: "Easy", "Medium", or "Hard" (vary them)
- topic: Clean topic name
- starter_code: A {language} code template with the function signature and a "# Write your code here" comment. Just the skeleton, no solution.

Example output format:
{{
    "title": "Build a Gemini API Chat Function",
    "content": "Write a function that connects to the Google Gemini API using the google-genai package, sends a user prompt, and returns the model's text response. The function should load the API key from environment variables.\\n\\nSample Input: prompt = 'What is machine learning?'\\nSample Output: 'Machine learning is a subset of AI...'",
    "difficulty": "Medium",
    "topic": "Gemini API",
    "starter_code": "import os\\nfrom google import genai\\n\\ndef chat_with_gemini(prompt: str) -> str:\\n    # Write your code here\\n    pass"
}}

Respond in JSON: {{"coding_questions": [...]}}""",
        user_prompt=f"Generate {count} coding questions in {language}.", max_tokens=4000,
        on_usage=_usage_cb(state),
    )

    added = []
    for cq_data in result.get("coding_questions", []):
        q_id = str(uuid.uuid4())
        code_id = str(uuid.uuid4())
        starter = cq_data.get("starter_code", f"# Write your {language} code here\n")

        cq = CodingQuestion(
            id=q_id,
            category=f"{lang_upper}_CODING",
            title=cq_data.get("title", "Coding Question"),
            content=cq_data.get("content", ""),
            code_id=code_id,
            topic=cq_data.get("topic", topics_str[:50]),
            difficulty=cq_data.get("difficulty", "Medium"),
            language=language,
            source="generated",
        )
        state.coding_questions[q_id] = cq

        # Store starter code as separate CodeSnippet
        snippet = CodeSnippet(
            code_id=code_id,
            code_content=starter,
            language=lang_upper,
        )
        state.code_snippets[code_id] = snippet

        added.append({"id": q_id, "title": cq.title, "difficulty": cq.difficulty})
    return {"generated": len(added), "questions": added}


def tool_search_github_questions(state: AgentState, outcomes: list) -> dict:
    """Harvest real interview questions from verified GitHub repos via the GitHub REST API."""
    from src.sources.github_repo import GithubRepoConnector
    records = GithubRepoConnector().fetch(outcomes)

    current = len(state.questions) + len(state.coding_questions)
    capacity = state.config.max_questions - current
    if capacity <= 0:
        return {"found": 0, "warning": f"Already at max ({state.config.max_questions})."}

    added = []
    for rec in records[:capacity]:
        q_id = str(uuid.uuid4())
        qd = QuestionDetail(
            question_id=q_id,
            category="THEORY",
            content=rec.question_text,
            topic=rec.source_type.split(":")[-1] if ":" in rec.source_type else "Interview",
            difficulty="Medium",
            source="web",
            source_url=rec.source_url,
        )
        state.questions[q_id] = qd
        added.append({
            "id": q_id,
            "content": rec.question_text[:150],
            "source_url": rec.source_url,
            "source_type": rec.source_type,
        })

    total = len(state.questions) + len(state.coding_questions)
    return {
        "found": len(records),
        "added": len(added),
        "total_accumulated": total,
        "remaining_capacity": state.config.max_questions - total,
    }


def tool_search_web_questions(state: AgentState, outcomes: list) -> dict:
    """Harvest real interview questions with company attribution from 45+ verified domains via Tavily."""
    from src import config as cfg
    if not cfg.TAVILY_API_KEY:
        return {"error": "TAVILY_API_KEY not set — skipping web search", "status": "skipped"}

    from src.sources.tavily_search import TavilyConnector
    # Use scope_in (short topic labels) as primary queries — better Tavily recall than full
    # outcome sentences. Supplement with whatever the agent passed.
    ctx = state.session_context
    search_terms = list(ctx.scope_in[:5]) if (ctx and ctx.scope_in) else []
    for out in outcomes:
        if out.lower() not in {t.lower() for t in search_terms}:
            search_terms.append(out)
    search_terms = search_terms[:8]
    records, tavily_calls = TavilyConnector().fetch(search_terms or outcomes)
    state.api_usage["tavily_calls"] += tavily_calls

    # Link-aliveness check: filter dead source URLs (HEAD-check first 10, keep rest unchecked)
    if len(records) >= 5:
        import concurrent.futures
        to_check, rest = records[:10], records[10:]
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:
            alive_flags = list(ex.map(lambda r: _url_is_alive(r.source_url), to_check))
        records = [r for r, ok in zip(to_check, alive_flags) if ok] + rest

    current = len(state.questions) + len(state.coding_questions)
    capacity = state.config.max_questions - current
    if capacity <= 0:
        return {"found": 0, "warning": f"Already at max ({state.config.max_questions})."}

    # Prioritise attributed company questions and premium sources over Reddit noise
    _PRIORITY_SOURCES = {"tryexponent.com", "ambitionbox.com", "glassdoor.com",
                         "interviewquery.com", "datalemur.com", "prepfully.com",
                         "igotanoffer.com", "leetcode.com"}
    records.sort(key=lambda r: (
        0 if r.company else 1,
        0 if any(s in r.source_type for s in _PRIORITY_SOURCES) else 1,
    ))

    # Use session topic for proper metadata
    session_topic = (state.session_context.key_concepts[0]
                     if state.session_context and state.session_context.key_concepts
                     else "Interview")

    # Build a set of topic keywords for pre-filtering (avoids off-topic guide pages)
    topic_keywords: set[str] = set()
    if ctx:
        for term in (ctx.scope_in + ctx.key_concepts + ctx.learning_outcomes):
            for w in term.lower().split():
                if len(w) >= 4 and w not in {
                    "with", "that", "this", "from", "what", "have", "will",
                    "about", "using", "build", "create", "learn", "your",
                    "into", "some", "each", "when", "which", "should",
                }:
                    topic_keywords.add(w)

    # Take up to capacity+10; pre-filter by topic relevance first
    take = min(len(records), capacity + 20)
    added = []
    for rec in records[:take]:
        # Skip records with no topical relevance to this session
        if topic_keywords:
            q_lower = rec.question_text.lower()
            if not any(kw in q_lower for kw in topic_keywords):
                continue

        if len(added) >= capacity + 10:
            break

        q_id = str(uuid.uuid4())
        qd = QuestionDetail(
            question_id=q_id,
            category="GEN_AI",
            content=rec.question_text,
            topic=session_topic,
            difficulty="Medium",
            source="web",
            asked_in_company=rec.company,
            source_url=rec.source_url,
        )
        state.questions[q_id] = qd
        added.append({
            "id": q_id,
            "content": rec.question_text[:150],
            "company": rec.company,
            "source_url": rec.source_url,
            "source_type": rec.source_type,
        })

    total = len(state.questions) + len(state.coding_questions)
    return {
        "found": len(records),
        "added": len(added),
        "total_accumulated": total,
        "remaining_capacity": state.config.max_questions - total,
    }


def tool_remove_question(state: AgentState, question_id: str, reason: str = "") -> dict:
    if question_id in state.questions:
        state.questions.pop(question_id)
        return {"removed": True, "remaining": len(state.questions) + len(state.coding_questions)}
    if question_id in state.coding_questions:
        state.coding_questions.pop(question_id)
        return {"removed": True, "remaining": len(state.questions) + len(state.coding_questions)}
    return {"removed": False, "error": f"Question {question_id} not found"}


def tool_submit_question_set(state: AgentState) -> dict:
    total = len(state.questions) + len(state.coding_questions)
    if total > state.config.max_questions:
        excess = total - state.config.max_questions
        for q_id in list(reversed(list(state.questions.keys())))[:excess]:
            state.questions.pop(q_id)
        total = len(state.questions) + len(state.coding_questions)
    state.submitted = True
    return {"submitted": True, "total_questions": total, "theory": len(state.questions), "coding": len(state.coding_questions)}


# ── Dispatch ────────────────────────────────────────────────────────────────

TOOL_DISPATCH = {
    "understand_session": tool_understand_session,
    "search_question_bank": tool_search_question_bank,
    "search_github_questions": tool_search_github_questions,
    "search_web_questions": tool_search_web_questions,
    "validate_relevance": tool_validate_relevance,
    "deduplicate_questions": tool_deduplicate_questions,
    "check_difficulty_balance": tool_check_difficulty_balance,
    "check_outcome_coverage": tool_check_outcome_coverage,
    "generate_expected_answers": tool_generate_expected_answers,
    "generate_interview_questions": tool_generate_interview_questions,
    "generate_coding_questions": tool_generate_coding_questions,
    "remove_question": tool_remove_question,
    "submit_question_set": tool_submit_question_set,
}
