from __future__ import annotations

import sqlite3
import time
from pathlib import Path
from typing import Iterable, Optional


DB_PATH = Path(__file__).resolve().parent / "bharatassist.db"


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_conn()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_messages (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              session_id TEXT NOT NULL,
              role TEXT NOT NULL,
              content TEXT NOT NULL,
              created_at INTEGER NOT NULL
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_chat_session ON chat_messages(session_id)")
        conn.commit()
    finally:
        conn.close()


def insert_message(session_id: str, role: str, content: str) -> None:
    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO chat_messages(session_id, role, content, created_at) VALUES (?, ?, ?, ?)",
            (session_id, role, content, int(time.time())),
        )
        conn.commit()
    finally:
        conn.close()


def fetch_recent_messages(session_id: str, limit: int = 12) -> list[dict]:
    conn = get_conn()
    try:
        cur = conn.execute(
            """
            SELECT role, content
            FROM chat_messages
            WHERE session_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (session_id, limit),
        )
        rows = cur.fetchall()
        rows = list(reversed(rows))
        return [{"role": r["role"], "content": r["content"]} for r in rows]
    finally:
        conn.close()
