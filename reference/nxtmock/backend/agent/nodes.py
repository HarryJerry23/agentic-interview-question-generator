"""All workflow nodes: assemble → split → process_set (×2) → human_gate → finalize.

Design notes
------------
* **Full-text split.** `assemble` takes the session's EXACT original Markdown (`get_source`) and
  cuts it into ordered heading sections whose concatenation reproduces the text byte-for-byte.
  `split` only chooses a seam index; `set_a.text + set_b.text == full session text` — never sampled.
* **One node per set.** `process_set` runs plan → generate → (concept-check ↔ refine) for ONE set
  end-to-end, so the two sets fan out cleanly and each loops on its own counter with no routing race.
* **Store access** is the `app_store()` singleton (feedback rules, ready-for-rubric hand-off).
"""
from __future__ import annotations

import re
from typing import Any, Dict, List

from langgraph.types import Send, interrupt
from pydantic import BaseModel, Field

from backend.agent.events import emit
from backend.agent.feedback import distill_and_persist, rules_block
from backend.agent.llm import fill, get_critic_llm, get_llm, load_prompt
from backend.agent.mcq_parser import parse_mcq_blocks, parse_one_block, render_code_fields, structural_ok
from backend.agent.provenance import _sum_usage, make_usage_cb, record_prompt, record_result, traced
from backend.domain.models import Question
from backend.domain.state import MAX_REFINE_ROUNDS, MIN_REFINE_ROUNDS
from backend.memory import app_store, get_source

_HEADING = re.compile(r"^(#{1,6})\s+\S", re.MULTILINE)

# Fenced code blocks: ```lang\n …body… ``` (lang optional). Used to decide if a session is a
# coding session and in which language(s) — Feature 7.
_FENCE = re.compile(r"```([A-Za-z0-9_+#.-]*)\r?\n(.*?)```", re.DOTALL)
# Fence tags → the CODE_LANGUAGE vocabulary the portal/prompts use. Unknown/text tags are ignored.
_LANG_ALIASES = {
    "py": "PYTHON", "python": "PYTHON", "python3": "PYTHON", "ipython": "PYTHON",
    "js": "JS", "javascript": "JS", "node": "JS", "ts": "JS", "typescript": "JS",
    "jsx": "REACT", "tsx": "REACT", "react": "REACT",
    "java": "JAVA", "html": "HTML", "xml": "HTML", "css": "CSS", "scss": "CSS",
    "sql": "SQL", "postgres": "SQL", "mysql": "SQL",
    "sh": "SHELL", "bash": "SHELL", "shell": "SHELL", "zsh": "SHELL", "console": "SHELL",
    "json": "JSON", "c": "C", "cpp": "CPP", "c++": "CPP", "cs": "CSHARP", "csharp": "CSHARP",
    "go": "GO", "golang": "GO", "rust": "RUST", "rb": "RUBY", "ruby": "RUBY", "php": "PHP", "kotlin": "KOTLIN",
}
# Tags that are prose/config, never counted as program code. NOTE: an EMPTY tag is deliberately not
# here — an untagged fence (```\n…```) is common for code, so it must fall through to _looks_like_code.
_NON_CODE_TAGS = {"text", "txt", "plaintext", "markdown", "md", "none", "output", "yaml", "yml", "toml", "ini", "diff"}


def _looks_like_code(body: str) -> bool:
    """Cheap heuristic: does an untagged fenced block look like program code (not prose/output)?"""
    hits = sum(tok in body for tok in
               ("();", "()", "{", "};", "= ", "def ", "function", "import ", "print(", "return ",
                "console.", "</", "/>", "SELECT ", "#include", "public ", "var ", "const ", "let "))
    return hits >= 2


def _detect_code(md: str) -> tuple[bool, list[str], str]:
    """Detect whether a session is a coding session + its language(s), from fenced code blocks.

    Returns (is_coding, languages_most_frequent_first, primary_language). A session counts as coding
    when it has ≥2 recognized code blocks, or ≥1 block with ≥200 chars of code — so an article with a
    single incidental snippet is not treated as a coding session.
    """
    from collections import Counter
    langs: list[str] = []
    n_code = 0
    code_chars = 0
    for tag, body in _FENCE.findall(md or ""):
        tagl = tag.strip().lower()
        norm = _LANG_ALIASES.get(tagl)
        if norm is None and tagl in _NON_CODE_TAGS:
            continue
        # Recognized language, OR an untagged/unknown fence that looks like code.
        if norm is not None or _looks_like_code(body):
            n_code += 1
            code_chars += len(body)
            if norm:
                langs.append(norm)
    is_coding = n_code >= 2 or (n_code >= 1 and code_chars >= 200)
    ordered = [l for l, _ in Counter(langs).most_common()]
    return is_coding, ordered, (ordered[0] if ordered else "")


