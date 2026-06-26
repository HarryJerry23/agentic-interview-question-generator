"""Write finalized classroom quizzes into the repo in the parent app's structured format.

Called in the FINAL phase (Feature 5 `export_finalize`), once the base questions have passed the
rubric gate and their variants have passed the variants gate. `export_set(...)` emits the
set_01/set_02 files (md + json + reading_material) with base + approved variants together, and
`write_portal_zip(...)` packages the portal JSON into the parent's uploadable zip shape.

The portal loads each upload as TWO JSON members, split by content type: `Default_new/` (standard
types) and `Code Analysis MCQs/` (the code-analysis types, in their own schema). `build_set_files`
splits accordingly; `export_set` writes both members on disk (mirroring the zip) + the MD record, and
`write_portal_zip` packages them into the uploadable zip.

Layout (mirrors gen-ai-courseware/courses/.../classroom_quiz/set_NN/):

    generated_quizzes/{course}/{session}/classroom_quiz/{set_01|set_02}/
        reading_material.md             # the half's source text
        classroom_quiz.md               # portal `-END-` blocks (with QUESTION_ID / OPTION_x_ID UUIDs)
        Default_new/{base}.json         # standard content types (MULTIPLE_CHOICE / MORE_THAN_ONE)
        Code Analysis MCQs/{base}.json  # code-analysis types (only when present)
    generated_quizzes/{course}/{session}/classroom_quiz/
        {session}_{set_NN}_classroom_quiz.zip   # portal upload: the two members above

`build_set_files` mints the UUIDs once and shares them between the MD and JSON so a question's
`QUESTION_ID` is identical in both. A re-run overwrites that session's set folders + zips.
"""
from __future__ import annotations

import json
import os
import zipfile
from typing import Any, Dict, List
from uuid import uuid4

from backend.domain.models import Question
from backend.settings import settings

_SET_DIR = {"set_a": "set_01", "set_b": "set_02"}


def _tag_names(q: Question) -> List[str]:
    """Deduped tag list from the question's metadata (parent convention)."""
    tags: List[str] = []
    for t in (q.topic, q.sub_topic, q.bloom_level, q.learning_outcome, q.question_key):
        t = (t or "").strip()
        if t and t not in tags:
            tags.append(t)
    return tags


def _correct_keys(q: Question) -> List[str]:
    return [c.strip() for c in q.correct_option.split(",") if c.strip()]


def _code_analysis_item(q: Question, qid: str, correct: List[str]) -> Dict[str, Any]:
    """One `Code Analysis MCQs` portal item (the portal's code-question schema — different from the
    standard `Default_new` shape). MC carries the answer as output/wrong_answers with the id nested in
    input_output; option-less code (TEXTUAL / FIB_CODING) carries a top-level id + the expected output."""
    code_metadata = [{
        "is_editable": False, "language": (q.code_language or "").upper(),
        "code_data": q.code, "default_code": True,
    }]
    tag_names = _tag_names(q)
    expl = {"content": q.explanation, "content_type": "MARKDOWN"}
    if q.question_type == "CODE_ANALYSIS_MULTIPLE_CHOICE":
        # correct option text(s) → output; the remaining options → wrong_answers
        output = [q.options[k] for k in sorted(q.options) if k in correct]
        wrong = [q.options[k] for k in sorted(q.options) if k not in correct]
        return {
            "question_key": q.question_key, "skills": [], "toughness": "EASY",
            "question_type": q.question_type, "explanation_for_answer": expl,
            "question_text": q.question_text, "multimedia": [],
            "content_type": q.content_type or "MARKDOWN", "tag_names": tag_names,
            "input_output": [{"input": q.code_input or "", "question_id": qid,
                              "wrong_answers": wrong, "output": output}],
            "code_metadata": code_metadata,
        }
    # CODE_ANALYSIS_TEXTUAL / FIB_CODING — option-less; the answer is the expected output.
    return {
        "question_key": q.question_key, "question_id": qid, "question_text": q.question_text,
        "multimedia": [], "skills": [], "toughness": "EASY", "reference": "",
        "question_type": q.question_type, "tag_names": tag_names,
        "content_type": q.content_type or "MARKDOWN",
        "input_output": [{"input": q.code_input or "", "output": [q.expected_output]}],
        "code_metadata": code_metadata,
        "explanation_for_answer": expl,
    }


