"""Data loader — loads prepared JSON data files into memory.

Reads from data/ directory (prepared by scripts/prepare_data.py):
  - interview_questions.json — filtered interview questions
  - knowledge_graph.json — KPs, sessions, prerequisites
  - scraped_questions.json — questions from curated URLs

Also loads reading materials from markdown files for session content.
"""

import json
import re
import networkx as nx
from pathlib import Path
from src.config import (
    PROJECT_ROOT,
    INTERVIEW_QUESTIONS_JSON, KNOWLEDGE_GRAPH_JSON, SCRAPED_QUESTIONS_JSON,
    GEN_AI_RM, LLM_APPS_RM, CURATED_URLS,
    GEN_AI_JSON, LLM_APPS_JSON, FLASK_JSON,
)


class DataStore:
    """Loads all prepared data files once and provides access."""

    def __init__(self):
        # From knowledge_graph.json
        self.kp_catalog: dict[str, str] = {}        # kp_id -> kp_label
        self.kp_source_map: dict[str, str] = {}     # kp_id -> course name
        self.kp_details: dict[str, dict] = {}       # kp_id -> full KP data (prereqs, dependents)
        self.sessions: dict[str, dict] = {}          # session_name -> {course, kp_ids, outcomes, ...}
        self.prerequisite_dag: nx.DiGraph = nx.DiGraph()

        # From interview_questions.json + scraped_questions.json
        self.interview_questions: list[dict] = []
        self.scraped_questions: list[dict] = []
        self.curriculum_questions: list[dict] = []

        # From reading materials
        self.reading_materials: dict[str, str] = {}  # session_name -> section text

        # From curriculum JSONs (for KP catalog building)
        self.csv_taxonomy: list[dict] = []
        self.curated_urls: list[str] = []

        self._loaded = False

    def load(self):
        if self._loaded:
            return
        self._load_knowledge_graph()
        self._load_interview_questions()
        self._load_scraped_questions()
        self._load_reading_materials()
        self._load_curated_urls()
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

    def _load_scraped_questions(self):
        """Load scraped questions from JSON."""
        if not SCRAPED_QUESTIONS_JSON.exists():
            return

        with open(SCRAPED_QUESTIONS_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.scraped_questions = data.get("questions", [])
        print(f"Loaded {len(self.scraped_questions)} scraped questions")

    def _load_reading_materials(self):
        """Parse reading material markdown files into session sections."""
        rm_files = [
            (GEN_AI_RM, "gen_ai"),
            (LLM_APPS_RM, "llm_applications"),
        ]
        for filepath, prefix in rm_files:
            if not filepath.exists():
                continue
            text = filepath.read_text(encoding="utf-8")
            sessions = self._parse_rm_sessions(text)
            for name, content in sessions.items():
                self.reading_materials[name] = content

    def _parse_rm_sessions(self, text: str) -> dict[str, str]:
        """Split reading material into sessions by top-level headings."""
        clean_text = re.sub(r'```[\s\S]*?```', '', text)
        pattern = r'^"?#\s+([A-Z][^\n]+)'
        sections: dict[str, str] = {}
        skip_titles = {
            "introduction", "common issues you may encounter",
            "setting the scheduler to run every week",
        }

        matches = list(re.finditer(pattern, clean_text, re.MULTILINE))
        for i, match in enumerate(matches):
            title = match.group(1).strip().strip('"').strip()
            if title.lower() in skip_titles or re.match(r'^\d+\.', title) or len(title) < 8:
                continue

            title_pattern = re.escape(title[:40])
            orig_match = re.search(r'^"?#\s+' + title_pattern, text, re.MULTILINE)
            if not orig_match:
                continue

            start = orig_match.start()
            next_heading = re.search(r'\n"?#\s+[A-Z]', text[start + 1:])
            end = start + 1 + next_heading.start() if next_heading else len(text)
            sections[title] = text[start:end].strip()[:8000]

        return sections

    def _load_curated_urls(self):
        """Load URLs from curated_urls.md."""
        if not CURATED_URLS.exists():
            return
        text = CURATED_URLS.read_text(encoding="utf-8")
        self.curated_urls = [
            line.strip() for line in text.splitlines()
            if line.strip() and line.strip().startswith("http")
        ]

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
        """Get reading material content for a session."""
        if session_name in self.reading_materials:
            return self.reading_materials[session_name]
        lower = session_name.lower()
        for name, content in self.reading_materials.items():
            if lower in name.lower() or name.lower() in lower:
                return content
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
        """Return only interview questions with verified company attribution.
        Scraped questions are excluded — they lack company/role tags required for output."""
        return self.interview_questions


# Singleton
_data_store: DataStore | None = None


def get_data_store() -> DataStore:
    global _data_store
    if _data_store is None:
        _data_store = DataStore()
        _data_store.load()
    return _data_store