# ── Structured-output schemas (for the JSON-emitting nodes) ──────────────────────

class _SetSplit(BaseModel):
    topics: List[str] = Field(default_factory=list)
    outcomes: List[str] = Field(default_factory=list)


class _SplitResult(BaseModel):
    seam_index: int
    set_a: _SetSplit = Field(default_factory=_SetSplit)
    set_b: _SetSplit = Field(default_factory=_SetSplit)


class _PlanResult(BaseModel):
    outcomes: List[str] = Field(default_factory=list)


class _OneCheck(BaseModel):
    qid: str
    met: bool = False
    reason: str = ""


class _CheckResult(BaseModel):
    checks: List[_OneCheck] = Field(default_factory=list)
    confidence: float = 0.0


class _LangResult(BaseModel):
    """LLM fallback when code blocks exist but carry no language tag (Feature 7)."""
    is_coding: bool = False
    primary_language: str = ""   # one of PYTHON/JS/JAVA/HTML/CSS/SQL/REACT/SHELL/JSON/…, or ""


# ── Section splitter (preserves the full text exactly) ───────────────────────────

def _split_into_sections(md: str) -> List[Dict[str, Any]]:
    """Cut Markdown into ordered sections at heading lines, preserving every character.

    Concatenating section['text'] in order reproduces `md` exactly. Section 0 is any preamble
    before the first heading.
    """
    starts = [m.start() for m in _HEADING.finditer(md)]
    bounds = ([0] if (not starts or starts[0] != 0) else []) + starts + [len(md)]
    bounds = sorted(set(bounds))
    sections: List[Dict[str, Any]] = []
    for i in range(len(bounds) - 1):
        text = md[bounds[i]:bounds[i + 1]]
        if not text.strip():
            continue
        first = text.lstrip().splitlines()[0] if text.strip() else ""
        heading = first.lstrip("#").strip() if first.startswith("#") else "(intro)"
        sections.append({
            "idx": len(sections),
            "heading": heading,
            "text": text,
            "token_count": len(text.split()),
        })
    return sections


def _render_sections(sections: List[Dict[str, Any]]) -> str:
    lines = []
    for s in sections:
        snippet = " ".join(s["text"].split())[:160]
        lines.append(f"[{s['idx']}] {s['heading']} — {snippet}")
    return "\n".join(lines)


def _render_questions(questions: List[Question]) -> str:
    out = []
    for q in questions:
        opts = "\n".join(f"  {k}: {v}" for k, v in sorted(q.options.items()))
        out.append(
            f"qid: {q.qid}\ncovers_concept: {q.covers_concept}\n"
            f"QUESTION: {q.question_text}\n{opts}\n"
            f"CORRECT: {q.correct_option}\nEXPLANATION: {q.explanation}"
        )
    return "\n---\n".join(out)


# ── Nodes ────────────────────────────────────────────────────────────────────────

def _load_module_content(store, course: str, session_ids: List[str]
                         ) -> tuple[str, List[str], str, List[Dict[str, Any]]]:
    """Merge several sessions into one body for a module quiz (Feature 9): concatenate their text in
    selected order under per-session headers, union their outcomes (order-preserving dedupe), and
    build a combined title. Also return a per-session list `[{title, text, outcomes}]` so planning can
    pick the most-important concepts FROM EACH session independently (≥6/session, no cap). Missing
    sessions are skipped."""
    parts, outcomes, titles = [], [], []
    sessions: List[Dict[str, Any]] = []
    seen = set()
    for sid in session_ids:
        src = get_source(store, course, sid)
        if src is None:
            continue
        title = src.get("session_title", sid)
        text = src.get("text", "")
        s_outcomes = list(src.get("outcomes", []) or [])
        titles.append(title)
        parts.append(f"\n\n## {title}\n\n{text}")
        sessions.append({"title": title, "text": text, "outcomes": s_outcomes})
        for o in s_outcomes:
            if o not in seen:
                seen.add(o)
                outcomes.append(o)
    combined_title = " + ".join(titles) if titles else "module"
    return "".join(parts).lstrip("\n"), outcomes, combined_title, sessions


