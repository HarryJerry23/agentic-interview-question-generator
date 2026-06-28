"""The memory layer — a thin wrapper over LangGraph's PostgresStore.

This is the single place the app reads/writes long-term memory. Ingestion writes here;
the future LangGraph agent reads the same store natively (`graph.compile(store=store)` →
`runtime.store.search(...)`). The store auto-manages its tables (`store.setup()`) and embeds
the indexed field on `put`, so there is no hand-rolled DDL or embedding code.

Namespaces (see the plan):
  ("content", course, session)  → one item per chunk, key = content_hash, index=["text"]
  ("outcomes", course, session) → one item, key="_", not embedded
  ("rubric",)                   → 30 checkpoints, key = checkpoint id, not embedded
  ("rubric_config",)            → per-(scope, category) min points, not embedded
"""
from __future__ import annotations

import difflib
import hashlib
import math
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Iterator

from langchain_openai import OpenAIEmbeddings
from langgraph.store.postgres import PostgresStore
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from backend.domain.rubric_seed import CATEGORY_MIN, CHECKPOINTS
from backend.settings import settings

# Generous ceiling for per-namespace listing — well above any real session's chunk count.
_LIST_LIMIT = 1000
# Ceiling for a whole course's chunks (one query powers the session list). Bump if a course
# ever exceeds this many chunks (current max ~180).
_COURSE_LIMIT = 10000

# Rubric namespaces. NOTE: PostgresStore.search() matches a prefix by *character* prefix of the
# dot-joined path (not element-wise), so ("rubric",) would also match ("rubric_config",). We keep
# the two rubric namespaces non-prefixing AND filter reads to the exact namespace (see _only).
_RUBRIC_NS = ("rubric_checkpoints",)
_RUBRIC_CFG_NS = ("rubric_config",)


def _only(items, namespace: tuple[str, ...]):
    """Keep only items whose namespace matches exactly.

    Guards against PostgresStore's character-prefix search leaking sibling namespaces whose
    name shares a leading substring (e.g. `mastering_image_generation` vs
    `mastering_image_generation_with_stable_diffusion`).
    """
    return [it for it in items if tuple(it.namespace) == namespace]


def _build_embeddings() -> OpenAIEmbeddings:
    """OpenAI-compatible embeddings (OpenRouter serves text-embedding-3-small at /v1).

    `check_embedding_ctx_length=False` makes the client send raw strings instead of
    pre-tokenized arrays, which is what non-OpenAI-compatible proxies expect.
    """
    return OpenAIEmbeddings(
        model=settings.embedding_model,
        base_url=settings.embedding_base_url,
        api_key=settings.embedding_api_key,
        check_embedding_ctx_length=False,
    )


# Shared Neon-resilient pool settings. One place for the knobs that keep a long-lived pool healthy on
# Neon: `check_connection` replaces a connection Neon dropped while idle (otherwise the pool hands out
# a dead conn → "SSL connection has been closed unexpectedly"); `max_idle` recycles before Neon's idle
# cutoff; `open=True` opens eagerly (psycopg_pool 3.2+ deprecates the implicit open and will default it
# to False). The store/checkpointer pools need dict_row + prepare_threshold=0; callers can override.
_POOL_KWARGS = {"autocommit": True, "prepare_threshold": 0, "row_factory": dict_row}


def make_neon_pool(
    dsn: str, *, min_size: int = 1, max_size: int = 4, kwargs: dict[str, Any] | None = None
) -> ConnectionPool:
    """A Neon-resilient ConnectionPool with the shared health-check + eager-open settings (Feature 5.3)."""
    return ConnectionPool(
        dsn, min_size=min_size, max_size=max_size,
        kwargs=dict(_POOL_KWARGS) if kwargs is None else kwargs,
        check=ConnectionPool.check_connection, max_idle=120, reconnect_timeout=10, open=True,
    )


@contextmanager
def open_store() -> Iterator[PostgresStore]:
    """Open the PostgresStore with semantic indexing enabled and ensure its schema."""
    index = {"embed": _build_embeddings(), "dims": settings.embedding_dims}
    with PostgresStore.from_conn_string(settings.postgres_store_dsn, index=index) as store:
        store.setup()  # idempotent: creates store tables + pgvector extension
        yield store


