"""Connector contract + registry + a shared polite HTTP getter (Feature 11).

A connector turns one legitimate source into candidate interview questions. Every connector returns
the SAME normalized `Record`; the harvest node fans out over `enabled_connectors()` (per the
per-source `.env` flags) and pools the results. Connectors must extract **verbatim** — never invent a
company name — and always attach the exact `source_url` the text came from.
"""
from __future__ import annotations

import ipaddress
import socket
import time
from dataclasses import dataclass
from typing import List, Optional, Protocol, runtime_checkable
from urllib.parse import urlparse

import httpx

from backend.settings import settings

_PRIVATE_NETS = [ipaddress.ip_network(n) for n in (
    "10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16", "169.254.0.0/16",
    "127.0.0.0/8", "0.0.0.0/8", "::1/128", "fc00::/7", "fe80::/10")]


def domain(url: str) -> str:
    """Registrable host of a URL, lower-cased, without a leading www. (shared by every connector)."""
    net = (urlparse(url or "").netloc or "").lower()
    return net[4:] if net.startswith("www.") else net


def is_safe_public_url(url: str) -> bool:
    """SSRF guard: http(s) only + the host must resolve to a PUBLIC IP — blocks cloud-metadata
    (169.254.169.254), localhost, and RFC-1918 ranges reachable from a harvested/redirected URL."""
    p = urlparse(url or "")
    if p.scheme not in ("http", "https") or not p.hostname:
        return False
    try:
        for fam, _, _, _, sockaddr in socket.getaddrinfo(p.hostname, None):
            ip = ipaddress.ip_address(sockaddr[0])
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
                return False
        return True
    except Exception:
        return False

# A descriptive, contactable UA — good web citizenship for the polite-fetch connectors.
USER_AGENT = ("nxtwave-mock-interview-bot/1.0 "
              "(+https://www.ccbp.in; gen-ai-content@nxtwave.co.in)")


@dataclass
class Record:
    """One harvested candidate, exactly as found on the source (no inference)."""
    question_text: str
    source_url: str
    company: Optional[str] = None
    raw_snippet: str = ""
    source_type: str = ""          # e.g. "github:owner/repo", "tavily:glassdoor.com"


@runtime_checkable
class Connector(Protocol):
    name: str
    def fetch(self, outcomes: List[str]) -> List[Record]: ...


_Q_STARTS = ("what", "why", "how", "when", "where", "explain", "describe", "compare", "define",
             "implement", "write", "design", "difference between", "list ", "name ", "can you",
             "walk me through", "tell me", "given ", "suppose")


def looks_like_question(t: str) -> bool:
    """Cheap shared test: is this string a plausible interview question/task? (Used by every connector
    so the harvest LLM only sees genuine candidates.)"""
    t = (t or "").strip()
    if not (15 <= len(t) <= 320):
        return False
    if t.endswith("?"):
        return True
    return t.lower().startswith(_Q_STARTS)


def polite_get(url: str, *, headers: Optional[dict] = None,
               timeout: float = 20.0, retries: int = 2) -> Optional[httpx.Response]:
    """GET with a descriptive UA, redirects, and a small backoff on 403/429/network errors.

    Returns the last response (even non-200) or None if every attempt raised. Callers check
    `.status_code`. Used by the GitHub connector (Part 1) and the polite scrapers (Part 2).
    """
    if not is_safe_public_url(url):     # SSRF guard — never fetch private/metadata/loopback hosts
        return None
    h = {"User-Agent": USER_AGENT}
    if headers:
        h.update(headers)
    last: Optional[httpx.Response] = None
    for attempt in range(retries + 1):
        try:
            r = httpx.get(url, headers=h, timeout=timeout, follow_redirects=True)
            if r.status_code == 200:
                return r
            last = r
            # Retry only genuinely transient statuses. NOT 403 — for the unauthenticated GitHub API a
            # 403 is the rate-limit/permission verdict; retrying just burns the remaining 60/hr quota.
            if r.status_code in (429, 500, 502, 503):
                time.sleep(1.0 + attempt)
                continue
            return r
        except httpx.HTTPError:
            time.sleep(0.5 + attempt)
    return last


def enabled_connectors() -> List[Connector]:
    """The connectors switched on in settings. Part 1: GitHub only. Part 2 appends the Tavily
    search-extract connector + the polite scrapers (GeeksforGeeks, Reddit, AmbitionBox) behind their
    own flags."""
    out: List[Connector] = []
    if settings.interview_src_github_enabled:
        from backend.agent.sources.github_repo import GithubRepoConnector
        out.append(GithubRepoConnector())
    # Tavily is the breadth + attribution layer: it searches the whole interview_source_allowlist
    # (GeeksforGeeks, AmbitionBox, Glassdoor, Levels, Blind, Reddit, the listicles, …) legitimately via
    # search — no direct scraping of anti-bot sites. Needs a key; off if blank.
    if settings.interview_src_tavily_enabled and settings.tavily_api_key:
        from backend.agent.sources.tavily_search import TavilyConnector
        out.append(TavilyConnector())
    return out