def assemble(state: Dict[str, Any]) -> Dict[str, Any]:
    course, session = state["course"], state["session"]
    run_id = state["run_id"]
    module_sessions: List[Dict[str, Any]] = []
    if state.get("workflow") in ("module_quiz", "mock_interview"):
        # Merge the selected sessions into one body; `session` is the slugified module/topic identity.
        # (mock_interview reuses this merge; it then harvests real interview questions — Feature 11.)
        full_text, outcomes, title, module_sessions = _load_module_content(
            app_store(), course, state.get("sessions", []))
        if not full_text.strip():
            emit(run_id, "assemble", {"error": "no selected sessions found"}, level="error")
            return {"status": "error", "sections": [], "course_outcomes": []}
        src = {"text": full_text, "outcomes": outcomes,
               "session_title": state.get("module_name") or state.get("topic_name") or title}
    else:
        src = get_source(app_store(), course, session)
        if src is None:
            emit(run_id, "assemble", {"error": "session not found"}, level="error")
            return {"status": "error", "sections": [], "course_outcomes": []}
    full_text = src.get("text", "")
    sections = _split_into_sections(full_text)
    outcomes = src.get("outcomes", []) or []

    # Coding detection (Feature 7): heuristic from fenced code blocks; LLM fallback only when code is
    # clearly present but no language tag was found (so we still know what language to author in).
    is_coding, code_languages, primary_language = _detect_code(full_text)
    if is_coding and not primary_language:
        try:
            res = traced(run_id, "detect_lang", "inline:detect_lang",
                         "Classify the primary programming language of this material. Reply with one "
                         "token from PYTHON/JS/JAVA/HTML/CSS/SQL/REACT/SHELL/JSON or empty if not code.\n\n"
                         + full_text[:4000],
                         lambda p, cfg: get_critic_llm().with_structured_output(_LangResult).invoke(p, config=cfg))
            primary_language = (res.primary_language or "").strip().upper()
            if primary_language:
                code_languages = [primary_language]
            is_coding = bool(res.is_coding) and bool(primary_language)
        except Exception as exc:
            emit(run_id, "assemble", {"warn": f"language classify failed: {exc}"}, level="warn")

    emit(run_id, "assemble", {
        "section_count": len(sections),
        "char_count": len(full_text),
        "session_title": src.get("session_title", session),
        "is_coding": is_coding,
        "code_languages": code_languages,
        "primary_language": primary_language,
    })
    return {
        "session_title": src.get("session_title", session),
        "content_ref": f"{course}/{session}",
        "sections": sections,
        "course_outcomes": outcomes,
        "module_sessions": module_sessions,   # per-session [{title,text,outcomes}] for module planning
        "is_coding": is_coding,
        "code_languages": code_languages,
        "primary_language": primary_language,
        "status": "running",
    }


