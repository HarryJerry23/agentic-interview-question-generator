"""Tavily search connector — breadth + attribution layer for real interview questions.

For each topic outcome it runs a Tavily search, keeps only results whose domain is on
INTERVIEW_SOURCE_ALLOWLIST, and extracts question-like lines from each result's page text.
This single connector reaches every allowlisted source (Glassdoor, AmbitionBox, GeeksforGeeks,
Levels, Blind, Reddit, etc.) legitimately via search — no direct scraping of anti-bot sites.

`search_question()` powers an optional research loop: given a confirmed question, find more
attribution for it. Company attribution is best-effort here; validate_relevance confirms fitness.

Adapted from nxtmock New_AddOn_files/tavily_search.py.
"""
from __future__ import annotations

import re
from typing import List, Optional
from urllib.parse import urlparse

from src.sources.base import Record, domain, looks_like_question
from src import config

_MAX_OUTCOMES = 14
_PER_RESULT = 8
_MAX_RECORDS = 800
_ATTRIBUTION_DOMAINS = ["glassdoor.com", "ambitionbox.com", "tryexponent.com", "datalemur.com",
                        "levels.fyi", "interviewquery.com", "prepfully.com", "igotanoffer.com",
                        "teamblind.com", "leetcode.com"]
_BROAD_DOMAINS = [
    "glassdoor.com", "ambitionbox.com", "tryexponent.com", "datalemur.com",
    "levels.fyi", "interviewquery.com", "prepfully.com", "igotanoffer.com",
    "teamblind.com", "leetcode.com",
    "reddit.com", "stackoverflow.com", "github.com", "medium.com", "dev.to",
    "geeksforgeeks.org", "quora.com", "hackerrank.com",
]


def _client():
    from tavily import TavilyClient
    return TavilyClient(api_key=config.TAVILY_API_KEY)


def _on_allowlist(dom: str, allow: set) -> bool:
    return bool(allow) and any(dom == d or dom.endswith("." + d) for d in allow)


def _company_from_url(url: str) -> Optional[str]:
    """Best-effort company name from URLs that embed it (Glassdoor, AmbitionBox, Levels, etc.)."""
    from urllib.parse import parse_qs
    net = domain(url)
    parsed = urlparse(url)
    path = parsed.path
    if "glassdoor." in net:
        m = re.search(r"/Interview/([A-Za-z0-9\-]+?)-Interview-Questions", path)
        if m:
            return m.group(1).replace("-", " ").title()
    if net.endswith("ambitionbox.com"):
        m = re.search(r"/(?:interviews|overview)/([a-z0-9\-]+?)-(?:interview-questions|interviews)", path)
        if m:
            return m.group(1).replace("-", " ").title()
    if net.endswith("levels.fyi"):
        m = re.search(r"/companies/([a-z0-9\-]+)/", path)
        if m:
            return m.group(1).replace("-", " ").title()
    if net.endswith("tryexponent.com"):
        # Try role-specific page first: /guides/<company>-<role>
        m = re.search(r"/guides/([a-z0-9\-]+?)-(?:data|machine|software|ml|ai|product|senior|engineer|backend|frontend|fullstack|devops|cloud)", path)
        if m:
            return m.group(1).replace("-", " ").title()
        # Broader fallback: /guides/<company>/ or /guides/<company>-interview
        m = re.search(r"/guides/([a-z0-9][a-z0-9\-]*?)(?:/|-interview)", path)
        if m:
            slug = m.group(1)
            if slug not in {"data", "machine", "software", "ml", "ai", "interview"}:
                return slug.replace("-", " ").title()
    if net.endswith("interviewquery.com"):
        params = parse_qs(parsed.query)
        company = params.get("company", [None])[0]
        if company:
            return company.replace("-", " ").title()
    if net.endswith("datalemur.com"):
        m = re.search(r"/(?:sql-interview-questions|interview-questions)/([a-z0-9\-]+?)-[a-z]", path)
        if m:
            return m.group(1).replace("-", " ").title()
    return None