_APP_STORE_CM = None  # kept alive so the underlying pool isn't garbage-collected/closed
_APP_STORE: PostgresStore | None = None


def app_store() -> PostgresStore:
    """A long-lived store for the web app: opened + set up once, reused across requests.

    Unlike `open_store()` (a context manager for CLI runs), this keeps one `PostgresStore`
    alive for the process, backed by a small connection pool (thread-safe, auto-reconnect).
    We retain the context-manager object in a module global so it is not GC'd (which would
    close the pool). Read endpoints and no-embed uploads make no LLM calls.
    """
    global _APP_STORE, _APP_STORE_CM
    if _APP_STORE is None:
        index = {"embed": _build_embeddings(), "dims": settings.embedding_dims}
        pool = make_neon_pool(settings.postgres_store_dsn)
        _APP_STORE_CM = pool   # retain so the pool isn't GC'd/closed
        _APP_STORE = PostgresStore(pool, index=index)
        _APP_STORE.setup()
    return _APP_STORE


# ── Content ──────────────────────────────────────────────────────────────────

def content_key(course: str, session: str, text: str) -> str:
    """Deterministic key for a chunk → re-ingesting identical text is a no-op."""
    return hashlib.sha256(f"{course}|{session}|{text}".encode("utf-8")).hexdigest()


def put_chunk(
    store: PostgresStore,
    course: str,
    session: str,
    *,
    text: str,
    chunk_index: int,
    heading_path: str,
    token_count: int,
    session_title: str,
    module: str,
    embed: bool = True,
) -> bool:
    """Store one chunk (idempotent). Returns True if written, False if it already existed.

    The False path skips the embedding call, so re-ingestion is cheap. `embed=False` stores the
    chunk without a vector (`index=False`) — instant, used by browser uploads; the chunk is still
    loadable via `get_session`, just not semantically searchable until embedded later.
    """
    key = content_key(course, session, text)
    if store.get(("content", course, session), key) is not None:
        return False
    store.put(
        ("content", course, session),
        key,
        {
            "text": text,
            "chunk_index": chunk_index,
            "heading_path": heading_path,
            "token_count": token_count,
            "session_title": session_title,
            "module": module,
        },
        index=["text"] if embed else False,
    )
    return True


def get_session(store: PostgresStore, course: str, session: str) -> list[dict[str, Any]]:
    """All chunks for a session, ordered by chunk_index (what a quiz run loads)."""
    target = ("content", course, session)
    items = _only(store.search(target, limit=_LIST_LIMIT), target)
    return sorted((it.value for it in items), key=lambda v: v.get("chunk_index", 0))


def _retry_once(fn):
    """Run `fn`; on a connection-level error retry exactly once. The pool's `check_connection` has
    by then replaced the dead Neon connection, so the second attempt succeeds. (Feature 5.3)"""
    import psycopg
    try:
        return fn()
    except (psycopg.OperationalError, psycopg.InterfaceError):
        return fn()


def list_courses(store: PostgresStore) -> list[str]:
    def _q():
        namespaces = store.list_namespaces(prefix=("content",), max_depth=2)
        return sorted({ns[1] for ns in namespaces if len(ns) >= 2 and ns[0] == "content"})
    return _retry_once(_q)


def list_sessions(store: PostgresStore, course: str) -> list[dict[str, Any]]:
    """Sessions for a course → powers the course→session dropdown.

    ONE light store query over the small ("outcomes", course) namespace (one tiny item per
    session: title + module), instead of scanning every chunk's full text. The original
    per-session loop did ~2N remote round-trips (~45s); a content scan pulled ~180 full-text
    chunks (~3s); this reads ~N small rows (sub-second).
    """
    def _q():
        prefix = ("outcomes", course)
        rows: list[dict[str, Any]] = []
        for it in store.search(prefix, limit=_COURSE_LIMIT):
            ns = tuple(it.namespace)
            if len(ns) != 3 or ns[0] != "outcomes" or ns[1] != course:
                continue  # guard against char-prefix matching a sibling course
            value = it.value or {}
            rows.append({
                "session": ns[2],
                "session_title": value.get("session_title") or ns[2],
                "module": value.get("module", ""),
            })
        return sorted(rows, key=lambda r: r["session"])
    return _retry_once(_q)


