"""Understand the Session — extracts learning outcomes, maps to KPs.

Uses knowledge_graph.json first (instant, no LLM call needed).
Falls back to LLM only when session is not in the knowledge graph.
"""

from src.models import SessionContext, KPMatch, TopicMatch
from src.data_loader import DataStore
from src.llm_client import chat_completion_json
from src import memory


LLM_SYSTEM_PROMPT = """You are an expert curriculum analyst. Given a session's reading material, you must:

1. Extract 3-7 core learning outcomes (what students should know/do after this session)
2. Identify key concepts with clear scope boundaries
3. Determine session type: "theory_heavy", "code_heavy", or "mixed"
4. Map the session to the most relevant Knowledge Point IDs from the provided catalog
5. Map the session to the most relevant interview CSV topic/sub_topic values

Respond in JSON with this exact structure:
{
    "learning_outcomes": ["outcome1", "outcome2", ...],
    "key_concepts": ["concept1", "concept2", ...],
    "scope_in": ["topic in scope", ...],
    "scope_out": ["topic NOT in scope", ...],
    "session_type": "theory_heavy" | "code_heavy" | "mixed",
    "matched_kp_ids": [
        {"kp_id": "KP_GLOBAL_XXXX", "kp_label": "...", "relevance": 0.9}
    ],
    "matched_csv_topics": [
        {"topic": "TOPIC_NAME", "sub_topic": "SUB_TOPIC_OR_NULL", "confidence": 0.85}
    ]
}

Rules:
- Only match KP IDs that are DIRECTLY relevant to this session's content
- If the session has coding projects/exercises, mark as "code_heavy"
- If it's mostly conceptual/explanatory, mark as "theory_heavy"
- scope_out should list related topics NOT covered in this specific session
"""


def understand_session(session_names: list[str], data_store: DataStore) -> SessionContext:
    """Extract structured understanding of session(s).

    Each session is resolved from ITS OWN reading material (or the knowledge
    graph) and the results are merged. This keeps every selected unit's content
    fairly represented instead of concatenating them into one truncated blob —
    the key to relevant, on-topic questions for multi-session topics.

    Per-session strategy:
    1. Reading material available → LLM extracts KPs from that session's content
    2. No reading material → knowledge_graph.json (pre-computed KPs)
    3. Not in graph either → pure LLM fallback
    """
    combined_name = " + ".join(session_names)

    # Check cache
    cached = memory.get_cached_resolution(combined_name)
    if cached:
        return SessionContext(**cached)

    if len(session_names) == 1:
        context = _resolve_single(session_names[0], data_store)
    else:
        per_session = [_resolve_single(name, data_store) for name in session_names]
        context = _merge_contexts(per_session, combined_name)

    memory.cache_resolution(combined_name, context.model_dump())
    return context


def _resolve_single(name: str, data_store: DataStore) -> SessionContext:
    """Resolve one session to a SessionContext using its own content."""
    if data_store.get_session_content(name):
        # Reading material is primary: extract only KPs that are directly taught.
        return _from_llm([name], name, data_store)
    context = _from_knowledge_graph([name], name, data_store)
    if not context:
        context = _from_llm([name], name, data_store)
    return context


def _merge_contexts(contexts: list[SessionContext], combined_name: str) -> SessionContext:
    """Union the per-session contexts into one (dedup, preserve order)."""
    def _dedup(items):
        return list(dict.fromkeys(items))

    outcomes, concepts, scope_in, scope_out = [], [], [], []
    kp_by_id: dict[str, KPMatch] = {}
    csv_topics: list[TopicMatch] = []
    types = []
    for c in contexts:
        outcomes += c.learning_outcomes
        concepts += c.key_concepts
        scope_in += c.scope_in
        scope_out += c.scope_out
        csv_topics += c.matched_csv_topics
        types.append(c.session_type)
        for kp in c.matched_kp_ids:
            kp_by_id.setdefault(kp.kp_id, kp)

    if "code_heavy" in types:
        session_type = "code_heavy"
    elif types and all(t == "theory_heavy" for t in types):
        session_type = "theory_heavy"
    else:
        session_type = "mixed"

    matched_kps = list(kp_by_id.values())
    kp_ids = [kp.kp_id for kp in matched_kps]
    # merge each session's prerequisite chain plus the unioned KP set
    chain_union = _dedup([k for c in contexts for k in c.prerequisite_kp_chain] + kp_ids)

    return SessionContext(
        session_name=combined_name,
        learning_outcomes=_dedup(outcomes),
        key_concepts=_dedup(concepts),
        scope_in=_dedup(scope_in),
        scope_out=_dedup(scope_out),
        session_type=session_type,
        matched_kp_ids=matched_kps,
        matched_csv_topics=csv_topics,
        prerequisite_kp_chain=chain_union,
        difficulty_distribution={"easy": 0.3, "medium": 0.5, "hard": 0.2},
    )