_NOT_COMPANY = {
    "machine", "learning", "data", "science", "deep", "generative", "ai", "ml", "llm", "nlp", "genai",
    "computer", "vision", "coding", "technical", "system", "design", "top", "common", "basic", "advanced",
    "senior", "junior", "the", "python", "sql", "java", "javascript", "react", "statistics", "probability",
    "behavioral", "hr", "software", "engineer", "engineering", "developer", "scientist", "analyst", "mock",
    "sample", "frequently", "asked", "popular", "best", "latest", "real", "fresher", "experienced", "job",
    "rag", "agent", "agentic", "interview", "questions", "answers", "guide", "preparation", "prep",
    "mle", "sde", "swe", "pm", "ds", "da", "llms", "gen", "intelligence", "artificial", "neural", "network",
    "prompt", "prompts", "prompting", "engineering",
    # generic roles / seniority levels — NOT companies (Glassdoor listing pages embed these)
    "manager", "lead", "associate", "consultant", "specialist", "architect", "intern",
    "trainee", "executive", "officer", "head", "director", "principal", "staff", "vp",
    "l1", "l2", "l3", "fullstack", "backend", "frontend", "devops", "cloud", "qa",
    "tester", "support", "graduate", "entry", "level", "role", "position",
    # page UI / navigation noise that precedes the word "interview" on web pages
    "share", "save", "saved", "apply", "follow", "following", "jobs", "job", "salary",
    "salaries", "reviews", "review", "photos", "benefits", "home", "login", "log",
    "sign", "menu", "search", "posted", "read", "more", "view", "see", "all", "your",
    "company", "companies", "overview", "about", "contact", "help", "blog", "news",
}


def _valid_company(name: Optional[str]) -> Optional[str]:
    """Return the name only if it looks like a real company — i.e. not made up
    purely of generic/role words. Otherwise None, so callers fall back to an
    honest source label instead of a misleading 'Manager'/'L1'."""
    if not name:
        return None
    tokens = [t for t in re.split(r"\s+", name.strip()) if t]
    if not tokens:
        return None
    if all(t.lower().strip(".&-") in _NOT_COMPANY for t in tokens):
        return None
    return name
_COMPANY_BEFORE_INTERVIEW = re.compile(
    r"([A-Z][A-Za-z0-9&.\-]*(?:\s+[A-Z][A-Za-z0-9&.\-]*){0,2})\s+[Ii]nterview")


def _company_from_text(text: str) -> Optional[str]:
    for m in _COMPANY_BEFORE_INTERVIEW.finditer(text or ""):
        lead = []
        for w in re.split(r"\s+", m.group(1).strip()):
            if w.lower().strip(".&-") in _NOT_COMPANY:
                break
            lead.append(w)
        if lead:
            return " ".join(lead)
    return None


_MD_LINK = re.compile(r"\[([^\]]+)\]\([^)]*\)?")
_MD_DANGLING = re.compile(r"\s*\]\([^\s)]*\)?")
_MD_NOISE = re.compile(r"[`*_]+")
# Strips leading list/question markers: bullets, "1.", "1)", "Q1.", "Q1)", "Q1:",
# "Question 1.", "Question 1:" — so question content never starts with a number/label.
_LEAD_MARKER = re.compile(r"^\s*(?:[•\-*]\s*)?(?:(?:q(?:uestion)?\s*)?\d+\s*[.):]\s*)?", re.IGNORECASE)


def _clean_seg(s: str) -> str:
    s = _MD_LINK.sub(r"\1", s)
    s = _MD_DANGLING.sub("", s)
    s = _MD_NOISE.sub("", s)
    s = re.sub(r"^[#>\[\]\-•*\s]+", "", s)
    s = _LEAD_MARKER.sub("", s)  # drop any leading Q1./1)/Question 2: prefix
    s = s.rstrip(" \t`]")
    return re.sub(r"\s+", " ", s).strip()


def _strip_trailing_company(text: str, company: Optional[str]) -> str:
    if not company:
        return text
    m = re.search(r"\s*\(([^)]*)\)\s*$", text)
    if m and m.group(1).strip().lower() == company.strip().lower():
        return text[:m.start()].rstrip()
    return text


def _extract_from_text(text: str) -> List[str]:
    out: List[str] = []
    segments: List[str] = []
    for line in (text or "").splitlines():
        line = _LEAD_MARKER.sub("", line).strip()
        if not line:
            continue
        segments.append(line)
        segments.extend(s.strip() for s in re.split(r"(?<=[.?!])\s+", line) if s.strip())
    seen = set()
    for seg in segments:
        seg = _clean_seg(seg)
        if looks_like_question(seg) and seg.lower() not in seen:
            seen.add(seg.lower())
            out.append(seg)
            if len(out) >= _PER_RESULT:
                break
    return out