# ── Source (full original Markdown, for the content viewer) ─────────────────────

def put_source(
    store: PostgresStore,
    course: str,
    session: str,
    *,
    text: str,
    session_title: str,
    module: str,
) -> None:
    """Store the session's full original Markdown (one item, not embedded)."""
    store.put(
        ("source", course, session),
        "_",
        {"text": text, "session_title": session_title, "module": module},
        index=False,
    )


def get_source(store: PostgresStore, course: str, session: str) -> dict[str, Any] | None:
    """The full reading material for the viewer: source text + the session's outcomes header.

    Returns None if the session has no stored source.
    """
    src = store.get(("source", course, session), "_")
    if src is None:
        return None
    oc = store.get(("outcomes", course, session), "_")
    meta = oc.value if oc else {}
    return {
        "session_title": src.value.get("session_title") or meta.get("session_title", session),
        "module": src.value.get("module") or meta.get("module", ""),
        "outcomes": meta.get("outcomes", []),
        "text": src.value.get("text", ""),
    }


# ── Outcomes ───────────────────────────────────────────────────────────────────

def put_outcomes(
    store: PostgresStore,
    course: str,
    session: str,
    *,
    session_title: str,
    module: str,
    outcomes: list[str],
    confidence: str,
) -> None:
    store.put(
        ("outcomes", course, session),
        "_",
        {
            "session_title": session_title,
            "module": module,
            "outcomes": outcomes,
            "confidence": confidence,
        },
        index=False,  # outcomes are not semantically searched
    )


# ── Rubric ─────────────────────────────────────────────────────────────────────

def seed_rubric_if_empty(store: PostgresStore) -> int:
    """Seed the 30 checkpoints + per-category minimums on first boot. Idempotent.

    Returns the number of checkpoints seeded (0 if the rubric already existed).
    """
    if _only(store.search(_RUBRIC_NS, limit=_LIST_LIMIT), _RUBRIC_NS):
        return 0
    for cp in CHECKPOINTS:
        store.put(_RUBRIC_NS, cp.id, cp.model_dump(), index=False)
    for scope, categories in CATEGORY_MIN.items():
        for category, min_points in categories.items():
            store.put(
                _RUBRIC_CFG_NS,
                f"{scope}:{category}",
                {"scope": scope, "category": category, "min_points": min_points},
                index=False,
            )
    return len(CHECKPOINTS)


def ensure_rubric_checkpoints(store: PostgresStore) -> int:
    """Idempotently insert any seed checkpoint missing from memory; returns how many were added.

    Non-destructive: existing rows (which may carry a promoted/refined `met_when`) are left untouched.
    This backfills new checkpoints — e.g. the Feature 7 `6.x` code checkpoints — into a store that was
    already seeded with the original 30, so promotion/self-evolving keeps working on them too.
    """
    existing = {it.key for it in _only(store.search(_RUBRIC_NS, limit=_LIST_LIMIT), _RUBRIC_NS)}
    added = 0
    for cp in CHECKPOINTS:
        if cp.id not in existing:
            store.put(_RUBRIC_NS, cp.id, cp.model_dump(), index=False)
            added += 1
    return added


def load_rubric(store: PostgresStore) -> dict[str, list[dict[str, Any]]]:
    checkpoints = _only(store.search(_RUBRIC_NS, limit=_LIST_LIMIT), _RUBRIC_NS)
    config = _only(store.search(_RUBRIC_CFG_NS, limit=_LIST_LIMIT), _RUBRIC_CFG_NS)
    return {
        "checkpoints": sorted((it.value for it in checkpoints), key=lambda v: v.get("id", "")),
        "config": [it.value for it in config],
    }


