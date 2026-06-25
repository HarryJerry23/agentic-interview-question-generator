"""Shared contract + utilities for live question-harvesting connectors (tools 12 & 13).

Each connector returns normalized `Record` objects — verbatim questions as found on the source,
never invented. Adapted from nxtmock/backend/agent/sources/base.py; uses `requests` (already in
requirements) instead of httpx.
"""
from __future__ import annotations

import ipaddress
import socket
import time
from dataclasses import dataclass
from typing import List, Optional, Protocol, runtime_checkable
from urllib.parse import urlparse

import requests

_PRIVATE_NETS = [ipaddress.ip_network(n) for n in (
    "10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16", "169.254.0.0/16",
    "127.0.0.0/8", "0.0.0.0/8", "::1/128", "fc00::/7", "fe80::/10")]


def domain(url: str) -> str:
    """Registrable host of a URL, lower-cased, without a leading www."""
    net = (urlparse(url or "").netloc or "").lower()
    return net[4:] if net.startswith("www.") else net


def is_safe_public_url(url: str) -> bool:
    """SSRF guard: http(s) only + host must resolve to a public IP."""
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


USER_AGENT = ("nxtwave-interview-bot/1.0 "
              "(+https://www.ccbp.in; gen-ai-content@nxtwave.co.in)")


@dataclass
class Record:
    """One harvested candidate, exactly as found on the source (no inference)."""
    question_text: str
    source_url: str
    company: Optional[str] = None
    raw_snippet: str = ""
    source_type: str = ""  # e.g. "github:owner/repo", "tavily:glassdoor.com"


@runtime_checkable
class Connector(Protocol):
    name: str
    def fetch(self, outcomes: List[str]) -> List[Record]: ...


_Q_STARTS = ("what", "why", "how", "when", "where", "explain", "describe", "compare", "define",
             "implement", "write", "design", "difference between", "list ", "name ", "can you",
             "walk me through", "tell me", "given ", "suppose")


def looks_like_question(t: str) -> bool:
    """True if the string is a plausible interview question or task prompt."""
    t = (t or "").strip()
    if not (15 <= len(t) <= 320):
        return False
    if t.endswith("?"):
        return True
    return t.lower().startswith(_Q_STARTS)


def polite_get(url: str, *, headers: Optional[dict] = None,
               timeout: float = 20.0, retries: int = 2) -> Optional[requests.Response]:
    """GET with descriptive UA, redirects, and backoff on transient errors.

    Returns the last response (even non-200) or None if every attempt raised.
    Anti-bot 401/403/429 responses are returned as-is (callers treat them as 'exists').
    """
    if not is_safe_public_url(url):
        return None
    h = {"User-Agent": USER_AGENT}
    if headers:
        h.update(headers)
    last: Optional[requests.Response] = None
    for attempt in range(retries + 1):
        try:
            r = requests.get(url, headers=h, timeout=timeout, allow_redirects=True)
            if r.status_code == 200:
                return r
            last = r
            if r.status_code in (429, 500, 502, 503):
                time.sleep(1.0 + attempt)
                continue
            return r
        except requests.RequestException:
            time.sleep(0.5 + attempt)
    return last
