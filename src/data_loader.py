"""Data loader — loads prepared JSON data files into memory.

Reads from data/ directory (prepared by scripts/prepare_data.py):
  - interview_questions.json — filtered interview questions
  - knowledge_graph.json — KPs, sessions, prerequisites
  - reading_materials/session_map.json — per-session reading material

Also loads reading materials from markdown files for session content.
"""

import json
import re
import networkx as nx
from pathlib import Path
from src.config import (
    PROJECT_ROOT, DATA_DIR,
    INTERVIEW_QUESTIONS_JSON, KNOWLEDGE_GRAPH_JSON,
    GEN_AI_RM, LLM_APPS_RM, SESSION_MAP_JSON,
    GEN_AI_JSON, LLM_APPS_JSON, FLASK_JSON,
)


def _normalize_session_key(name: str) -> str:
    """Normalize a session name for tolerant exact-ish matching (case, spacing,
    punctuation around 'Part N')."""
    s = name.lower().strip()
    s = re.sub(r"[|:]", " ", s)        # treat "| Part 1" / ": Part 1" uniformly
    s = re.sub(r"\s+", " ", s)
    return s


class DataStore:
    """Loads all prepared data files once and provides access."""

    def __init__(self):
        # From knowledge_graph.json
        self.kp_catalog: dict[str, str] = {}        # kp_id -> kp_label
        self.kp_source_map: dict[str, str] = {}     # kp_id -> course name
        self.kp_details: dict[str, dict] = {}       # kp_id -> full KP data (prereqs, dependents)
        self.sessions: dict[str, dict] = {}          # session_name -> {course, kp_ids, outcomes, ...}
        self.prerequisite_dag: nx.DiGraph = nx.DiGraph()

        # From interview_questions.json
        self.interview_questions: list[dict] = []
        self.curriculum_questions: list[dict] = []

        # From reading materials
        self.reading_materials: dict[str, str] = {}  # session_name -> section text
        self._rm_norm_index: dict[str, str] = {}     # normalized name -> canonical key

        # From curriculum JSONs (for KP catalog building)
        self.csv_taxonomy: list[dict] = []

        self._loaded = False

    def load(self):
        if self._loaded:
            return
        self._load_knowledge_graph()
        self._load_interview_questions()
        self._load_reading_materials()
        self._load_curriculum_kps()
        self._loaded = True

    def _load_knowledge_graph(self):
        """Load knowledge graph with KPs, sessions, and prerequisites."""
        if not KNOWLEDGE_GRAPH_JSON.exists():
            print("WARNING: knowledge_graph.json not found. Run: python scripts/prepare_data.py")
            return

        with open(KNOWLEDGE_GRAPH_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)

        # KPs
        for kp_id, kp_data in data.get("knowledge_points", {}).items():
            self.kp_catalog[kp_id] = kp_data["label"]
            self.kp_source_map[kp_id] = kp_data.get("course", "unknown")
            self.kp_details[kp_id] = kp_data

        # Sessions
        self.sessions = data.get("sessions", {})

        # DAG
        for edge in data.get("prerequisite_edges", []):
            src, tgt = edge.get("from", ""), edge.get("to", "")
            if src and tgt:
                self.prerequisite_dag.add_edge(src, tgt)

        print(f"Loaded knowledge graph: {len(self.kp_catalog)} KPs, {len(self.sessions)} sessions")

    def _load_interview_questions(self):
        """Load pre-filtered interview questions from JSON."""
        if not INTERVIEW_QUESTIONS_JSON.exists():
            print("WARNING: interview_questions.json not found. Run: python scripts/prepare_data.py")
            return

        with open(INTERVIEW_QUESTIONS_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.interview_questions = data.get("questions", [])
        print(f"Loaded {len(self.interview_questions)} interview questions")

    def _load_reading_materials(self):
        """Load the precise per-session reading-material map.

        The map (data/reading_materials/session_map.json) is keyed by canonical
        session names and built by scripts/build_session_reading_material.py.
        We rely on exact/normalized keys — no fuzzy substring guessing — so a
        session always gets its OWN content (or none, falling back to the KG).
        """
        if not SESSION_MAP_JSON.exists():
            print("WARNING: session_map.json not found. "
                  "Run: python scripts/build_session_reading_material.py")
            return
        with open(SESSION_MAP_JSON, "r", encoding="utf-8") as f:
            self.reading_materials = json.load(f)
        self._rm_norm_index = {
            _normalize_session_key(name): name for name in self.reading_materials
        }
        print(f"Loaded reading material for {len(self.reading_materials)} sessions")

    def _load_curriculum_kps(self):
        """Load KP catalog from curriculum JSONs and add questions to bank."""
        json_files = [
            (GEN_AI_JSON, "gen_ai"),
            (LLM_APPS_JSON, "llm_applications"),
            (FLASK_JSON, "flask"),
        ]
        for filepath, course_name in json_files:
            if not filepath.exists():
                continue
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            for q in data.get("questions", []):
                # KP catalog
                kps = q.get("selected_knowledge_points", [])
                for kp in kps:
                    kp_id = kp["resolved_kp_id"]
                    if kp_id not in self.kp_catalog:
                        self.kp_catalog[kp_id] = kp["resolved_kp_label"]
                        self.kp_source_map[kp_id] = course_name
                # Normalize into question bank format
                text = (q.get("question_text_with_code_context") or "").strip()
                if not text or len(text) < 10:
                    continue
                topic = kps[0].get("resolved_kp_label", course_name) if kps else course_name
                diff_raw = q.get("question_difficulty", "medium")
                difficulty = diff_raw.capitalize() if diff_raw else "Medium"
                self.curriculum_questions.append({
                    "id": q.get("question_id", ""),
                    "content": text,
                    "difficulty": difficulty,
                    "category": q.get("question_type", "GENERAL"),
                    "topic": topic,
                    "sub_topic": None,
                    "company": None,
                    "role": None,
                    "source": "curriculum",
                })
        print(f"Loaded {len(self.curriculum_questions)} curriculum questions into bank")

    # ── Public API ──────────────────────────────────────────────────────

    def get_session_names(self) -> list[str]:
        """Return all known session names (from knowledge graph + reading materials)."""
        all_names = set(self.sessions.keys()) | set(self.reading_materials.keys())
        return sorted(all_names)

    def get_session_content(self, session_name: str) -> str | None:
        """Get reading material content for a session.

        Exact key first, then a normalized (case/spacing/'| Part N') match.
        No broad substring fallback — a near-miss must return None so
        understand_session falls back to the knowledge graph rather than
        feeding the wrong session's content.
        """
        if session_name in self.reading_materials:
            return self.reading_materials[session_name]
        canonical = self._rm_norm_index.get(_normalize_session_key(session_name))
        if canonical:
            return self.reading_materials[canonical]
        return None

    def get_session_info(self, session_name: str) -> dict | None:
        """Get structured session info from knowledge graph (KPs, outcomes, type)."""
        if session_name in self.sessions:
            return self.sessions[session_name]
        lower = session_name.lower()
        for name, info in self.sessions.items():
            if lower in name.lower() or name.lower() in lower:
                return info
        return None

    def get_kp_ancestors(self, kp_ids: list[str]) -> list[str]:
        """Get prerequisite KP IDs ordered by topological sort."""
        ancestors = set()
        for kp_id in kp_ids:
            if kp_id in self.prerequisite_dag:
                ancestors.update(nx.ancestors(self.prerequisite_dag, kp_id))
        all_kps = ancestors | set(kp_ids)
        subgraph = self.prerequisite_dag.subgraph(
            [kp for kp in all_kps if kp in self.prerequisite_dag]
        )
        try:
            return list(nx.topological_sort(subgraph))
        except nx.NetworkXUnfeasible:
            return list(all_kps)

    def get_all_questions(self) -> list[dict]:
        """Return the interview questions with verified company attribution."""
        return self.interview_questions


_COURSE_STRUCTURE = DATA_DIR / "course_structure.json"
_topic_index: dict[str, str] | None = None  # session name (lower) -> topic name


def get_topic_for_session(session_name: str) -> str | None:
    """Reverse-lookup the course topic for a (possibly combined) session name.

    `session_name` may be "A + B + C"; returns the course_structure topic whose
    session list contains any of those sessions. Returns None if not found
    (e.g. a custom topic). Cached after first load.
    """
    global _topic_index
    if _topic_index is None:
        _topic_index = {}
        try:
            with open(_COURSE_STRUCTURE, "r", encoding="utf-8") as f:
                structure = json.load(f)
            for topic, sessions in structure.items():
                for s in sessions:
                    _topic_index[s.strip().lower()] = topic
        except Exception:
            _topic_index = {}
    for part in session_name.split(" + "):
        topic = _topic_index.get(part.strip().lower())
        if topic:
            return topic
    return None


# Singleton
_data_store: DataStore | None = None


def get_data_store() -> DataStore:
    global _data_store
    if _data_store is None:
        _data_store = DataStore()
        _data_store.load()
    return _data_store