# ── Feedback rules (generic, sentence-wise — Feature 3; scalable retrieval) ──────
# A single flat namespace of generalizable authoring rules learned from failures. The store
# holds ONLY the generic rule text (never questions, never session facts). Each rule is one
# "lesson to self" about a quality dimension (answer validity, distractor quality, clarity, …).
#
# Two layers keep this scalable AND non-destructive (nothing is ever deleted):
#   • Write (evolve-in-place): an exact repeat bumps `hit_count`; a *paraphrase* of an existing
#     lesson (semantic match) bumps that lesson and records the new wording in `aliases` — so the
#     lesson strengthens instead of spawning a near-duplicate row.
#   • Read (relevance): in semantic/hybrid mode rules are selected by similarity to the *problem
#     at hand* (a failure reason / category / reviewer note), blended with proven frequency —
#     not just globally-top-by-hit_count.
# Rows folded into a canonical carry `superseded_by` and are skipped at read time (still stored).
_FEEDBACK_NS = ("feedback",)


def _norm(text: str) -> str:
    return " ".join((text or "").lower().split())


def _rule_key(rule: str) -> str:
    return hashlib.sha256(_norm(rule).encode("utf-8")).hexdigest()


def _active(items):
    """Drop rows folded into a canonical (`superseded_by` set) — kept in the DB, never injected."""
    return [it for it in items if not it.value.get("superseded_by")]


def _semantic_match(store: PostgresStore, rule: str, category: str):
    """Best existing rule semantically ~identical to `rule` in the same category, else None.

    Embeds `rule` as the search query (one embedding call) — call only in semantic/hybrid mode.
    Returns `(key, value_copy)` of a match whose similarity ≥ `feedback_dedup_similarity`.

    Pulls a wider window than 1 so same-category paraphrases aren't missed when the very nearest
    hits happen to sit in other categories (we filter by category below).
    """
    hits = _active(_only(store.search(_FEEDBACK_NS, query=rule, limit=20), _FEEDBACK_NS))
    for it in hits:
        if (it.value.get("category") or "") != (category or ""):
            continue  # never merge across rubric categories
        if (it.score or 0.0) >= settings.feedback_dedup_similarity:
            return it.key, dict(it.value)
    return None


def _bump(store: PostgresStore, key: str, v: dict, category: str, checkpoint_ref: str, *, alias: str | None) -> int:
    """Strengthen an existing rule in place: +1 hit, backfill category/ref, record a paraphrase.

    In semantic/hybrid mode we re-embed (`index=["rule"]`) so a rule first stored in frequency mode
    still gets a vector once a later bump happens under semantic mode (re-embedding the unchanged
    text is idempotent — same vector — and cheap). In frequency mode there are no vectors, so we
    keep `index=False`.
    """
    v["hit_count"] = int(v.get("hit_count", 1)) + 1
    if category and not v.get("category"):
        v["category"] = category
    if checkpoint_ref and not v.get("checkpoint_ref"):
        v["checkpoint_ref"] = checkpoint_ref
    if alias:
        aliases = list(v.get("aliases") or [])
        if alias not in aliases and alias != v.get("rule"):
            aliases.append(alias)
            # Keep the MOST RECENT `cap` paraphrases (drop oldest), so a full list still records new wordings.
            v["aliases"] = aliases[-settings.feedback_alias_cap:]
    embed = settings.feedback_retrieval_mode != "frequency"
    store.put(_FEEDBACK_NS, key, v, index=["rule"] if embed else False)
    return v["hit_count"]


