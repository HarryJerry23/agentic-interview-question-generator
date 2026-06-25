"""GitHub-repos connector — license-clean backbone source for real interview questions.

Pulls configured `INTERVIEW_GITHUB_REPOS` via the GitHub REST API + raw files and extracts
question-like lines (headings / list items / "what|why|how…" / lines ending in "?") from Markdown.
These repos are topic-organized (not per-question company-tagged), so `company` is left None here.
File blob URLs serve as proof links. Adapted from nxtmock New_AddOn_files/github_repo.py.
"""
from __future__ import annotations

import re
from typing import List, Set

from src.sources.base import Record, looks_like_question, polite_get
from src import config

_API = "https://api.github.com"
_RAW = "https://raw.githubusercontent.com"
_MAX_FILES_PER_REPO = 15
_MAX_CANDIDATES = 600
_SKIP = ("license", "contributing", "code_of_conduct", "changelog", "security", "node_modules")

_REPO_RE = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+")
_PATH_RE = re.compile(r"[A-Za-z0-9_./\-]+\.md")
_HEADING = re.compile(r"^#{1,6}\s+(.*)$")
_LISTITEM = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+(.*)$")
_LINK = re.compile(r"\[([^\]]+)\]\([^)]+\)")
_MD_NOISE = re.compile(r"[*_`>#]+")
_ENUM = re.compile(r"^\s*\d+[.)]\s+")


def _headers() -> dict:
    h = {"Accept": "application/vnd.github+json"}
    if config.GITHUB_TOKEN:
        h["Authorization"] = f"Bearer {config.GITHUB_TOKEN}"
    return h


def _clean(text: str) -> str:
    t = _LINK.sub(r"\1", text)
    t = _MD_NOISE.sub("", t)
    t = _ENUM.sub("", t)
    t = re.sub(r"\s+", " ", t)
    return t.strip(" .:-\t")


def _outcome_tokens(outcomes: List[str]) -> Set[str]:
    toks: Set[str] = set()
    for o in outcomes:
        for w in re.split(r"[^a-z0-9]+", (o or "").lower()):
            if len(w) >= 4:
                toks.add(w)
    return toks


def _relevant(q: str, toks: Set[str]) -> bool:
    if not toks:
        return True
    ql = q.lower()
    return any(w in ql for w in toks)


def _extract_questions(md: str) -> List[str]:
    out: List[str] = []
    in_fence = False
    for line in md.splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        m = _HEADING.match(line) or _LISTITEM.match(line)
        if not m:
            continue
        cand = _clean(m.group(1))
        if cand and looks_like_question(cand):
            out.append(cand)
    return out


class GithubRepoConnector:
    """Reads INTERVIEW_GITHUB_REPOS → candidate questions. Network errors degrade gracefully."""
    name = "github"

    def fetch(self, outcomes: List[str]) -> List[Record]:
        toks = _outcome_tokens(outcomes)
        records: List[Record] = []
        seen: Set[str] = set()
        for repo in config.INTERVIEW_GITHUB_REPOS:
            if not _REPO_RE.fullmatch(repo or ""):
                continue
            try:
                records.extend(self._fetch_repo(repo, toks, seen))
            except Exception:
                continue
            if len(records) >= _MAX_CANDIDATES:
                break
        return records[:_MAX_CANDIDATES]

    def _fetch_repo(self, repo: str, toks: Set[str], seen: Set[str]) -> List[Record]:
        meta = polite_get(f"{_API}/repos/{repo}", headers=_headers())
        if meta is None or meta.status_code != 200:
            return []
        branch = (meta.json() or {}).get("default_branch", "main")
        tree = polite_get(f"{_API}/repos/{repo}/git/trees/{branch}?recursive=1", headers=_headers())
        if tree is None or tree.status_code != 200:
            return []
        paths = [n["path"] for n in (tree.json() or {}).get("tree", [])
                 if n.get("type") == "blob" and n["path"].lower().endswith(".md")
                 and _PATH_RE.fullmatch(n["path"])
                 and not any(s in n["path"].lower() for s in _SKIP)]
        paths.sort(key=lambda p: (0 if "readme" in p.lower() else 1, p))
        out: List[Record] = []
        for path in paths[:_MAX_FILES_PER_REPO]:
            raw = polite_get(f"{_RAW}/{repo}/{branch}/{path}")
            if raw is None or raw.status_code != 200:
                continue
            file_url = f"https://github.com/{repo}/blob/{branch}/{path}"
            for q in _extract_questions(raw.text):
                if not _relevant(q, toks):
                    continue
                key = " ".join(q.lower().split())
                if key in seen:
                    continue
                seen.add(key)
                out.append(Record(question_text=q, source_url=file_url, company=None,
                                  raw_snippet=q, source_type=f"github:{repo}"))
        return out
