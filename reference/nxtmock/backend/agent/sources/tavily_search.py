"""Tavily search-extract connector (Feature 11, Part 2) — the breadth + attribution layer.

For each topic outcome it runs a Tavily search, keeps only results whose domain is on the
`interview_source_allowlist`, and extracts question-like lines from each result's page text. This one
connector reaches every allowlisted source (GeeksforGeeks, AmbitionBox, Glassdoor, Levels, Blind,
Reddit, the listicles, …) **legitimately via search** — no direct scraping of anti-bot sites. The
verify node corroborates across the resulting domains and (with prompt 22) confirms the company.

`search_question()` powers the verify⟲research loop: given a single confirmed question, find MORE
attribution for it. Company is best-effort from the URL here; prompt 22 is the authoritative extractor.
"""
from __future__ import annotations

import re
from typing import List, Optional
from urllib.parse import urlparse

from backend.agent.sources.base import Record, domain, looks_like_question
from backend.settings import settings

_MAX_OUTCOMES = 14
_PER_RESULT = 8
_MAX_RECORDS = 800
# Allowlist subset where the COMPANY is reliably named (in the URL or page) — used for a forced
# company-attribution search pass so even conceptual topics surface real company tags.
_ATTRIBUTION_DOMAINS = ["glassdoor.com", "ambitionbox.com", "tryexponent.com", "datalemur.com",
                        "levels.fyi", "interviewquery.com", "prepfully.com", "igotanoffer.com",
                        "teamblind.com", "leetcode.com", "prachub.com", "naukri.com",
                        "geeksforgeeks.org"]


def _client():
    from tavily import TavilyClient
    return TavilyClient(api_key=settings.tavily_api_key)


def _on_allowlist(dom: str, allow: set[str]) -> bool:
    # Empty allowlist → DENY all (never let a misconfigured/empty list silently disable the trust filter).
    return bool(allow) and any(dom == d or dom.endswith("." + d) for d in allow)


def _company_from_url(url: str) -> Optional[str]:
    """Best-effort company name from URLs that embed it (Glassdoor / AmbitionBox / Levels). Verbatim."""
    net = domain(url)
    path = urlparse(url).path
    if "glassdoor." in net:
        m = re.search(r"/Interview/([A-Za-z0-9\-]+?)-Interview-Questions", path)
        if m:
            return m.group(1).replace("-", " ").strip()
    if net.endswith("ambitionbox.com"):
        m = re.search(r"/(?:interviews|overview)/([a-z0-9\-]+?)-(?:interview-questions|interviews)", path)
        if m:
            return m.group(1).replace("-", " ").title()
    if net.endswith("levels.fyi"):
        m = re.search(r"/companies/([a-z0-9\-]+)/", path)
        if m:
            return m.group(1).replace("-", " ").title()
    if net.endswith("tryexponent.com"):     # /guides/<company>-<role>-interview
        m = re.search(r"/guides/([a-z0-9\-]+?)-(?:data|machine|software|ml|ai|product|senior|engineer)", path)
        if m:
            return m.group(1).replace("-", " ").title()
    return None


# Generic words that look like a company before "interview" but aren't one (skip these).
_NOT_COMPANY = {
    "machine", "learning", "data", "science", "deep", "generative", "ai", "ml", "llm", "nlp", "genai",
    "computer", "vision", "coding", "technical", "system", "design", "top", "common", "basic", "advanced",
    "senior", "junior", "the", "python", "sql", "java", "javascript", "react", "statistics", "probability",
    "behavioral", "hr", "software", "engineer", "engineering", "developer", "scientist", "analyst", "mock",
    "sample", "frequently", "asked", "popular", "best", "latest", "real", "fresher", "experienced", "job",
    "rag", "agent", "agentic", "interview", "questions", "answers", "guide", "preparation", "prep",
    "mle", "sde", "swe", "pm", "ds", "da", "llms", "gen", "intelligence", "artificial", "neural", "network",
    "prompt", "prompts", "prompting", "engineering",   # "Prompt Engineering interview" → NOT a company
}
# "<Company> interview" — up to 3 leading Capitalized words (e.g. "Goldman Sachs", "JP Morgan", "Amazon").
_COMPANY_BEFORE_INTERVIEW = re.compile(
    r"([A-Z][A-Za-z0-9&.\-]*(?:\s+[A-Z][A-Za-z0-9&.\-]*){0,2})\s+[Ii]nterview")


def _company_from_text(text: str) -> Optional[str]:
    """Heuristic company from a title/snippet (e.g. 'Top 50 Amazon Interview Questions' → 'Amazon',
    'Dell Data Scientist Interview' → 'Dell'). Keeps the LEADING capitalized words up to the first
    generic/role word. Permissive — prompt 22's grounded check drops anything the evidence doesn't back."""
    for m in _COMPANY_BEFORE_INTERVIEW.finditer(text or ""):
        lead = []
        for w in re.split(r"\s+", m.group(1).strip()):
            if w.lower().strip(".&-") in _NOT_COMPANY:
                break                      # stop at the first role/generic word ("Data", "Scientist", …)
            lead.append(w)
        if lead:
            return " ".join(lead)
    return None


