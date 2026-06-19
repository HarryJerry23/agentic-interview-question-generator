"""SQLite memory layer — caching, run history, RLHF feedback.

Question storage is now in JSON files (data/), NOT in SQLite.
SQLite is only for: session resolution cache, run history, feedback.
"""

import sqlite3
import json
from src.config import MEMORY_DB


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
    """)
    conn.commit()
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
             composite_score: float, loops_used: int, approved: bool = False):
    conn = get_connection()
    conn.execute(
        """INSERT OR REPLACE INTO run_history
           (run_id, session_name, question_count, composite_score, loops_used, approved)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (run_id, session_name, question_count, composite_score, loops_used, int(approved))
    )
    conn.commit()
    conn.close()


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


# Initialize on import
init_db()