def _summarize_tavily_error(errors: list) -> str:
    """Turn raw Tavily exception strings into one human-readable status."""
    joined = " ".join(errors).lower()
    if "usage limit" in joined or "exceeds your plan" in joined or "forbidden" in joined:
        return "Tavily quota/usage limit reached — web search unavailable (upgrade or replace TAVILY_API_KEY)."
    if "unauthorized" in joined or "401" in joined or "invalid api key" in joined:
        return "Tavily API key invalid or unauthorized — web search unavailable."
    if "rate limit" in joined or "429" in joined:
        return "Tavily rate limit hit — web search temporarily unavailable."
    return f"Tavily web search failed: {errors[0]}"


def _search(client, query: str, include_domains: Optional[list] = None,
            errors: Optional[list] = None):
    try:
        kw = dict(query=query, max_results=config.TAVILY_MAX_RESULTS,
                  search_depth="basic", include_raw_content="markdown")
        if include_domains:
            kw["include_domains"] = include_domains
        resp = client.search(**kw)
        return resp.get("results") or []
    except Exception as e:
        # Don't swallow silently — record so callers can surface WHY web search
        # returned nothing (e.g. expired key, quota/usage limit, rate limit).
        msg = f"{type(e).__name__}: {e}"
        print(f"[tavily] search failed for {query!r}: {msg}")
        if errors is not None:
            errors.append(msg)
        return []


def _records_from_results(results, allow: set, seen: set) -> List[Record]:
    out: List[Record] = []
    for r in results:
        url = r.get("url", "") or ""
        dom = domain(url)
        if not url or not _on_allowlist(dom, allow):
            continue
        text = r.get("raw_content") or r.get("content") or ""
        title = r.get("title", "") or ""
        company = _valid_company(
            _company_from_url(url) or _company_from_text(title) or _company_from_text(text[:200])
        )
        for cand in _extract_from_text(text):
            cand = _strip_trailing_company(cand, company)
            key = " ".join(cand.lower().split())
            if key in seen:
                continue
            seen.add(key)
            out.append(Record(question_text=cand, source_url=url, company=company,
                              raw_snippet=(text or "")[:700], source_type=f"tavily:{dom}"))
    return out


class TavilyConnector:
    name = "tavily"

    def fetch(self, outcomes: List[str]) -> tuple:
        """Return (records, search_call_count, error).

        error is None on success, or a short string describing why searches
        failed (e.g. quota/usage limit) so callers can surface it instead of
        silently looking like 'no results found'.
        """
        if not config.TAVILY_API_KEY:
            return [], 0, "TAVILY_API_KEY not set"
        allow = set(config.INTERVIEW_SOURCE_ALLOWLIST or [])
        client = _client()
        records: List[Record] = []
        seen: set = set()
        errors: list = []
        search_count = 0
        for outcome in (outcomes or [])[:_MAX_OUTCOMES]:
            q = outcome.replace("_", " ").strip()
            # Pass 1 (broad — community + attribution): catch forum/community questions
            records.extend(_records_from_results(
                _search(client, f"{q} interview question asked at company",
                        include_domains=_BROAD_DOMAINS, errors=errors), allow, seen))
            search_count += 1
            # Pass 2 (attribution — company-keyed sites only)
            records.extend(_records_from_results(
                _search(client, f"{q} interview questions",
                        include_domains=_ATTRIBUTION_DOMAINS, errors=errors), allow, seen))
            search_count += 1
            if len(records) >= _MAX_RECORDS:
                break
            # All searches erroring (e.g. quota exceeded) — stop early, don't burn calls
            if errors and not records and search_count >= 2:
                break
        error = None
        if not records and errors:
            error = _summarize_tavily_error(errors)
        return records[:_MAX_RECORDS], search_count, error


def search_question(question: str) -> List[Record]:
    """Research loop helper: find more allowlisted attribution for one confirmed question."""
    if not config.TAVILY_API_KEY:
        return []
    allow = set(config.INTERVIEW_SOURCE_ALLOWLIST or [])
    results = _search(_client(), f'"{question}" interview asked at company')
    return _records_from_results(results, allow, set())