def put_feedback_rule(
    store: PostgresStore, rule: str, *, source: str = "", category: str = "", checkpoint_ref: str = ""
) -> int:
    """Store/refresh one generic rule; returns its current `hit_count` (0 if blank).

    Exact repeat → bump. In semantic/hybrid mode a *paraphrase* of an existing lesson (cosine ≥
    `feedback_dedup_similarity`, same category) evolves that lesson in place (bump + alias) rather
    than inserting a near-duplicate. A genuinely new lesson is stored embedded so future paraphrases
    can find it. Feature 4 tags rules with the rubric `category`/`checkpoint_ref`; generation rules
    leave those blank. Nothing is ever deleted.
    """
    rule = rule.strip()
    if not rule:
        return 0
    key = _rule_key(rule)
    existing = store.get(_FEEDBACK_NS, key)
    if existing is not None:
        return _bump(store, key, dict(existing.value), category, checkpoint_ref, alias=None)
    # No exact match — try to evolve a semantically-identical lesson in place (semantic/hybrid only).
    if settings.feedback_retrieval_mode != "frequency":
        try:
            match = _semantic_match(store, rule, category)
        except Exception:
            match = None  # embedding endpoint hiccup → fall through to a plain insert
        if match is not None:
            mkey, mval = match
            return _bump(store, mkey, mval, category, checkpoint_ref, alias=rule)
    # First time we've seen this lesson. Embed it (semantic/hybrid) so paraphrases can match later.
    embed = settings.feedback_retrieval_mode != "frequency"
    store.put(
        _FEEDBACK_NS, key,
        {"rule": rule, "hit_count": 1, "source": source, "category": category,
         "checkpoint_ref": checkpoint_ref, "aliases": []},
        index=["rule"] if embed else False,
    )
    return 1


def top_feedback_rules(store: PostgresStore, k: int = 8, *, category: str | None = None) -> list[str]:
    """The top-k rule sentences by hit_count → the `"frequency"` selection (and the safe fallback).

    `category` (Feature 4) restricts to rules learned for one rubric category. Superseded rows are
    skipped. This is the deterministic, embedding-free path used when retrieval mode is "frequency"
    or whenever semantic retrieval errors out.
    """
    items = _active(_only(store.search(_FEEDBACK_NS, limit=_LIST_LIMIT), _FEEDBACK_NS))
    if category:
        items = [it for it in items if it.value.get("category") == category]
    ranked = sorted(items, key=lambda it: it.value.get("hit_count", 1), reverse=True)
    return [it.value.get("rule", "") for it in ranked[:k] if it.value.get("rule")]


def _recency(updated_at: Any, half_life_days: int) -> float:
    """0..1 freshness from `updated_at` with exponential decay; 0.5 at one half-life old."""
    if not isinstance(updated_at, datetime) or half_life_days <= 0:
        return 0.0
    now = datetime.now(timezone.utc)
    ts = updated_at if updated_at.tzinfo else updated_at.replace(tzinfo=timezone.utc)
    age_days = max(0.0, (now - ts).total_seconds() / 86400.0)
    return math.exp(-age_days / half_life_days)


def _hybrid_rank(items, k: int):
    """Re-rank vector-search hits by relevance + proven frequency + (optional) recency.

    final = w_sem*similarity + w_freq*log-normalized-hits + w_rec*recency.
    Frequency is log-dampened so a very high hit_count can't bury a highly-relevant newer rule.
    """
    if not items:
        return []
    max_hits = max(int(it.value.get("hit_count", 1)) for it in items) or 1
    w_sem, w_freq, w_rec = (
        settings.feedback_weight_semantic, settings.feedback_weight_frequency, settings.feedback_weight_recency,
    )

    def score(it):
        sim = float(it.score or 0.0)
        freq = math.log1p(int(it.value.get("hit_count", 1))) / math.log1p(max_hits)
        rec = _recency(getattr(it, "updated_at", None), settings.feedback_recency_half_life_days)
        return w_sem * sim + w_freq * freq + w_rec * rec

    return sorted(items, key=score, reverse=True)[:k]


def _dedup_results(rules: list[str]) -> list[str]:
    """Lightweight lexical safety-net: drop a rule too similar to one already kept.

    The strong, semantic de-duplication happens at write time (`put_feedback_rule`) and via
    `fold_duplicate_rules`; this only stops obvious near-identical wordings from filling the
    injected list when older un-folded duplicates still exist. No embedding calls.
    """
    kept: list[str] = []
    for r in rules:
        rn = _norm(r)
        if any(difflib.SequenceMatcher(None, rn, _norm(k)).ratio() >= 0.85 for k in kept):
            continue
        kept.append(r)
    return kept


