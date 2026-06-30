"""SQLite memory layer — caching, run history, RLHF feedback, cross-run question bank."""

import sqlite3
import json
import pathlib
from src.config import MEMORY_DB

_RULES_FILE = pathlib.Path(__file__).parent.parent / "data" / "learned_rules.md"
_MAX_RULE_CHARS = 200


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(MEMORY_DB))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    """Create tables if they don't exist."""
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS session_resolutions (
            session_name    TEXT PRIMARY KEY,
            resolution_json TEXT NOT NULL,
            created_at      TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS run_history (
            run_id          TEXT PRIMARY KEY,
            session_name    TEXT NOT NULL,
            question_count  INTEGER,
            composite_score REAL,
            loops_used      INTEGER,
            approved        INTEGER DEFAULT 0,
            created_at      TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS run_results (
            run_id       TEXT PRIMARY KEY,
            payload_json TEXT NOT NULL,
            created_at   TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS question_feedback (
            question_id TEXT NOT NULL,
            run_id      TEXT NOT NULL,
            feedback    TEXT NOT NULL,
            created_at  TEXT DEFAULT (datetime('now')),
            PRIMARY KEY (question_id, run_id)
        );

        CREATE TABLE IF NOT EXISTS suppress_boost (
            question_id TEXT PRIMARY KEY,
            score       REAL NOT NULL,
            action      TEXT NOT NULL,
            updated_at  TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS question_bank (
            question_id  TEXT PRIMARY KEY,
            session_name TEXT NOT NULL,
            content      TEXT NOT NULL,
            source       TEXT,
            created_at   TEXT DEFAULT (datetime('now'))
        );
    """)
    conn.commit()
    # Migrate: add columns to existing databases
    for migration in [
        "ALTER TABLE run_history ADD COLUMN api_usage_json TEXT",
    ]:
        try:
            conn.execute(migration)
            conn.commit()
        except sqlite3.OperationalError:
            pass  # column already exists
    conn.close()


# --- Session Resolution Cache ---

def get_cached_resolution(session_name: str) -> dict | None:
    conn = get_connection()
    row = conn.execute(
        "SELECT resolution_json FROM session_resolutions WHERE session_name = ?",
        (session_name,)
    ).fetchone()
    conn.close()
    if row:
        return json.loads(row["resolution_json"])
    return None


def cache_resolution(session_name: str, resolution: dict):
    conn = get_connection()
    conn.execute(
        "INSERT OR REPLACE INTO session_resolutions (session_name, resolution_json) VALUES (?, ?)",
        (session_name, json.dumps(resolution))
    )
    conn.commit()
    conn.close()


# --- Run History ---

def save_run(run_id: str, session_name: str, question_count: int,
             composite_score: float, loops_used: int, approved: bool = False,
             api_usage: dict | None = None):
    conn = get_connection()
    conn.execute(
        """INSERT OR REPLACE INTO run_history
           (run_id, session_name, question_count, composite_score, loops_used, approved, api_usage_json)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (run_id, session_name, question_count, composite_score, loops_used, int(approved),
         json.dumps(api_usage) if api_usage else None)
    )
    conn.commit()
    conn.close()


def save_run_result(run_id: str, payload: dict):
    """Persist the full run payload ({context, output, report}) so Review and
    re-export survive server restarts."""
    conn = get_connection()
    conn.execute(
        "INSERT OR REPLACE INTO run_results (run_id, payload_json) VALUES (?, ?)",
        (run_id, json.dumps(payload))
    )
    conn.commit()
    conn.close()


def get_run_result(run_id: str) -> dict | None:
    conn = get_connection()
    row = conn.execute(
        "SELECT payload_json FROM run_results WHERE run_id = ?", (run_id,)
    ).fetchone()
    conn.close()
    return json.loads(row["payload_json"]) if row else None


def get_run_history(limit: int = 100) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT run_id, session_name, question_count, composite_score, loops_used, approved, "
        "created_at, api_usage_json FROM run_history ORDER BY created_at DESC LIMIT ?",
        (limit,)
    ).fetchall()
    conn.close()
    result = []
    for row in rows:
        d = dict(row)
        d["api_usage"] = json.loads(d.pop("api_usage_json") or "{}") or {}
        result.append(d)
    return result


# --- Suppress/Boost Lists ---

def get_suppress_list() -> list[str]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT question_id FROM suppress_boost WHERE action = 'suppress'"
    ).fetchall()
    conn.close()
    return [r["question_id"] for r in rows]


def get_boost_list() -> list[str]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT question_id FROM suppress_boost WHERE action = 'boost'"
    ).fetchall()
    conn.close()
    return [r["question_id"] for r in rows]


# --- Learned Rules (distilled from human rejections) ---

def get_learned_rules() -> list[str]:
    """Read learned validation rules from data/learned_rules.md."""
    try:
        text = _RULES_FILE.read_text()
        section = text.split("## Rules")[-1]
        return [line.lstrip("- ").strip() for line in section.splitlines()
                if line.strip().startswith("- ")]
    except Exception:
        return []


def append_learned_rule(rule: str) -> bool:
    """Append a new rule to learned_rules.md. Returns True if added, False if duplicate/invalid."""
    rule = rule.strip()[:_MAX_RULE_CHARS]
    if not rule or "##" in rule or "<!--" in rule:
        return False
    if rule in get_learned_rules():
        return False
    _RULES_FILE.parent.mkdir(exist_ok=True)
    if not _RULES_FILE.exists():
        _RULES_FILE.write_text(
            "# Learned Validation Rules\n"
            "<!-- Auto-generated from reviewer rejections. Do not edit manually. -->\n\n"
            "## Rules\n"
        )
    with _RULES_FILE.open("a") as f:
        f.write(f"- {rule}\n")
    return True


def distill_rule(session_name: str, reason: str) -> str:
    """Use LLM to distil a rejection reason into a reusable validation rule."""
    from src.llm_client import chat_completion_json
    try:
        result = chat_completion_json(
            system_prompt="You convert interview question rejection reasons into reusable validation rules.",
            user_prompt=(
                f'A reviewer rejected an interview question for a session on "{session_name}" '
                f'with this reason:\n"{reason}"\n\n'
                f"Write a ≤200-char rule starting with \"Reject if\" or \"Skip if\" that generalises "
                f"this rejection so future questions with the same problem are caught automatically. "
                f"Be specific and actionable.\n"
                f'Return JSON: {{"rule": "..."}}'
            ),
            max_tokens=200,
        )
        return (result.get("rule") or "").strip()[:_MAX_RULE_CHARS]
    except Exception:
        return ""


# --- Cross-Run Question Bank ---

def save_question_to_bank(question_id: str, session_name: str, content: str, source: str = None):
    """Save an approved question to the persistent cross-run bank."""
    conn = get_connection()
    conn.execute(
        "INSERT OR IGNORE INTO question_bank (question_id, session_name, content, source) VALUES (?, ?, ?, ?)",
        (question_id, session_name, content, source)
    )
    conn.commit()
    conn.close()


def get_bank_questions(session_name: str) -> list[dict]:
    """Return all banked questions for the given session (for cross-run dedup)."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT question_id, content FROM question_bank WHERE session_name = ? ORDER BY created_at DESC",
        (session_name,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# Initialize on import
init_db()