def build_set_files(questions: List[Question], reading_text: str) -> Dict[str, Any]:
    """Return {'md': str, 'default_new': list, 'code_analysis': list} for one set, with shared
    per-question/option UUIDs. The portal loads each upload as TWO members: `Default_new` (standard
    content types) and `Code Analysis MCQs` (the code-analysis types, in their own schema). We split by
    `Question.is_code_type` (Feature 7) so each lands in the right member with the right shape. The MD
    record still lists every question in one file.
    """
    md_blocks: List[str] = []
    default_new: List[Dict[str, Any]] = []
    code_analysis: List[Dict[str, Any]] = []

    for q in questions:
        qid = str(uuid4())
        opt_ids = {k: str(uuid4()) for k in q.options}
        correct = _correct_keys(q)
        # Code items keep their own question_type; non-code multi-select becomes MORE_THAN_ONE.
        qtype = q.question_type if q.is_code_type else (
            "MORE_THAN_ONE_MULTIPLE_CHOICE" if len(correct) > 1 else (q.question_type or "MULTIPLE_CHOICE"))

        # ── Markdown block (portal `-END-` shape) — shared header, lists every question ──
        lines = [
            f"TOPIC: {q.topic}", f"SUB_TOPIC: {q.sub_topic}", f"CONCEPT: {q.concept or q.covers_concept}",
            f"QUESTION_ID: {qid}", f"QUESTION_KEY: {q.question_key}",
            f"BASE_QUESTION_KEYS: {q.base_question_keys or 'NA'}",
            f"QUESTION_TEXT: {q.question_text}", f"CONTENT_TYPE: {q.content_type or 'MARKDOWN'}",
            f"QUESTION_TYPE: {qtype}", f"LEARNING_OUTCOME: {q.learning_outcome}",
            f"CODE: {q.code or 'NA'}", f"CODE_LANGUAGE: {q.code_language or 'NA'}",
        ]
        if q.is_optionless:
            in_key, out_key = ("INPUT_1", "OUTPUT_1") if q.question_type == "FIB_CODING" else ("INPUT", "OUTPUT")
            lines += [f"{in_key}: {q.code_input}", f"{out_key}: {q.expected_output}"]
        else:
            for k in sorted(q.options):
                lines.append(f"{k}_ID: {opt_ids[k]}")
                lines.append(f"{k}: {q.options[k]}")
            lines.append(f"CORRECT_OPTION: {q.correct_option}")
        lines += [f"EXPLANATION: {q.explanation}", f"BLOOM_LEVEL: {q.bloom_level or 'UNDERSTAND'}", "-END-"]
        md_blocks.append("\n".join(lines))

        # ── JSON item → the member matching its type ──
        if q.is_code_type:
            code_analysis.append(_code_analysis_item(q, qid, correct))
        else:
            default_new.append({
                "question_id": qid, "question_key": q.question_key, "skills": [], "toughness": "EASY",
                "question_type": qtype,
                "question": {
                    "content": q.question_text, "content_type": q.content_type or "MARKDOWN",
                    "tag_names": _tag_names(q), "multimedia": [],
                },
                "options": [
                    {"content": q.options[k], "content_type": "MARKDOWN",
                     "is_correct": k in correct, "multimedia": []}
                    for k in sorted(q.options)
                ],
                "explanation_for_answer": {"content": q.explanation, "content_type": "MARKDOWN"},
            })

    return {
        "md": "\n".join(md_blocks) + ("\n" if md_blocks else ""),
        "default_new": default_new,
        "code_analysis": code_analysis,
    }


def _layout(course: str, session: str, set_label: str, workflow: str) -> tuple[str, str, str, str]:
    """(set_dir_name, out_dir, md_name, base) per workflow — the single source of truth shared by
    export_set and write_portal_zip so the on-disk files and the zip members carry the SAME base."""
    if workflow == "mcq_practice":
        set_dir_name = "mcq_practice"
        out_dir = os.path.join(settings.quizzes_dir, course, session, "mcq_practice")
        return set_dir_name, out_dir, "mcq_practice.md", f"{session}_mcq_practice"
    if workflow == "module_quiz":
        # Feature 9 — a single merged quiz under the module identity (`session` = slug(module_name)).
        set_dir_name = "module_quiz"
        out_dir = os.path.join(settings.quizzes_dir, course, session, "module_quiz")
        return set_dir_name, out_dir, "module_quiz.md", f"{session}_module_quiz"
    if workflow == "mock_interview":
        # Feature 11 — a harvested-question table under the topic identity (`session` = slug(topic_name)).
        out_dir = os.path.join(settings.quizzes_dir, course, session, "mock_interview")
        return "mock_interview", out_dir, "mock_interview.md", f"{session}_mock_interview"
    set_dir_name = _SET_DIR.get(set_label, set_label)
    out_dir = os.path.join(settings.quizzes_dir, course, session, "classroom_quiz", set_dir_name)
    return set_dir_name, out_dir, "classroom_quiz.md", f"{session}_{set_dir_name}_classroom_quiz"