def relevant_feedback_rules(
    store: PostgresStore, query: str, *, k: int | None = None, category: str | None = None
) -> list[str]:
    """Rules most relevant to the *problem at hand* (semantic/hybrid), with a frequency fallback.

    `query` describes the current problem/dimension (a failure reason, rubric category, reviewer
    note) — NOT the session topic. Blank query or `feedback_retrieval_mode == "frequency"` →
    delegate to `top_feedback_rules`. On any embedding/transport error we also fall back, so a run
    never breaks.
    """
    k = k or settings.feedback_semantic_k
    if not (query or "").strip() or settings.feedback_retrieval_mode == "frequency":
        return top_feedback_rules(store, k=k, category=category)
    try:
        items = _active(_only(
            store.search(_FEEDBACK_NS, query=query, limit=settings.feedback_candidate_limit), _FEEDBACK_NS
        ))
        if category:
            items = [it for it in items if it.value.get("category") == category]
            # The similarity window may not contain any rule of this category → don't silently
            # return nothing; fall back to that category's frequency-ranked rules.
            if not items:
                return top_feedback_rules(store, k=k, category=category)
        ranked = _hybrid_rank(items, k)
        rules = [it.value.get("rule", "") for it in ranked if it.value.get("rule")]
        return _dedup_results(rules)
    except Exception:
        return top_feedback_rules(store, k=k, category=category)


def list_feedback_rules(store: PostgresStore) -> list[dict[str, Any]]:
    """All active (non-superseded) feedback rules with full metadata, ranked by hit_count.

    Powers the read-only "what the system learned" UI (`/api/feedback-rules`). Unlike
    `top_feedback_rules` (rule strings only) this returns rule + hit_count + source + category +
    checkpoint_ref + aliases so the UI can show how each lesson was reinforced.
    """
    items = _active(_only(store.search(_FEEDBACK_NS, limit=_LIST_LIMIT), _FEEDBACK_NS))
    rows = [{
        "rule": it.value.get("rule", ""),
        "hit_count": int(it.value.get("hit_count", 1)),
        "source": it.value.get("source", ""),
        "category": it.value.get("category", ""),
        "checkpoint_ref": it.value.get("checkpoint_ref", ""),
        "aliases": list(it.value.get("aliases") or []),
    } for it in items if it.value.get("rule")]
    return sorted(rows, key=lambda r: r["hit_count"], reverse=True)


# ── Feedback maintenance (non-destructive) — backfill embeddings + fold duplicates ──

def backfill_feedback_embeddings(store: PostgresStore, *, dry_run: bool = False) -> dict[str, int]:
    """Re-put every feedback rule with `index=["rule"]` so it gets a vector (idempotent).

    Existing rules written in "frequency" mode have no embedding and are invisible to semantic
    search until embedded. Re-putting preserves the value verbatim (same key) and only adds/refreshes
    the vector — no data loss. Per-item errors are counted, not raised, so a flaky embedding endpoint
    yields a partial (still-correct) backfill.
    """
    items = _only(store.search(_FEEDBACK_NS, limit=_LIST_LIMIT), _FEEDBACK_NS)
    stats = {"scanned": 0, "reembedded": 0, "skipped": 0, "errors": 0}
    for it in items:
        stats["scanned"] += 1
        rule = (it.value or {}).get("rule", "")
        if not rule:
            stats["skipped"] += 1
            continue
        if dry_run:
            stats["reembedded"] += 1
            continue
        try:
            store.put(_FEEDBACK_NS, it.key, dict(it.value), index=["rule"])
            stats["reembedded"] += 1
        except Exception:
            stats["errors"] += 1
    return stats


