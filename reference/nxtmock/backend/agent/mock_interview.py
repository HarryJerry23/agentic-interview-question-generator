"""Mock Interview (Feature 11) — harvest REAL interview questions; never generate them.

The LLM only (1) names the topic's interview-relevant outcomes, (2) *selects* genuine interview
questions from candidates pulled VERBATIM by the source connectors, and (3) tags each with its
outcome. It never authors a question or invents a company.

PART 1 (this file) — walking skeleton, one source (GitHub repos), gateless / auto-publish:
    extract_outcomes → harvest → verify → export_md
Part 2 adds the rest of the connectors + the ≤3-round verify⟲research loop, cross-source
corroboration, the strict >1-source bar and embedding dedup. Part 3 adds the human review queue +
the self-evolving SKILL.md.
"""
from __future__ import annotations

import hashlib
import math
import re
from typing import Any, Dict, List

import httpx
from langgraph.types import interrupt
from pydantic import BaseModel, Field

from backend.agent.concurrency import pmap
from backend.agent.events import emit, flush_events
from backend.agent.export import export_interview
from backend.agent.interview_skill import append_learned_rule, learned_rules
from backend.agent.llm import fill, get_critic_llm, load_prompt
from backend.agent.provenance import traced
from backend.agent.sources.base import USER_AGENT, domain as _domain, enabled_connectors, is_safe_public_url
from backend.agent.sources.tavily_search import _company_from_url, search_question
from backend.memory import app_store, embed_texts, get_interview_bank, put_interview_question
from backend.settings import settings

_MAX_LIVE_CHECK_URLS = 200    # cap the link-resolve fan-out (SSRF/DoS bound, security review F2)
_MAX_RULES_PER_RUN = 5        # cap SKILL.md growth per run (security review F7)


def _one_line(text: str, limit: int = 320) -> str:
    """Collapse a candidate/snippet to a single trimmed line — defuses multi-line prompt-injection
    payloads embedded in scraped page text before it reaches prompts 21/22 (security review F3/F4)."""
    return re.sub(r"\s+", " ", (text or "")).strip()[:limit]


def _row_id(question_text: str) -> str:
    """Stable id for a queued row so gate decisions key on it (mirrors the bank key)."""
    return hashlib.sha256(" ".join((question_text or "").lower().split()).encode("utf-8")).hexdigest()[:16]

_HARVEST_BATCH = 50          # candidates per LLM filter call
_MAX_FILTER_CANDIDATES = 240  # cap LLM filtering work
_RESEARCH_GROUP_CAP = 20      # under-bar groups researched per round (bounds Tavily calls)


# ── Structured-output schemas ────────────────────────────────────────────────────

class _Outcomes(BaseModel):
    outcomes: List[str] = Field(default_factory=list)


class _HarvestItem(BaseModel):
    index: int = -1
    outcome: str = ""
    keep: bool = False


class _HarvestResult(BaseModel):
    items: List[_HarvestItem] = Field(default_factory=list)


class _Grounded(BaseModel):
    is_question: bool = True
    companies: List[str] = Field(default_factory=list)   # verbatim, only those the evidence supports


# ── Evidence-engine helpers (Part 2) — pure where possible (offline-testable) ──────

def _cosine(a: List[float], b: List[float]) -> float:
    s = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return s / (na * nb) if na and nb else 0.0


def _greedy_cluster(vectors: List[List[float]], threshold: float) -> List[List[int]]:
    """Group indices whose vectors are within `threshold` cosine of a cluster representative."""
    reps: List[int] = []
    clusters: List[List[int]] = []
    for i, v in enumerate(vectors):
        placed = False
        for ci, rep in enumerate(reps):
            if _cosine(v, vectors[rep]) >= threshold:
                clusters[ci].append(i)
                placed = True
                break
        if not placed:
            reps.append(i)
            clusters.append([i])
    return clusters