def export_set(course: str, session: str, set_label: str,
               questions: List[Question], reading_text: str,
               workflow: str = "classroom_quiz") -> Dict[str, Any]:
    """Write reading_material.md + the quiz MD + the TWO portal JSON members for one set (classroom),
    the pool (practice), or the merged module — split by content type to match the portal's upload:
    `Default_new/<base>.json` (standard types) and `Code Analysis MCQs/<base>.json` (code-analysis
    types). The on-disk layout mirrors the zip members exactly; only non-empty members are written.
    Returns the built arrays so the caller hands them straight to write_portal_zip (same UUIDs).
    """
    set_dir_name, out_dir, md_name, base = _layout(course, session, set_label, workflow)
    os.makedirs(out_dir, exist_ok=True)

    files = build_set_files(questions, reading_text)
    rm_path = os.path.join(out_dir, "reading_material.md")
    md_path = os.path.join(out_dir, md_name)
    written = [rm_path, md_path]
    with open(rm_path, "w", encoding="utf-8") as f:
        f.write(reading_text or "")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(files["md"])

    # The two portal JSON members, on disk under the same relative paths used inside the zip.
    for folder, items in (("Default_new", files["default_new"]), ("Code Analysis MCQs", files["code_analysis"])):
        if not items:
            continue
        sub_dir = os.path.join(out_dir, folder)
        os.makedirs(sub_dir, exist_ok=True)
        p = os.path.join(sub_dir, f"{base}.json")
        with open(p, "w", encoding="utf-8") as f:
            json.dump(items, f, indent=2, ensure_ascii=False)
        written.append(p)

    return {
        "set": set_dir_name,
        "dir": out_dir,
        "files": written,
        "count": len(files["default_new"]) + len(files["code_analysis"]),
        # Hand the already-built arrays to write_portal_zip so the zip and the on-disk JSON share the
        # SAME question/option ids (build_set_files mints fresh uuid4s each call).
        "default_new": files["default_new"],
        "code_analysis": files["code_analysis"],
    }


def write_portal_zip(course: str, session: str, set_label: str,
                     parts: Dict[str, List[Dict[str, Any]]],
                     workflow: str = "classroom_quiz") -> Dict[str, Any]:
    """Package a set's (or the pool's / module's) portal JSON into the parent app's uploadable zip.

    The portal loads each upload as TWO members: `Default_new/<base>.json` (standard content types) and
    `Code Analysis MCQs/<base>.json` (code-analysis types, own schema). `parts` is
    `{default_new: [...], code_analysis: [...]}` from build_set_files (via export_set) — same UUIDs as
    the on-disk files. A member is written only when its array is non-empty. The zip is named per
    workflow (classroom `{session}_{set_NN}_classroom_quiz.zip`, etc.) and overwrites on re-run.
    """
    set_dir_name, set_out_dir, _md, base = _layout(course, session, set_label, workflow)
    # The zip lives in the workflow root (one level up from the classroom set_NN subdir).
    out_dir = (os.path.join(settings.quizzes_dir, course, session, "classroom_quiz")
               if workflow not in ("mcq_practice", "module_quiz") else set_out_dir)
    os.makedirs(out_dir, exist_ok=True)
    zip_path = os.path.join(out_dir, f"{base}.zip")
    members: List[str] = []
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for folder, items in (("Default_new", parts.get("default_new") or []),
                              ("Code Analysis MCQs", parts.get("code_analysis") or [])):
            if not items:
                continue
            member = f"{folder}/{base}.json"
            zf.writestr(member, json.dumps(items, indent=2, ensure_ascii=False))
            members.append(member)
    count = len(parts.get("default_new") or []) + len(parts.get("code_analysis") or [])
    return {"set": set_dir_name, "zip": zip_path, "members": members, "count": count}


def _md_cell(text: str) -> str:
    """Make a value safe inside a Markdown table cell (escape pipes, collapse newlines)."""
    return (text or "").replace("|", "\\|").replace("\n", " ").strip()


def export_interview(course: str, topic: str, rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Write the mock-interview deliverable (Feature 11): a GitHub-flavored Markdown TABLE
    (`mock_interview.md`) plus a `mock_interview.json` sidecar (raw rows, for re-load). Rows are
    ordered by `# companies` desc. Each row: question · outcome/skill · companies (linked) ·
    # companies · source links. No portal zip for this workflow — the .md is the product.
    """
    _name, out_dir, md_name, _base = _layout(course, topic, "interview", "mock_interview")
    os.makedirs(out_dir, exist_ok=True)
    ordered = sorted(rows, key=lambda r: r.get("company_count", 0), reverse=True)

    lines = [
        f"# Mock Interview — {topic}", "",
        f"_{len(ordered)} real interview questions harvested for this topic._", "",
        "| # | Interview Question | Outcome / Skill | Companies | # Companies | Source links |",
        "|---|---|---|---|---|---|",
    ]
    for i, r in enumerate(ordered, 1):
        companies = r.get("companies") or []
        comp_md = ", ".join(
            f"[{_md_cell(c.get('name',''))}]({c['url']})" if c.get("url") else _md_cell(c.get("name", ""))
            for c in companies if c.get("name")
        ) or "—"
        srcs = " · ".join(f"[src]({u})" for u in (r.get("source_urls") or [])) or "—"
        lines.append(
            f"| {i} | {_md_cell(r.get('question_text',''))} | {_md_cell(r.get('outcome',''))} "
            f"| {comp_md} | {r.get('company_count', 0)} | {srcs} |"
        )
    md = "\n".join(lines) + "\n"

    md_path = os.path.join(out_dir, md_name)
    json_path = os.path.join(out_dir, "mock_interview.json")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(ordered, f, indent=2, ensure_ascii=False)
    return {"set": "mock_interview", "dir": out_dir, "md_path": md_path,
            "json_path": json_path, "md": md, "count": len(ordered)}