def fold_duplicate_rules(
    store: PostgresStore, *, dry_run: bool = False, category: str | None = None
) -> dict[str, Any]:
    """Non-destructively merge existing paraphrase-duplicates within each category.

    For each cluster of rules with pairwise cosine ≥ `feedback_dedup_similarity`, pick the canonical
    (highest hit_count), set its `hit_count = sum`, append the others' text to its `aliases`, and mark
    the others `superseded_by=<canonical key>`. Superseded rows STAY in the store (skipped at read);
    nothing is deleted. Idempotent: an already-folded set yields no clusters.
    """
    items = _active(_only(store.search(_FEEDBACK_NS, limit=_LIST_LIMIT), _FEEDBACK_NS))
    if category is not None:
        items = [it for it in items if (it.value.get("category") or "") == category]
    by_key = {it.key: it for it in items}

    # Union-find over near-duplicate pairs (within the same category).
    parent = {k: k for k in by_key}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for it in items:
        rule = it.value.get("rule", "")
        if not rule:
            continue
        # Wide window so a large cluster of mutual near-duplicates fully unions (no partial folds).
        for hit in _active(_only(store.search(_FEEDBACK_NS, query=rule, limit=settings.feedback_candidate_limit), _FEEDBACK_NS)):
            if hit.key == it.key or hit.key not in by_key:
                continue
            if (hit.value.get("category") or "") != (it.value.get("category") or ""):
                continue
            if (hit.score or 0.0) >= settings.feedback_dedup_similarity:
                union(it.key, hit.key)

    clusters: dict[str, list[str]] = {}
    for k in by_key:
        clusters.setdefault(find(k), []).append(k)

    folds, folded_rows = [], 0
    for member_keys in clusters.values():
        if len(member_keys) < 2:
            continue
        members = [by_key[k] for k in member_keys]
        canonical = max(members, key=lambda it: int(it.value.get("hit_count", 1)))
        others = [it for it in members if it.key != canonical.key]
        cval = dict(canonical.value)
        cval["hit_count"] = sum(int(it.value.get("hit_count", 1)) for it in members)
        aliases = list(cval.get("aliases") or [])
        for o in others:
            for txt in [o.value.get("rule", "")] + list(o.value.get("aliases") or []):
                if txt and txt != cval.get("rule") and txt not in aliases:
                    aliases.append(txt)
        cval["aliases"] = aliases[: settings.feedback_alias_cap]
        folds.append({"canonical": cval.get("rule", ""), "merged": [o.value.get("rule", "") for o in others],
                      "hit_count": cval["hit_count"]})
        folded_rows += len(others)
        if dry_run:
            continue
        store.put(_FEEDBACK_NS, canonical.key, cval, index=["rule"])
        for o in others:
            ov = dict(o.value)
            ov["superseded_by"] = canonical.key
            store.put(_FEEDBACK_NS, o.key, ov, index=False)
    return {"clusters_folded": len(folds), "rows_superseded": folded_rows, "dry_run": dry_run, "folds": folds}


def promote_checkpoint_from_feedback(
    store: PostgresStore, checkpoint_ref: str, guidance: str
) -> str | None:
    """Auto-refine a rubric checkpoint from recurring rejection feedback (Feature 4).

    Appends `guidance` to the referenced checkpoint's `met_when` (the rule the critic applies), so the
    rubric *learns* — staying within the checkpoint's own category. Returns the checkpoint id refined,
    or None if the ref is unknown. Idempotent on identical guidance (won't append the same sentence twice).
    """
    if not checkpoint_ref or not guidance.strip():
        return None
    item = store.get(_RUBRIC_NS, checkpoint_ref)
    if item is None:
        return None
    cp = dict(item.value)
    guidance = guidance.strip()
    if guidance.lower() in cp.get("met_when", "").lower():
        return checkpoint_ref  # already folded in
    cp["met_when"] = f"{cp.get('met_when', '').rstrip()} Also: {guidance}".strip()
    store.put(_RUBRIC_NS, checkpoint_ref, cp, index=False)
    return checkpoint_ref


# ── Per-run real cost (Feature 5.2) — accumulated OpenRouter usage diff across the run's segments ──

def put_run_cost(store: PostgresStore, run_id: str, value: dict[str, Any]) -> None:
    store.put(("run_cost", run_id), "_", value, index=False)


