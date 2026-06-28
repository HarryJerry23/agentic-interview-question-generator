"""Self-evolving verifier criteria (Feature 11, Part 3).

The evaluation lives in a repo `SKILL.md` (NOT a DB rubric). `load_skill_text()` returns the checks for
the prompt-22 context; `learned_rules()` parses the "## Learned rules" bullets; `append_learned_rule()`
writes a new bullet (git-versioned on disk) so a reviewer rejection sharpens the checks for the next run.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import List

# backend/agent/interview_skill.py → parents[2] = agentic-mcq-generation-workflow/ (repo root).
_SKILL = (Path(__file__).resolve().parents[2]
          / ".claude" / "skills" / "verifying-interview-evidence" / "SKILL.md")
_LEARNED_HEADER = "## Learned rules"
_BULLET = re.compile(r"^\s*[-*]\s+(.*\S)\s*$")


def skill_path() -> Path:
    return _SKILL


def load_skill_text() -> str:
    try:
        return _SKILL.read_text(encoding="utf-8")
    except Exception:
        return ""


def learned_rules() -> List[str]:
    """The bullets under '## Learned rules' (the lessons distilled from past rejections)."""
    text = load_skill_text()
    if _LEARNED_HEADER not in text:
        return []
    section = text.split(_LEARNED_HEADER, 1)[1]
    rules: List[str] = []
    for line in section.splitlines():
        if line.startswith("## "):           # stop at the next section so it never bleeds in
            break
        if line.lstrip().startswith("<!--"):
            continue
        m = _BULLET.match(line)
        if m:
            rules.append(m.group(1).strip())
    return rules


def append_learned_rule(rule: str) -> bool:
    """Append a distilled rule as a new bullet (idempotent). Returns True if written."""
    rule = " ".join((rule or "").split())
    if not rule:
        return False
    if rule.lower() in {r.lower() for r in learned_rules()}:
        return False
    text = load_skill_text()
    if not text:
        return False
    if _LEARNED_HEADER not in text:
        text = text.rstrip() + f"\n\n{_LEARNED_HEADER}\n"
    text = text.rstrip() + f"\n- {rule}\n"
    try:
        _SKILL.write_text(text, encoding="utf-8")
        return True
    except Exception:
        return False