def _aggregate_group(members: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Collapse a cluster of candidate rows into one logical question + its cross-source evidence."""
    canonical = max(members, key=lambda m: len(m.get("question_text") or ""))["question_text"] or ""
    outcome = next((m.get("outcome") for m in members if m.get("outcome")), "")
    evidence = [{
        "company": m.get("company"),
        "url": m.get("source_url", ""),
        "domain": _domain(m.get("source_url", "")),
        "snippet": (m.get("raw_snippet") or m.get("question_text") or "")[:500],
    } for m in members]
    return {"question": canonical, "outcome": outcome, "evidence": evidence}


def _group_domains(group: Dict[str, Any]) -> set:
    return {e["domain"] for e in group["evidence"] if e["domain"]}


def _hint_companies(group: Dict[str, Any]) -> set:
    return {e["company"] for e in group["evidence"] if e.get("company")}


def _link_alive(url: str) -> bool:
    """Reachable (not 404/410/DNS-dead). An anti-bot 401/403/429 — and a 3xx redirect — still mean the
    page EXISTS, so they count as valid proof links. `follow_redirects=False` + the SSRF host guard keep
    a malicious redirect from reaching cloud-metadata/internal hosts (security review F1)."""
    if not is_safe_public_url(url):
        return False
    try:
        r = httpx.head(url, timeout=8, follow_redirects=False, headers={"User-Agent": USER_AGENT})
        if r.status_code in (405, 501):   # HEAD unsupported → try a light GET (still no redirect follow)
            r = httpx.get(url, timeout=10, follow_redirects=False, headers={"User-Agent": USER_AGENT})
        return r.status_code not in (404, 410)
    except Exception:
        return False


# Domains whose URL PATH *is* a specific company's interview page → the company in the URL is
# authoritative (e.g. ambitionbox.com/interviews/<company>-interview-questions). Exponent's
# /guides/<role> pages are role-centric, not company-keyed → excluded from auto-trust (they produce
# noise like "Product Manager"); any company they imply still goes through prompt-22 grounding instead.
_URL_TRUST_DOMAINS = ("ambitionbox.com", "glassdoor.com", "levels.fyi")


def _url_companies(live: List[Dict[str, Any]]) -> Dict[str, str]:
    """Companies parsed straight from COMPANY-KEYED source URLs (AmbitionBox/Glassdoor/Levels).
    Authoritative — the page IS that company's interview page, so the URL itself is the proof. Returns
    {company_name: proof_url}. This is the recall fix for conceptual questions the LLM-grounding would
    otherwise leave as "—"."""
    out: Dict[str, str] = {}
    for e in live:
        dom = e.get("domain", "")
        if dom and any(dom == d or dom.endswith("." + d) for d in _URL_TRUST_DOMAINS):
            name = _company_from_url(e.get("url", "") or "")
            if name and name not in out:
                out[name] = e["url"]
    return out


def _company_objs(names: List[str], live: List[Dict[str, Any]],
                  url_map: Dict[str, str] | None = None) -> List[Dict[str, Any]]:
    """Pair each company with a proof URL — its URL-derived proof first, else its own matching evidence."""
    url_map = url_map or {}
    out: List[Dict[str, Any]] = []
    for name in names:
        url = (url_map.get(name)
               or next((e["url"] for e in live if (e.get("company") or "").lower() == name.lower()),
                       live[0]["url"] if live else ""))
        out.append({"name": name, "url": url})
    return out


# ── Nodes ──────────────────────────────────────────────────────────────────────

_OUTCOMES_CHAR_CAP = 16000   # per-session content budget for prompt 20 (no session starves another)


def _outcomes_for_one(run_id: str, label: str, title: str, suggested: List[str], text: str) -> List[str]:
    """Run prompt 20 over ONE session's content and return its key interview outcomes (verbatim list)."""
    prompt = fill(
        load_prompt("20_interview_outcomes"),
        topic_title=title or "topic",
        suggested_outcomes="\n".join(f"- {o}" for o in suggested) or "(none)",
        content=(text or "")[:_OUTCOMES_CHAR_CAP],
    )
    try:
        res = traced(run_id, f"extract_outcomes:{label}", "20_interview_outcomes", prompt,
                     lambda p, cfg: get_critic_llm().with_structured_output(_Outcomes).invoke(p, config=cfg))
        return [o.strip() for o in res.outcomes if o.strip()]
    except Exception as exc:  # noqa: BLE001 — a failed session falls back to its suggested outcomes
        emit(run_id, "outcomes", {"warn": f"extract failed for '{label}': {exc}"}, level="warn")
        return [o.strip() for o in suggested if o.strip()]


def extract_outcomes(state: Dict[str, Any]) -> Dict[str, Any]:
    """Name the topic's interview-relevant outcomes/skills — extracted PER SELECTED SESSION, then merged.

    Every selected session contributes its own outcomes (no session is truncated away by a shared cap),
    then we union + order-preserving dedupe into one flat `interview_outcomes` list that `harvest`
    consumes. Falls back to a single merged-body pass for a single-session/edge run with no
    `module_sessions`."""
    run_id = state["run_id"]
    module_sessions = state.get("module_sessions", []) or []
    sections = state.get("sections", []) or []

    per_session: List[Dict[str, Any]] = []
    if module_sessions:
        def _do(item):
            idx, sess = item
            title = sess.get("title") or f"session {idx + 1}"
            outs = _outcomes_for_one(run_id, title, title, sess.get("outcomes", []) or [], sess.get("text", ""))
            return {"title": title, "outcomes": outs}
        per_session = pmap(_do, list(enumerate(module_sessions))) or []
    else:
        # Single-session / edge: one pass over the (already merged) body.
        text = "".join(s.get("text", "") for s in sections)
        title = state.get("session_title") or state.get("topic_name") or "topic"
        outs = _outcomes_for_one(run_id, "topic", title, state.get("course_outcomes", []) or [], text)
        per_session = [{"title": title, "outcomes": outs}]

    # Union + order-preserving dedupe across sessions.
    outcomes: List[str] = []
    seen: set = set()
    for ps in per_session:
        for o in (ps.get("outcomes") or []):
            key = o.lower()
            if key not in seen:
                seen.add(key)
                outcomes.append(o)

    if not outcomes:
        outcomes = [s["heading"] for s in sections
                    if s.get("heading") and s["heading"] != "(intro)"][:10] or ["key_concepts"]

    emit(run_id, "outcomes", {
        "outcomes": outcomes,
        "count": len(outcomes),
        "session_count": len(per_session),
        "per_session": [{"title": ps["title"], "n": len(ps.get("outcomes") or [])} for ps in per_session],
    })
    return {"interview_outcomes": outcomes, "status": "running"}


def _filter_genuine(run_id: str, candidates: List[Dict[str, Any]], outcomes: List[str]
                    ) -> List[Dict[str, Any]]:
    """Prompt 21 (batched): keep genuine, on-topic interview questions + tag each with its outcome."""
    pool = candidates[:_MAX_FILTER_CANDIDATES]
    oc_block = "\n".join(f"- {o}" for o in outcomes) or "(none)"
    chunks = [(i, pool[i:i + _HARVEST_BATCH]) for i in range(0, len(pool), _HARVEST_BATCH)]

    def _do(chunk):
        offset, batch = chunk
        listing = "\n".join(f"[{offset + i}] {_one_line(c['question_text'])}" for i, c in enumerate(batch))
        prompt = fill(load_prompt("21_interview_harvest"), outcomes=oc_block, candidates=listing)
        try:
            res = traced(run_id, "harvest_filter", "21_interview_harvest", prompt,
                         lambda p, cfg: get_critic_llm().with_structured_output(_HarvestResult).invoke(p, config=cfg))
            # Keep only kept items whose index is in THIS batch's range — guards an LLM echoing an
            # index that belongs to another concurrent batch (which would tag the wrong question).
            return [it for it in res.items if it.keep and offset <= it.index < offset + len(batch)]
        except Exception:  # noqa: BLE001 — a failed batch just drops out
            return []

    results = pmap(_do, chunks) if chunks else []
    kept: List[Dict[str, Any]] = []
    seen_idx: set = set()
    for r in (results or []):
        for it in (r or []):
            if it.index in seen_idx or not (0 <= it.index < len(pool)):
                continue
            seen_idx.add(it.index)
            c = dict(pool[it.index])
            c["outcome"] = it.outcome or c.get("outcome", "")
            kept.append(c)
    return kept


def harvest(state: Dict[str, Any]) -> Dict[str, Any]:
    """Fan out over the enabled connectors (Part 1: GitHub), pool the verbatim candidates, then keep
    only genuine on-topic interview questions (prompt 21)."""
    run_id = state["run_id"]
    outcomes = state.get("interview_outcomes", []) or []
    connectors = enabled_connectors()
    emit(run_id, "harvest", {"connectors": [c.name for c in connectors], "outcomes": len(outcomes)})

    def _run(conn):
        try:
            recs = conn.fetch(outcomes)
        except Exception:  # noqa: BLE001 — never echo the exception text (may carry an auth header/token)
            emit(run_id, "harvest", {"connector": conn.name, "warn": "connector error"}, level="warn")
            return []
        emit(run_id, "harvest", {"connector": conn.name, "found": len(recs)})
        return [{"question_text": r.question_text, "company": r.company,
                 "source_url": r.source_url, "source_type": r.source_type,
                 "raw_snippet": r.raw_snippet} for r in recs]

    batches = pmap(_run, connectors) if connectors else []
    raw = [c for b in (batches or []) for c in (b or [])]
    # Prioritize company-bearing + web (attribution) candidates ahead of the LLM-filter cap, so GitHub
    # (which carries no company) never crowds company-tagged questions out of the published table.
    raw.sort(key=lambda c: (c.get("company") is None, (c.get("source_type") or "").startswith("github")))
    emit(run_id, "harvest", {"raw_candidates": len(raw)})

    candidates = _filter_genuine(run_id, raw, outcomes)
    emit(run_id, "harvest", {"kept": len(candidates)})
    return {"interview_candidates": candidates, "status": "running"}


def _ground_group(run_id: str, group: Dict[str, Any], rules_text: str) -> _Grounded:
    """Prompt 22: confirm it's a genuine question + report ONLY the companies the evidence supports.
    `rules_text` injects the self-evolving SKILL.md learned rules (Part 3)."""
    ev = "\n".join(
        f"- {e['domain']} · {e.get('company') or '(no hint)'} · {_one_line(e['snippet'], 240)}"
        for e in group["evidence"][:8]
    ) or "(none)"
    prompt = fill(load_prompt("22_interview_verify"), question=_one_line(group["question"]),
                  evidence=ev, learned_rules=rules_text)
    try:
        return traced(run_id, "verify_grounded", "22_interview_verify", prompt,
                      lambda p, cfg: get_critic_llm().with_structured_output(_Grounded).invoke(p, config=cfg))
    except Exception:  # noqa: BLE001 — fall back to the URL-derived hints
        return _Grounded(is_question=True, companies=sorted(_hint_companies(group)))


def verify(state: Dict[str, Any]) -> Dict[str, Any]:
    """Part 2 evidence engine. Cluster candidates across sources (embeddings), corroborate, run a
    bounded ≤3-round research loop to strengthen under-bar questions, then GROUND each (prompt 22) and
    publish only those with **> min_sources independent live domains + a named, evidence-supported
    company**. Writes to the accumulating bank with embedding dedup; the table is built from the bank.
    """
    run_id = state["run_id"]
    course, topic = state["course"], state["session"]
    cands = state.get("interview_candidates", []) or []
    store = app_store()
    if not cands:
        rows = get_interview_bank(store, course, topic)
        emit(run_id, "verify", {"published_this_run": 0, "bank_total": len(rows)})
        return {"interview_rows": rows, "status": "running"}

    # 1) Embed + cluster cross-source (same question, different wording/source → one group).
    texts = [c.get("question_text", "") for c in cands]
    try:
        vecs = embed_texts(texts)
        clusters = _greedy_cluster(vecs, settings.interview_dedup_similarity)
    except Exception as exc:  # noqa: BLE001 — degrade to one-per-candidate
        emit(run_id, "verify", {"warn": f"embedding failed: {exc}"}, level="warn")
        clusters = [[i] for i in range(len(cands))]
    groups = [_aggregate_group([cands[i] for i in idxs]) for idxs in clusters]
    emit(run_id, "verify", {"candidates": len(cands), "clusters": len(groups)})

    # 2) Research loop — strengthen under-bar groups with more allowlisted attribution (needs Tavily).
    rounds = 0
    while rounds < settings.interview_research_rounds and settings.tavily_api_key:
        under = [g for g in groups
                 if len(_group_domains(g)) < settings.interview_min_sources or not _hint_companies(g)]
        if not under:
            break
        rounds += 1
        more = pmap(lambda g: search_question(g["question"]), under[:_RESEARCH_GROUP_CAP])
        added = 0
        for g, recs in zip(under[:_RESEARCH_GROUP_CAP], more or []):
            for r in (recs or []):
                d = _domain(r.source_url)
                if d and d not in _group_domains(g):
                    g["evidence"].append({"company": r.company, "url": r.source_url, "domain": d,
                                          "snippet": (r.raw_snippet or r.question_text)[:500]})
                    added += 1
        emit(run_id, "verify", {"research_round": rounds, "added": added})
        if added == 0:
            break

    # 3) Resolve every cited link once (kept = exists; anti-bot 401/403/429 still counts).
    all_urls = list({e["url"] for g in groups for e in g["evidence"] if e["url"]})[:_MAX_LIVE_CHECK_URLS]
    alive = {u for u, ok in zip(all_urls, pmap(_link_alive, all_urls) or []) if ok} if all_urls else set()

    # 4) Ground (prompt 22, with the self-evolving SKILL.md rules) every group that has a live source,
    #    then split into PUBLISH / QUEUE / DROP.
    rules_text = "\n".join(f"- {r}" for r in learned_rules()) or "(none yet)"
    live_groups = [g for g in groups if any(e["url"] in alive for e in g["evidence"])]
    grounded = pmap(lambda g: _ground_group(run_id, g, rules_text), live_groups) if live_groups else []
    gmap = {id(g): res for g, res in zip(live_groups, grounded or [])}

    published = queued = dropped = 0
    queue_rows: List[Dict[str, Any]] = []
    for g in groups:
        res = gmap.get(id(g))
        live = [e for e in g["evidence"] if e["url"] in alive]
        live_domains = {e["domain"] for e in live if e["domain"]}
        if not live or not (g["question"] or "").strip():
            dropped += 1                                   # no live source / empty text → discard
            continue
        # Companies parsed from company-tagged URLs are authoritative proof (the page IS that company's
        # interview page) — available even when grounding errored or named nothing.
        url_co = _url_companies(live)
        source_urls = list(dict.fromkeys(e["url"] for e in live))
        if res is None:
            # grounding errored (not a verdict) → don't lose a live-sourced question; send it to review,
            # but still surface any URL-derived company so the reviewer sees it.
            names = list(dict.fromkeys([*sorted(_hint_companies(g)), *url_co.keys()]))
            queue_rows.append({
                "qid": _row_id(g["question"]), "question_text": g["question"], "outcome": g["outcome"],
                "companies": _company_objs(names, live, url_co), "company_count": len(names),
                "source_urls": source_urls, "domains": sorted(live_domains),
            })
            queued += 1
            continue
        if not res.is_question:
            dropped += 1                                   # the model says it isn't a real question
            continue
        grounded = [c.strip() for c in (res.companies or []) if c and c.strip()]
        names = list(dict.fromkeys([*grounded, *url_co.keys()]))   # union: grounded + URL-authoritative
        comp_objs = _company_objs(names, live, url_co)
        # Publish if corroborated (≥min_sources domains + a company) OR a company-tagged page names it
        # directly (single strong attribution source is enough — its URL is the proof).
        if (len(live_domains) >= settings.interview_min_sources and comp_objs) or url_co:
            put_interview_question(                         # passes the bar → auto-publish
                store, course, topic, question_text=g["question"], outcome=g["outcome"],
                companies=comp_objs, source_urls=source_urls,
                status="published", run_id=run_id, dedup_threshold=settings.interview_dedup_similarity)
            published += 1
        else:                                               # real + on-topic but under-evidenced → human
            queue_rows.append({
                "qid": _row_id(g["question"]), "question_text": g["question"], "outcome": g["outcome"],
                "companies": comp_objs, "company_count": len(comp_objs), "source_urls": source_urls,
                "domains": sorted(live_domains),
            })
            queued += 1

    rows = get_interview_bank(store, course, topic)
    emit(run_id, "verify", {"published_this_run": published, "queued": queued, "dropped": dropped,
                            "bank_total": len(rows)})
    return {"interview_rows": rows, "interview_queued": queue_rows, "status": "running"}


def interview_gate(state: Dict[str, Any]) -> Dict[str, Any]:
    """Exception-only human review (Part 3): interrupt ONLY when there are under-evidenced queued rows.
    Fully-corroborated runs auto-publish in verify and skip the gate entirely (minimal intervention)."""
    run_id = state["run_id"]
    queued = state.get("interview_queued", []) or []
    if not queued:
        return {"interview_decisions": {}, "status": "running"}
    # `cards` = the under-evidenced rows to review; `published` = the already-auto-published rows (with
    # their companies) so the reviewer sees the evidenced results, not just the company-less remainder.
    payload = {"gate": "interview", "workflow": "mock_interview", "cards": queued,
               "published": state.get("interview_rows", []) or []}
    emit(run_id, "awaiting_human", payload)   # carries cards + published so the UI renders without a refetch
    decisions = interrupt(payload) or []
    return {"interview_decisions": {d["qid"]: d for d in decisions if d.get("qid")},
            "status": "running"}


def _distill_rule(run_id: str, reason: str) -> str:
    """Turn a reviewer's reject reason into ONE generic verification rule (for SKILL.md). No DB write —
    interview learning lives only in the skill file, never in the MCQ feedback namespace."""
    prompt = (
        "A reviewer rejected a harvested interview question for this reason:\n"
        f'"{reason}"\n\n'
        "Write ONE short, generic verification rule (max 20 words) that would stop us accepting such a "
        "question in future. Reply with ONLY the rule sentence.")
    try:
        out = traced(run_id, "distill_rule", "inline:distill_rule", prompt,
                     lambda p, cfg: get_critic_llm().invoke(p, config=cfg))
        return (getattr(out, "content", "") or "").strip().strip('"').strip()
    except Exception:  # noqa: BLE001
        return reason


def export_md(state: Dict[str, Any]) -> Dict[str, Any]:
    """Apply the human gate's decisions to the queued rows (approve/edit → publish; reject → distil a
    learned rule into SKILL.md), then write the mock_interview.md table from the bank and finish."""
    run_id = state["run_id"]
    course, topic = state["course"], state["session"]
    store = app_store()
    queued = state.get("interview_queued", []) or []
    decisions = state.get("interview_decisions", {}) or {}
    approved = rejected = edited = learned = 0
    for row in queued:
        d = decisions.get(row["qid"]) or {"action": "approve"}   # untouched → approve (publish)
        action = d.get("action", "approve")
        if action == "reject":
            rejected += 1
            reason = (d.get("reason") or d.get("feedback_text") or "").strip()[:500]   # bound the input
            if reason and learned < _MAX_RULES_PER_RUN:
                rule = _one_line(_distill_rule(run_id, reason), 200)
                # reject anything that could corrupt the SKILL.md "Learned rules" section structure
                if rule and "##" not in rule and "<!--" not in rule and append_learned_rule(rule):
                    learned += 1
            continue
        qtext = row["question_text"]
        new_text = (d.get("edited") or d.get("question_text") or "").strip()
        if action in ("edit", "improve") and new_text:
            qtext = new_text
            edited += 1
        put_interview_question(
            store, course, topic, question_text=qtext, outcome=row.get("outcome", ""),
            companies=row.get("companies", []), source_urls=row.get("source_urls", []),
            status="published", run_id=run_id, dedup_threshold=settings.interview_dedup_similarity)
        approved += 1

    rows = get_interview_bank(store, course, topic)
    res = export_interview(course, topic, rows)
    flush_events()
    emit(run_id, "interview_export", {"path": res["md_path"], "count": res["count"], "md": res["md"],
                                      "approved": approved, "rejected": rejected, "edited": edited,
                                      "learned_rules_added": learned})
    return {"exported": [res], "status": "done"}