def get_run_cost(store: PostgresStore, run_id: str) -> dict[str, Any] | None:
    it = store.get(("run_cost", run_id), "_")
    return dict(it.value) if it is not None else None


# ── Interview bank (Feature 11) — accumulating store of REAL, evidenced interview questions ──
# Namespace ("interview_bank", course, topic_slug); key = hash of the normalized question, so the
# SAME question across sources/runs merges (companies + source links accrue, count grows) instead of
# duplicating. Part 1 dedups on exact-normalized text (index=False); Part 2 adds embedding dedup.

def _interview_key(question_text: str) -> str:
    return hashlib.sha256(" ".join(question_text.lower().split()).encode("utf-8")).hexdigest()


_EMB_SINGLETON: OpenAIEmbeddings | None = None


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts with the shared model (cross-source clustering in the verify engine)."""
    global _EMB_SINGLETON
    if _EMB_SINGLETON is None:
        _EMB_SINGLETON = _build_embeddings()
    return _EMB_SINGLETON.embed_documents(list(texts))


def put_interview_question(
    store: PostgresStore, course: str, topic: str, *,
    question_text: str, outcome: str = "",
    companies: list[dict[str, Any]] | None = None,
    source_urls: list[str] | None = None,
    status: str = "published", run_id: str = "",
    dedup_threshold: float | None = None,
) -> bool:
    """Upsert one harvested question into the topic's bank. Returns True if newly inserted, False if it
    merged into an existing row (companies de-duped by name, source_urls unioned, count recomputed).

    Exact-normalized text merges by key. When `dedup_threshold` is given (Part 2), a NEW question also
    semantic-searches the bank and merges into a near-duplicate (cosine ≥ threshold) so "Explain RAG"
    and "What is retrieval-augmented generation?" become one row whose company_count accrues.
    """
    if not (question_text or "").strip():
        return False                       # never bank a blank question (would render an empty md row)
    ns = ("interview_bank", course, topic)
    key = _interview_key(question_text)
    now = datetime.now(timezone.utc).isoformat()
    companies = [c for c in (companies or []) if c.get("name")]
    source_urls = list(dict.fromkeys(source_urls or []))
    existing = store.get(ns, key)
    if existing is None and dedup_threshold is not None:
        try:   # semantic near-duplicate → merge into that row instead of inserting a twin
            hits = _only(store.search(ns, query=question_text, limit=3), ns)
            best = max((h for h in hits if getattr(h, "score", None) is not None),
                       key=lambda h: h.score, default=None)
            if best is not None and best.score is not None and best.score >= dedup_threshold:
                key = best.key
                existing = store.get(ns, key)
        except Exception:
            pass
    if existing is not None:
        v = dict(existing.value)
        by_name = {c["name"]: c for c in v.get("companies", []) if c.get("name")}
        for c in companies:
            by_name.setdefault(c["name"], c)
        urls = list(dict.fromkeys((v.get("source_urls") or []) + source_urls))
        rids = list(dict.fromkeys((v.get("run_ids") or []) + ([run_id] if run_id else [])))
        v.update({"companies": list(by_name.values()), "company_count": len(by_name),
                  "source_urls": urls, "last_seen": now, "run_ids": rids})
        if not v.get("outcome") and outcome:
            v["outcome"] = outcome
        store.put(ns, key, v, index=["question_text"])
        return False
    store.put(ns, key, {
        "question_text": question_text, "outcome": outcome,
        "companies": companies, "company_count": len(companies),
        "source_urls": source_urls, "status": status,
        "first_seen": now, "last_seen": now,
        "run_ids": [run_id] if run_id else [],
    }, index=["question_text"])
    return True


def get_interview_bank(store: PostgresStore, course: str, topic: str) -> list[dict[str, Any]]:
    """All banked questions for a topic (ordered by company_count desc, then recency)."""
    ns = ("interview_bank", course, topic)
    items = _only(store.search(ns, limit=_LIST_LIMIT), ns)
    rows = [it.value for it in items]
    return sorted(rows, key=lambda r: (r.get("company_count", 0), r.get("last_seen", "")), reverse=True)