# [label](url) — also matches a link whose closing ")" was stripped upstream ("\)?" optional).
_MD_LINK = re.compile(r"\[([^\]]+)\]\([^)]*\)?")
# Orphan link tail "](url)" left when the leading "[" was already removed (sentence split / marker strip).
_MD_DANGLING = re.compile(r"\s*\]\([^\s)]*\)?")
_MD_NOISE = re.compile(r"[`*_]+")
# Leading list/bullet markers only ("• ", "- ", "* ", "1. ", "1) ") — NOT trailing punctuation.
_LEAD_MARKER = re.compile(r"^\s*(?:[•\-*]\s*)?(?:\d+[.)]\s*)?")
# Interview-question prefixes that leak from source pages: "Q.", "Q1.", "Q12)", "Question 3:",
# "(Interview Question 1)", "Ans.", "A." — strip the marker, keep the question.
_Q_PREFIX = re.compile(
    r"^\s*(?:\(?\s*(?:interview\s+)?question\s*\d*\s*\)?[.):\-]?\s*"
    r"|q\s*\d*\s*[.):\-]\s*"
    r"|ans?\s*[.):\-]\s*)", re.IGNORECASE)


def _clean_seg(s: str) -> str:
    """Strip Markdown noise that leaks from page text (links, headings, list markers, emphasis) and any
    interview-question prefix ("Q.", "Q1.", "(Interview Question 1)", "Ans.")."""
    s = _MD_LINK.sub(r"\1", s)                 # [label](url) → label (closing paren optional)
    s = _MD_DANGLING.sub("", s)                # drop an orphan "](url)" tail
    s = _MD_NOISE.sub("", s)                   # ` * _ emphasis
    s = re.sub(r"^[#>\[\]\-•*\s]+", "", s)      # leading heading/quote/list/link markers
    s = _Q_PREFIX.sub("", s)                   # "Q.", "Q1.", "(Interview Question 1)", "Ans." prefix
    s = s.rstrip(" \t`]")
    return re.sub(r"\s+", " ", s).strip()


def _strip_trailing_company(text: str, company: Optional[str]) -> str:
    """Drop a trailing "(Company)" tag that duplicates the detected company (e.g. a prachub.com
    attribution like "Design a batch inference API for a GPU cluster (Anthropic)" → drop "(Anthropic)").
    Leaves all other parentheticals intact."""
    if not company:
        return text
    m = re.search(r"\s*\(([^)]*)\)\s*$", text)
    if m and m.group(1).strip().lower() == company.strip().lower():
        return text[:m.start()].rstrip()
    return text


def _extract_from_text(text: str) -> List[str]:
    """Question-like segments from a page's text (prose or a listicle)."""
    out: List[str] = []
    # Split on newlines first (listicles), then on sentence boundaries for prose.
    segments: List[str] = []
    for line in (text or "").splitlines():
        # Strip only LEADING list/bullet markers — keep trailing punctuation (a stripped ")" used to
        # break markdown-link cleaning and leak "](url)" tails / unclosed "(Company" into questions).
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


def _search(client, query: str, include_domains: Optional[list] = None):
    try:
        kw = dict(query=query, max_results=settings.tavily_max_results,
                  search_depth="basic", include_raw_content="markdown")
        if include_domains:
            kw["include_domains"] = include_domains
        resp = client.search(**kw)
        return resp.get("results") or []
    except Exception:
        return []


def _records_from_results(results, allow: set[str], seen: set[str]) -> List[Record]:
    out: List[Record] = []
    for r in results:
        url = r.get("url", "") or ""
        dom = domain(url)
        if not url or not _on_allowlist(dom, allow):
            continue
        text = r.get("raw_content") or r.get("content") or ""
        title = r.get("title", "") or ""
        # company hint: explicit URL pattern → page title ("Amazon Interview Questions") → snippet head.
        company = _company_from_url(url) or _company_from_text(title) or _company_from_text(text[:200])
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

    def fetch(self, outcomes: List[str]) -> List[Record]:
        if not settings.tavily_api_key:
            return []
        allow = set(settings.interview_source_allowlist or [])
        client = _client()
        records: List[Record] = []
        seen: set[str] = set()
        for outcome in (outcomes or [])[:_MAX_OUTCOMES]:
            q = outcome.replace("_", " ").strip()
            # 1) broad pass — best question coverage across the whole allowlist
            records.extend(_records_from_results(
                _search(client, f"{q} interview question asked at company"), allow, seen))
            # 2) company-attribution pass — force the company-tagged sites so real company names surface
            records.extend(_records_from_results(
                _search(client, f"{q} interview questions", include_domains=_ATTRIBUTION_DOMAINS), allow, seen))
            if len(records) >= _MAX_RECORDS:
                break
        return records[:_MAX_RECORDS]


# Company-tagged sites that, when searched ONE-AT-A-TIME for the exact question, surface the specific
# company's interview page (whose URL names the company). Searched individually because a combined
# include_domains call lets a high-volume site (GeeksforGeeks) crowd the company pages out.
_COMPANY_PROBE_DOMAINS = ["ambitionbox.com", "glassdoor.com"]


def search_question(question: str) -> List[Record]:
    """Research-loop helper: find MORE allowlisted attribution for one question. Runs a broad
    corroboration pass plus a PER-DOMAIN quoted-phrase probe of the top company-tagged sites, so the
    page that actually names the company (e.g. AmbitionBox '<Company> Interview Questions') surfaces —
    that page's URL is what gives the question its real company name (the recall fix for "—")."""
    if not settings.tavily_api_key:
        return []
    allow = set(settings.interview_source_allowlist or [])
    client = _client()
    seen: set[str] = set()
    out: List[Record] = []
    # 1) broad pass — corroboration across the whole allowlist
    out.extend(_records_from_results(_search(client, f'"{question}" interview asked at company'), allow, seen))
    # 2) per-company-site quoted-phrase probes — precise hits on the company-naming pages
    for dom in _COMPANY_PROBE_DOMAINS:
        out.extend(_records_from_results(_search(client, f'"{question}"', include_domains=[dom]), allow, seen))
    return out