def _from_knowledge_graph(
    session_names: list[str],
    combined_name: str,
    data_store: DataStore,
) -> SessionContext | None:
    """Try to build SessionContext from knowledge_graph.json data."""
    all_kp_ids = []
    all_outcomes = []
    all_concepts = []
    session_types = []

    for name in session_names:
        info = data_store.get_session_info(name)
        if not info:
            return None  # Session not in graph — need LLM

        all_kp_ids.extend(info.get("kp_ids", []))
        all_outcomes.extend(info.get("learning_outcomes", []))
        all_concepts.extend(info.get("key_concepts", []))
        session_types.append(info.get("session_type", "mixed"))

    if not all_kp_ids:
        return None  # No KP mapping — need LLM

    # Build KPMatch objects
    matched_kps = []
    for kp_id in list(dict.fromkeys(all_kp_ids)):  # deduplicate preserving order
        label = data_store.kp_catalog.get(kp_id, kp_id)
        source = data_store.kp_source_map.get(kp_id, "unknown")
        matched_kps.append(KPMatch(
            kp_id=kp_id, kp_label=label,
            relevance=0.9, source_file=source,
        ))

    # Determine session type
    if "code_heavy" in session_types:
        session_type = "code_heavy"
    elif all(t == "theory_heavy" for t in session_types):
        session_type = "theory_heavy"
    else:
        session_type = "mixed"

    # Build prerequisite chain
    prereq_chain = data_store.get_kp_ancestors(all_kp_ids)

    # If outcomes are empty, generate basic ones from KP labels
    if not all_outcomes:
        all_outcomes = [f"Understand {kp.kp_label}" for kp in matched_kps[:5]]

    # Build scope_in from KP labels
    scope_in = list(dict.fromkeys([kp.kp_label for kp in matched_kps]))

    return SessionContext(
        session_name=combined_name,
        learning_outcomes=all_outcomes,
        key_concepts=all_concepts if all_concepts else [kp.kp_label for kp in matched_kps[:5]],
        scope_in=scope_in,
        scope_out=[],
        session_type=session_type,
        matched_kp_ids=matched_kps,
        matched_csv_topics=[],
        prerequisite_kp_chain=prereq_chain,
        difficulty_distribution={"easy": 0.3, "medium": 0.5, "hard": 0.2},
    )


def _safe_topic_matches(raw: list) -> list[TopicMatch]:
    out = []
    for t in raw:
        if not isinstance(t, dict):
            continue
        try:
            out.append(TopicMatch(**t))
        except Exception:
            pass
    return out


def _from_llm(
    session_names: list[str],
    combined_name: str,
    data_store: DataStore,
) -> SessionContext:
    """Fall back to LLM-based session analysis."""
    rm_parts = []
    for name in session_names:
        content = data_store.get_session_content(name)
        if content:
            rm_parts.append(f"### {name}\n{content}")

    rm_content = "\n\n---\n\n".join(rm_parts) if rm_parts else f"Session: {combined_name}"

    kp_list = "\n".join(
        f"- {kp_id}: {kp_label}"
        for kp_id, kp_label in sorted(data_store.kp_catalog.items())
    )

    result = chat_completion_json(
        system_prompt=LLM_SYSTEM_PROMPT,
        user_prompt=f"## Session: {combined_name}\n\n## Reading Material\n{rm_content[:8000]}\n\n## KP Catalog\n{kp_list}",
        max_tokens=2048,
    )

    matched_kps = []
    for kp_data in result.get("matched_kp_ids", []):
        if not isinstance(kp_data, dict):
            continue
        try:
            kp_id = kp_data.get("kp_id", "")
            matched_kps.append(KPMatch(
                kp_id=kp_id,
                kp_label=kp_data.get("kp_label", data_store.kp_catalog.get(kp_id, "")),
                relevance=float(kp_data.get("relevance", 0.5)),
                source_file=data_store.kp_source_map.get(kp_id, "unknown"),
            ))
        except Exception:
            pass

    kp_ids = [kp.kp_id for kp in matched_kps]
    prereq_chain = data_store.get_kp_ancestors(kp_ids)

    return SessionContext(
        session_name=combined_name,
        learning_outcomes=result.get("learning_outcomes", []),
        key_concepts=result.get("key_concepts", []),
        scope_in=result.get("scope_in", []),
        scope_out=result.get("scope_out", []),
        session_type=result.get("session_type", "mixed"),
        matched_kp_ids=matched_kps,
        matched_csv_topics=_safe_topic_matches(result.get("matched_csv_topics", [])),
        prerequisite_kp_chain=prereq_chain,
        difficulty_distribution={"easy": 0.3, "medium": 0.5, "hard": 0.2},
    )
