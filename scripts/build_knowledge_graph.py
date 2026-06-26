"""Rebuild data/knowledge_graph.json from course_structure + curriculum files.

Sources:
  data/course_structure.json                             — authoritative 22 topics / 52 sessions
  data/knowledge_graph.json                              — existing KP-level data + session-KP mapping
  data/curriculum/gen_ai_final.json                      — Gen AI KP labels
  data/curriculum/llm_applications_kp_links_final_fixed.json  — LLM Apps KP labels
  data/curriculum/flask_kp_links_final.json              — Flask KP labels

Run: python3 scripts/build_knowledge_graph.py
Output: data/knowledge_graph.json (overwritten)
"""

import json
import re
from pathlib import Path
from difflib import SequenceMatcher
from collections import defaultdict

ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"
CURRICULUM_DIR = DATA_DIR / "curriculum"


# ─── Helpers ─────────────────────────────────────────────────────────────────

def load_json(path):
    with open(path) as f:
        return json.load(f)


def normalize_name(s):
    """Lowercase, strip Part N markers, collapse whitespace for fuzzy matching."""
    s = s.lower()
    s = re.sub(r'[|,()\-]+', ' ', s)
    s = re.sub(r'\bpart\s*\d+\b', '', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s


def name_similarity(a, b):
    return SequenceMatcher(None, normalize_name(a), normalize_name(b)).ratio()


# ─── Load sources ─────────────────────────────────────────────────────────────

print("Loading sources...")
course_structure = load_json(DATA_DIR / "course_structure.json")
existing_kg      = load_json(DATA_DIR / "knowledge_graph.json")

existing_kps      = existing_kg.get("knowledge_points", {})
existing_sessions = existing_kg.get("sessions", {})
existing_edges    = existing_kg.get("prerequisite_edges", [])

print(f"  Existing KG: {len(existing_kps)} KPs, {len(existing_sessions)} sessions, {len(existing_edges)} edges")

# ─── Build full KP registry (existing + curriculum) ──────────────────────────

all_kps = {k: dict(v) for k, v in existing_kps.items()}  # deep copy

curriculum_files = [
    (CURRICULUM_DIR / "gen_ai_final.json",                          "gen_ai"),
    (CURRICULUM_DIR / "llm_applications_kp_links_final_fixed.json", "llm_apps"),
    (CURRICULUM_DIR / "flask_kp_links_final.json",                  "flask"),
]

new_kp_count = 0
for fpath, course in curriculum_files:
    data = load_json(fpath)
    for link in data.get("question_kp_links", []):
        kp_id    = link.get("resolved_kp_id")  or link.get("kp_id")
        kp_label = link.get("resolved_kp_label") or link.get("kp_label")
        if kp_id and kp_label and kp_id not in all_kps:
            all_kps[kp_id] = {
                "label": kp_label,
                "course": course,
                "prerequisites": [],
                "dependents": [],
            }
            new_kp_count += 1

print(f"  Total KPs after curriculum merge: {len(all_kps)} (+{new_kp_count} new)")

# ─── KP keyword index for session matching ───────────────────────────────────

# Build inverted index: word → [kp_id]
kp_word_index = defaultdict(list)
STOP_WORDS = {'the','a','an','to','for','in','of','with','and','or','is','as',
              'at','by','from','on','this','that','using','use','its','their'}

for kp_id, kp_data in all_kps.items():
    label = kp_data.get("label", "")
    words = set(re.sub(r'[^\w]', ' ', label.lower()).split()) - STOP_WORDS
    for w in words:
        kp_word_index[w].append(kp_id)


def find_kps_for_session(session_name, topic, n_max=6):
    """Keyword match session name + topic against KP labels."""
    search_text = session_name + " " + topic
    words = set(re.sub(r'[^\w]', ' ', search_text.lower()).split()) - STOP_WORDS - {
        'introduction', 'building', 'part', '1', '2', 'your', 'ai', 'llm',
        'getting', 'started', 'advanced', 'mastering', 'understanding', 'how',
        'works', 'running', 'locally'
    }

    score_map = defaultdict(int)
    for w in words:
        # Give more weight to longer, more specific words
        weight = max(1, len(w) - 4)
        for kp_id in kp_word_index.get(w, []):
            score_map[kp_id] += weight

    ranked = sorted(score_map.items(), key=lambda x: -x[1])
    return [kp_id for kp_id, _ in ranked[:n_max]]


# ─── Session name matching: CS → existing KG ─────────────────────────────────

print("\nMatching course_structure sessions to existing KG sessions...")

# All CS sessions flat
all_cs_sessions = [(topic, s) for topic, sessions in course_structure.items() for s in sessions]

cs_to_kg_map = {}  # cs_name → kg_name (or None)
for topic, cs_name in all_cs_sessions:
    best_kg, best_score = None, 0
    for kg_name in existing_sessions:
        score = name_similarity(cs_name, kg_name)
        if score > best_score:
            best_kg, best_score = kg_name, score

    if best_score >= 0.75:
        cs_to_kg_map[cs_name] = best_kg
        print(f"  MATCH {best_score:.2f}: '{cs_name}'  →  '{best_kg}'")
    else:
        cs_to_kg_map[cs_name] = None
        print(f"  NEW  (best={best_score:.2f}): '{cs_name}'")

matched = sum(1 for v in cs_to_kg_map.values() if v)
print(f"\n  Matched: {matched}/{len(all_cs_sessions)},  New: {len(all_cs_sessions)-matched}")


# ─── Session type heuristics ──────────────────────────────────────────────────

CODE_SIGNALS    = ['build', 'implement', 'deploy', 'integrat', 'creat', 'develop',
                   'fine-tun', 'automat', 'workflow', 'step-by-step', 'coding',
                   'rest api', 'flask', 'deploying', 'running']
THEORY_SIGNALS  = ['introduction', 'understanding', 'overview', 'explore', 'insight',
                   'concept', 'fundamentals', 'principles', 'in the real world',
                   'journey', 'kaggle', 'setting up your', 'productivity', 'enhancing',
                   'mastering', 'how llms work', 'evaluation']

def infer_session_type(session_name, topic):
    n = (session_name + " " + topic).lower()
    code_hits   = sum(1 for s in CODE_SIGNALS  if s in n)
    theory_hits = sum(1 for s in THEORY_SIGNALS if s in n)
    if code_hits > theory_hits:
        return "code_heavy"
    if theory_hits > code_hits:
        return "theory_heavy"
    return "mixed"


# ─── Course inference ─────────────────────────────────────────────────────────

FLASK_TOPICS    = {"Building REST API's using Flask"}
LLMAPPS_TOPICS  = {
    "Getting Started with Third-Party Packages",
    "Building LLM Applications Using Python",
    "Building UI and Deploying LLM Applications",
    "Understanding How LLMs Works & Enhancing Productivity with AI",
    "Tools Use & Function Calling in LLMs",
    "Introduction to LangChain and Retrieval-Augmented Generation (RAG)",
    "Building AI Agents Using LangChain and Memory Agents",
    "Building AI-Powered Conversational Interview Assistant and RAG Agent Using LangChain",
    "Introduction to Context Engineering and MCP",
    "Building Multi Agent Systems and LLM Evaluation",
    "Running Models locally and Fine-Tuning LLMs",
}

def infer_course(topic, session_name):
    if topic in FLASK_TOPICS:
        return "flask"
    if topic in LLMAPPS_TOPICS:
        return "llm_apps"
    return "gen_ai"


# ─── Learning outcome / key concept derivation ───────────────────────────────

THEORY_VERBS = ["Understand", "Explain", "Describe", "Identify", "Recognize"]
CODE_VERBS   = ["Implement", "Apply", "Build", "Configure", "Use"]
MIXED_VERBS  = ["Understand and apply", "Work with", "Explore", "Understand"]

_ACTION_PREFIX = re.compile(
    r'^(understand|implement|build|apply|configure|use|create|design|'
    r'explore|identify|work with|learn|develop|integrate|train|deploy|'
    r'write|test|run|set up|setup|manage|handle|perform|generate|evaluate|'
    r'analyze|analyse|connect|access|load|store|retrieve|define|describe|'
    r'explain|demonstrate|establish|convert|process|extract|parse)\b',
    re.IGNORECASE,
)

def kp_to_outcome(kp_label, session_type, idx=0):
    label = kp_label.strip()
    # If KP label already starts with an action verb, use it directly
    if _ACTION_PREFIX.match(label):
        # Capitalise first letter
        return label[0].upper() + label[1:]
    if session_type == "theory_heavy":
        verb = THEORY_VERBS[idx % len(THEORY_VERBS)]
    elif session_type == "code_heavy":
        verb = CODE_VERBS[idx % len(CODE_VERBS)]
    else:
        verb = MIXED_VERBS[idx % len(MIXED_VERBS)]
    return f"{verb} {label}"


def kp_to_concept(kp_label):
    """Strip leading action verb from KP label to get the concept noun phrase."""
    label = re.sub(
        r'^(understanding|implementing|using|building|creating|exploring|integrating|'
        r'configuring|applying|working with)\s+',
        '', kp_label.lower()
    )
    return label.strip()


# ─── Build new sessions dict ──────────────────────────────────────────────────

print("\nBuilding new sessions...")
new_sessions = {}

for topic, sessions in course_structure.items():
    for session_name in sessions:
        kg_match = cs_to_kg_map.get(session_name)

        if kg_match:
            kp_ids = list(existing_sessions[kg_match].get("kp_ids", []))
        else:
            kp_ids = find_kps_for_session(session_name, topic)

        session_type = infer_session_type(session_name, topic)
        course       = infer_course(topic, session_name)

        # Derive outcomes and concepts from KP labels
        learning_outcomes = []
        key_concepts = []
        for i, kp_id in enumerate(kp_ids):
            kp_label = all_kps.get(kp_id, {}).get("label", "")
            if kp_label:
                learning_outcomes.append(kp_to_outcome(kp_label, session_type, i))
                key_concepts.append(kp_to_concept(kp_label))

        # Fallback: derive from session name
        if not learning_outcomes:
            clean = re.sub(r'\s*\|\s*Part\s*\d+', '', session_name).strip()
            action = "Implement" if session_type == "code_heavy" else "Understand"
            learning_outcomes = [f"{action} {clean}"]
            key_concepts      = [clean.lower()]

        new_sessions[session_name] = {
            "course":            course,
            "session_type":      session_type,
            "topic":             topic,
            "kp_ids":            kp_ids,
            "learning_outcomes": learning_outcomes,
            "key_concepts":      key_concepts,
        }

print(f"  Built {len(new_sessions)} sessions")
sessions_with_kps = sum(1 for s in new_sessions.values() if s["kp_ids"])
print(f"  Sessions with KPs: {sessions_with_kps}/{len(new_sessions)}")


# ─── Prerequisite edges ───────────────────────────────────────────────────────
# Keep existing KP-level edges; they're derived from curriculum and are correct.
# Also add session-ordering edges as topic_order (stored separately for reference).

topic_order_edges = []
topics_list = list(course_structure.keys())
for t_idx, topic in enumerate(topics_list):
    sessions = course_structure[topic]
    # Within-topic ordering
    for s_idx in range(len(sessions) - 1):
        topic_order_edges.append({
            "from": sessions[s_idx],
            "to":   sessions[s_idx + 1],
            "type": "within_topic",
        })
    # Cross-topic: last session of topic N → first session of topic N+1
    if t_idx < len(topics_list) - 1:
        next_sessions = course_structure[topics_list[t_idx + 1]]
        if sessions and next_sessions:
            topic_order_edges.append({
                "from": sessions[-1],
                "to":   next_sessions[0],
                "type": "cross_topic",
            })


# ─── Build KP registry (clean — use only KPs referenced by sessions) ─────────

used_kp_ids = set()
for s in new_sessions.values():
    used_kp_ids.update(s["kp_ids"])

# Keep all existing KPs (they may be referenced by prerequisite edges) + used ones
new_kps = {}
for kp_id, kp_data in all_kps.items():
    if kp_id in existing_kps or kp_id in used_kp_ids:
        new_kps[kp_id] = kp_data

print(f"\n  KPs in new graph: {len(new_kps)}")
print(f"  Topic-order session edges: {len(topic_order_edges)}")
print(f"  KP prerequisite edges kept: {len(existing_edges)}")


# ─── Write output ─────────────────────────────────────────────────────────────

output = {
    "metadata": {
        "total_kps":      len(new_kps),
        "total_sessions": len(new_sessions),
        "total_edges":    len(existing_edges),
        "topics":         len(course_structure),
        "built_from":     [
            "data/course_structure.json",
            "data/knowledge_graph.json",
            "data/curriculum/gen_ai_final.json",
            "data/curriculum/llm_applications_kp_links_final_fixed.json",
            "data/curriculum/flask_kp_links_final.json",
        ],
    },
    "knowledge_points":     new_kps,
    "sessions":             new_sessions,
    "prerequisite_edges":   existing_edges,
    "session_order_edges":  topic_order_edges,
}

out_path = DATA_DIR / "knowledge_graph.json"
with open(out_path, "w") as f:
    json.dump(output, f, indent=2)

print(f"\nWrote {out_path}")
print(f"  {len(new_kps)} KPs, {len(new_sessions)} sessions, {len(existing_edges)} KP edges, {len(topic_order_edges)} session-order edges")

# ─── Verification ─────────────────────────────────────────────────────────────

print("\n--- Verification ---")
for session_name, data in list(new_sessions.items())[:5]:
    print(f"\nSession: {session_name}")
    print(f"  type: {data['session_type']}, course: {data['course']}, topic: {data['topic']}")
    print(f"  kp_ids: {data['kp_ids'][:3]}")
    print(f"  outcomes: {data['learning_outcomes'][:2]}")
    print(f"  concepts: {data['key_concepts'][:2]}")