def split(state: Dict[str, Any]) -> Dict[str, Any]:
    run_id = state["run_id"]
    sections: List[Dict[str, Any]] = state.get("sections", [])
    n = len(sections)
    if n == 0:
        emit(run_id, "split", {"error": "no sections"}, level="error")
        return {"status": "error"}

    prompt = fill(
        load_prompt("01_split_session"),
        session_title=state.get("session_title", state["session"]),
        sections=_render_sections(sections),
        course_outcomes="\n".join(f"- {o}" for o in state.get("course_outcomes", [])) or "(none)",
    )
    seam = max(1, n // 2)  # safe fallback: midpoint
    res: _SplitResult | None = None
    if n >= 2:
        try:
            res = traced(run_id, "split", "01_split_session", prompt,
                         lambda p, cfg: get_critic_llm().with_structured_output(_SplitResult).invoke(p, config=cfg))
            if 1 <= res.seam_index < n:
                seam = res.seam_index
        except Exception as exc:
            emit(run_id, "split", {"warn": f"LLM split failed, using midpoint: {exc}"}, level="warn")

    a_idx, b_idx = list(range(0, seam)), list(range(seam, n))
    a_text = "".join(sections[i]["text"] for i in a_idx)
    b_text = "".join(sections[i]["text"] for i in b_idx)
    # Full-text invariant: the two halves must reproduce the whole session, no overlap, no loss.
    full_ok = (a_text + b_text) == "".join(s["text"] for s in sections) and not (set(a_idx) & set(b_idx))

    def _topics(idxs, fallback):
        return fallback or [sections[i]["heading"] for i in idxs if sections[i]["heading"] != "(intro)"]

    set_plan = {
        "set_a": {
            "set_label": "set_a", "section_idx": a_idx, "text": a_text,
            "topics": _topics(a_idx, res.set_a.topics if res else []),
            "outcomes": (res.set_a.outcomes if res else []),
        },
        "set_b": {
            "set_label": "set_b", "section_idx": b_idx, "text": b_text,
            "topics": _topics(b_idx, res.set_b.topics if res else []),
            "outcomes": (res.set_b.outcomes if res else []),
        },
    }
    emit(run_id, "split", {
        "seam_index": seam,
        "set_a_topics": set_plan["set_a"]["topics"],
        "set_b_topics": set_plan["set_b"]["topics"],
        "set_a_chars": len(a_text), "set_b_chars": len(b_text),
        "full_text_ok": full_ok,
    })
    return {"set_plan": set_plan}


def split_fanout(state: Dict[str, Any]) -> List[Send]:
    """Fan out one process_set per half (skips an empty half, e.g. a single-section session)."""
    base = {k: state[k] for k in ("run_id", "course", "session") if k in state}
    base["session_title"] = state.get("session_title", state["session"])
    sends = []
    for label in ("set_a", "set_b"):
        entry = state.get("set_plan", {}).get(label)
        if entry and entry.get("text", "").strip():
            sends.append(Send("process_set", {**base, "set_label": label, "set_entry": entry}))
    return sends


def process_set(state: Dict[str, Any]) -> Dict[str, Any]:
    """Plan → generate → (concept-check ↔ refine) for ONE set. Returns delta for global state."""
    run_id = state["run_id"]
    label = state["set_label"]
    entry = dict(state["set_entry"])
    set_text = entry["text"]

    # 1) PLAN — derive the key learning outcomes (count agent-decided)
    plan_prompt = fill(
        load_prompt("02_plan_outcomes"),
        set_label=label,
        set_content=set_text,
        set_topics="\n".join(f"- {t}" for t in entry.get("topics", [])) or "(none)",
        set_outcomes="\n".join(f"- {o}" for o in entry.get("outcomes", [])) or "(none)",
    )
    try:
        plan = traced(run_id, "plan", "02_plan_outcomes", plan_prompt,
                      lambda p, cfg: get_critic_llm().with_structured_output(_PlanResult).invoke(p, config=cfg))
        outcomes = [o.strip() for o in plan.outcomes if o.strip()]
    except Exception as exc:
        outcomes = entry.get("outcomes", [])
        emit(run_id, "plan", {"set": label, "warn": f"plan failed: {exc}"}, level="warn")
    if not outcomes:
        outcomes = entry.get("topics", []) or ["key_concepts"]
    entry["outcomes"] = outcomes
    emit(run_id, "plan", {"set": label, "outcomes": outcomes, "count": len(outcomes)})

    # 2) GENERATE — one MCQ per outcome
    gen_prompt = fill(
        load_prompt("03_generate_mcq"),
        reading_material=set_text,
        learning_outcomes="\n".join(f"{i+1}. {o}" for i, o in enumerate(outcomes)),
        question_count=str(len(outcomes)),
        feedback_rules=rules_block(),
    )
    # Stream the model and reveal each question the moment its `-END-` block lands.
    gen_seq = record_prompt(run_id, "generate", "03_generate_mcq", gen_prompt)
    gen_cb = make_usage_cb()
    gen_cfg = {"callbacks": [gen_cb]} if gen_cb is not None else {}
    questions: List[Question] = []
    buffer = ""
    try:
        for chunk in get_llm().stream(gen_prompt, config=gen_cfg):
            buffer += chunk.content or ""
            while "-END-" in buffer:
                block, buffer = buffer.split("-END-", 1)
                q = parse_one_block(block, label)
                if q is not None and structural_ok(q)[0]:
                    questions.append(q)
                    emit(run_id, "question", {"set": label, "question": q.model_dump()})
    except Exception as exc:  # fall back to a single shot if streaming fails
        emit(run_id, "generator", {"set": label, "warn": f"stream failed: {exc}"}, level="warn")
        raw = get_llm().invoke(gen_prompt, config=gen_cfg).content
        questions = [q for q in parse_mcq_blocks(raw, label) if structural_ok(q)[0]]
        for q in questions:
            emit(run_id, "question", {"set": label, "question": q.model_dump()})
    g_in, g_out = _sum_usage(gen_cb) if gen_cb is not None else (0, 0)
    record_result(run_id, gen_seq, f"parsed {len(questions)} questions", input_tokens=g_in, output_tokens=g_out)
    emit(run_id, "generator", {"set": label, "qcount": len(questions)})

    # 3) CONCEPT-CHECK ↔ REFINE loop (>= MIN rounds, <= MAX rounds)
    checks: Dict[str, _OneCheck] = {}
    round_no = 0
    while round_no < MAX_REFINE_ROUNDS:
        round_no += 1
        checks = _run_concept_check(run_id, label, set_text, outcomes, questions, round_no)
        not_met = [q for q in questions if not checks.get(q.qid, _OneCheck(qid=q.qid)).met]
        if not not_met and round_no >= MIN_REFINE_ROUNDS:
            break
        if round_no >= MAX_REFINE_ROUNDS:
            break
        if not_met:
            questions = _refine(run_id, label, set_text, questions, not_met, checks, round_no)

    # 4) Eligibility flags
    for q in questions:
        c = checks.get(q.qid)
        q.eligible_for_rubric = bool(c and c.met)
        q.needs_attention = not q.eligible_for_rubric

    # Stream the finished set so the UI can render its column (incl. the source text) live.
    emit(run_id, "set_done", {
        "set": label,
        "topics": entry.get("topics", []),
        "outcomes": outcomes,
        "rounds": round_no,
        "text": set_text,  # the half's reading material → collapsible source panel in the UI
        "questions": [{**q.model_dump(), "check": checks[q.qid].model_dump()}
                      for q in questions if q.qid in checks],
    })

    return {
        "questions": questions,
        "outcome_checks": {q.qid: checks[q.qid].model_dump() for q in questions if q.qid in checks},
        "iteration": {label: round_no},
        "set_plan": {label: entry},
    }


def _run_concept_check(run_id, label, set_text, outcomes, questions, round_no) -> Dict[str, _OneCheck]:
    if not questions:
        return {}
    prompt = fill(
        load_prompt("04_concept_check"),
        planned_outcomes="\n".join(f"- {o}" for o in outcomes),
        set_content=set_text,
        questions=_render_questions(questions),
    )
    try:
        result = traced(run_id, "concept_check", "04_concept_check", prompt,
                        lambda p, cfg: get_critic_llm().with_structured_output(_CheckResult).invoke(p, config=cfg))
        checks = {c.qid: c for c in result.checks}
    except Exception as exc:
        emit(run_id, "concept_check", {"set": label, "warn": f"check failed: {exc}"}, level="warn")
        checks = {q.qid: _OneCheck(qid=q.qid, met=True) for q in questions}  # fail-open, don't loop forever
    # Any question the critic didn't mention defaults to not-met (so it gets attention).
    for q in questions:
        checks.setdefault(q.qid, _OneCheck(qid=q.qid, met=False, reason="not evaluated"))
    met = sum(1 for q in questions if checks[q.qid].met)
    emit(run_id, "concept_check", {
        "set": label, "round": round_no, "met": met, "not_met": len(questions) - met,
    })
    return checks


def _refine(run_id, label, set_text, questions, not_met, checks, round_no) -> List[Question]:
    by_key = {q.question_key: q for q in questions if q.question_key}
    payload = []
    for q in not_met:
        payload.append(
            f"QUESTION_KEY: {q.question_key}\nREASON: {checks[q.qid].reason}\n"
            f"QUESTION: {q.question_text}\n{render_code_fields(q)}OPTIONS: {q.options}\nCORRECT: {q.correct_option}"
        )
    # The concept-check failure reasons ARE the problem to match feedback against (semantic/hybrid).
    fb_query = "\n".join(checks[q.qid].reason for q in not_met if checks.get(q.qid))
    prompt = fill(
        load_prompt("05_refine"),
        feedback_rules=rules_block(query=fb_query),
        set_content=set_text,
        not_met_questions="\n---\n".join(payload),
    )
    try:
        raw = traced(run_id, "refine", "05_refine", prompt,
                     lambda p, cfg: get_llm().invoke(p, config=cfg)).content
    except Exception as exc:
        emit(run_id, "refine", {"set": label, "warn": f"refine failed: {exc}"}, level="warn")
        return questions
    refined = parse_mcq_blocks(raw, label)
    fixed_keys = []
    for rq in refined:
        ok, _ = structural_ok(rq)
        base = by_key.get(rq.question_key)
        if ok and base is not None:
            rq.qid = base.qid                      # preserve identity → replace in place
            rq.covers_concept = base.covers_concept or rq.covers_concept
            by_key[rq.question_key] = rq
            fixed_keys.append(rq.question_key)
    emit(run_id, "refine", {"set": label, "round": round_no, "fixed": fixed_keys})
    # Rebuild list preserving order, swapping in refined versions.
    return [by_key.get(q.question_key, q) for q in questions]


def human_gate(state: Dict[str, Any]) -> Dict[str, Any]:
    """Auto-show the questions for accept/edit/delete. Pauses via interrupt() until resumed."""
    run_id = state["run_id"]
    questions: List[Question] = state.get("questions", [])
    checks = state.get("outcome_checks", {})

    def _q(q: Question) -> Dict[str, Any]:
        d = q.model_dump()
        d["check"] = checks.get(q.qid, {})
        return d

    if state.get("workflow") == "module_quiz":
        # Module quiz is a single merged "module" body → one flat list (like practice's pool), but it
        # still flows into the rubric + variants tail. The UI renders it as one column.
        items = [_q(q) for q in questions]
        payload = {"gate": "generation", "workflow": "module_quiz", "questions": items}
        emit(run_id, "awaiting_human", payload)
    else:
        payload = {
            "gate": "generation",
            "set_a": [_q(q) for q in questions if q.set_label == "set_a"],
            "set_b": [_q(q) for q in questions if q.set_label == "set_b"],
        }
        emit(run_id, "awaiting_human", {
            "gate": "generation",
            "set_a_count": len(payload["set_a"]), "set_b_count": len(payload["set_b"]),
        })
    decisions = interrupt(payload)  # ← pauses here; resumes with the reviewer's decisions
    decisions = decisions or []
    return {"human_decisions": {d["qid"]: d for d in decisions if d.get("qid")}, "status": "running"}


def collect_accepted(state: Dict[str, Any]) -> Dict[str, Any]:
    """Apply the generation gate's accept/edit/drop, distill generic feedback, and hand the accepted
    questions to the rubric phase (via `rubric_questions`). Does NOT park or finish — the rubric phase
    continues in the same run and `finalize` (rubric.py) does the parking + done.
    """
    run_id = state["run_id"]
    questions: List[Question] = state.get("questions", [])
    checks = state.get("outcome_checks", {})
    decisions: Dict[str, Any] = state.get("human_decisions", {})

    accepted_q: List[Question] = []
    dropped, human_reasons = [], []

    for q in questions:
        d = decisions.get(q.qid)
        action = (d or {}).get("action")
        if action == "drop":
            dropped.append(q.model_dump())
            if (d or {}).get("reason"):
                human_reasons.append(d["reason"])
            continue
        final_q = q
        # "improve" carries the accepted LLM rewrite in `edited` + the feedback that drove it.
        if action == "improve" and (d or {}).get("edited"):
            final_q = Question(**{**q.model_dump(), **d["edited"], "qid": q.qid})
            fb = (d or {}).get("feedback_text") or (d or {}).get("reason")
            if fb:
                human_reasons.append(fb)   # distilled into a generic rule below → self-evolves
        # accept (explicit, or default when no decision recorded e.g. CLI auto-accept of eligible ones)
        if action in ("accept", "improve") or (action is None and q.eligible_for_rubric):
            final_q.eligible_for_rubric = True
            accepted_q.append(final_q)

    # Generic feedback: concept-check not-met reasons + human reasons → generic one-sentence rules.
    not_met_reasons = [c.get("reason", "") for c in checks.values() if not c.get("met") and c.get("reason")]
    written = distill_and_persist(not_met_reasons, human_reasons)
    if written:
        emit(run_id, "feedback", {"rules": written})

    emit(run_id, "collected", {
        "accepted": len(accepted_q), "dropped": len(dropped), "feedback_rules": len(written),
        # The authoritative accepted set → the UI shows these live during rubric scoring (never blanks).
        "questions": [q.model_dump() for q in accepted_q],
    })
    return {
        "rubric_questions": accepted_q,
        "accepted": [q.model_dump() for q in accepted_q], "dropped": dropped,
        "feedback_written": written, "status": "running",
    }
