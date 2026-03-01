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
    """Initialize the SQLite database and chat_messages table."""
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
    """Insert a message into chat history.

    Args:
        session_id: Chat session identifier
        role: Message role ('user' or 'assistant')
        content: Message content/text
    """
    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO chat_messages(session_id, role, content, created_at) VALUES (?, ?, ?, ?)",
            (session_id, role, content, int(time.time())),
        )
        conn.commit()
    finally:
        conn.close()


def save_message(session_id: str, role: str, message: str) -> None:
    """Save a message to chat history (alias for insert_message).

    Args:
        session_id: Chat session identifier
        role: Message role ('user' or 'assistant')
        message: Message text
    """
    insert_message(session_id, role, message)


def fetch_recent_messages(session_id: str, limit: int = 12) -> list[dict]:
    """Fetch recent messages from a chat session, in chronological order.

    Args:
        session_id: Chat session identifier
        limit: Maximum number of messages to fetch (default: 12)

    Returns:
        List of message dicts with 'role' and 'content' keys
    """
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


def get_chat_history(session_id: str, limit: int = 12) -> list[dict]:
    """Get chat history for a session (alias for fetch_recent_messages).

    Args:
        session_id: Chat session identifier
        limit: Maximum number of messages to fetch (default: 12)

    Returns:
        List of message dicts with 'role' and 'content' keys, in chronological order
    """
    return fetch_recent_messages(session_id, limit)


def get_all_chat_history(session_id: str) -> list[dict]:
    """Get entire chat history for a session.

    Args:
        session_id: Chat session identifier

    Returns:
        List of all message dicts with 'role', 'content', 'created_at', and 'id' keys
    """
    conn = get_conn()
    try:
        cur = conn.execute(
            """
            SELECT id, session_id, role, content, created_at
            FROM chat_messages
            WHERE session_id = ?
            ORDER BY id ASC
            """,
            (session_id,),
        )
        rows = cur.fetchall()
        return [
            {
                "id": r["id"],
                "session_id": r["session_id"],
                "role": r["role"],
                "content": r["content"],
                "created_at": r["created_at"],
            }
            for r in rows
        ]
    finally:
        conn.close()


def delete_session_history(session_id: str) -> int:
    """Delete all messages in a chat session.

    Args:
        session_id: Chat session identifier

    Returns:
        Number of messages deleted
    """
    conn = get_conn()
    try:
        cur = conn.execute(
            "DELETE FROM chat_messages WHERE session_id = ?",
            (session_id,),
        )
        conn.commit()
        return cur.rowcount
    finally:
        conn.close()


def get_session_count() -> int:
    """Get total number of unique chat sessions.

    Returns:
        Count of unique session IDs
    """
    conn = get_conn()
    try:
        cur = conn.execute("SELECT COUNT(DISTINCT session_id) as count FROM chat_messages")
        row = cur.fetchone()
        return row["count"] if row else 0
    finally:
        conn.close()


def get_message_count(session_id: str) -> int:
    """Get message count for a specific session.

    Args:
        session_id: Chat session identifier

    Returns:
        Number of messages in session
    """
    conn = get_conn()
    try:
        cur = conn.execute(
            "SELECT COUNT(*) as count FROM chat_messages WHERE session_id = ?",
            (session_id,),
        )
        row = cur.fetchone()
        return row["count"] if row else 0
    finally:
        conn.close()


def export_session_to_json(session_id: str) -> dict:
    """Export a complete chat session as JSON-serializable dict.

    Args:
        session_id: Chat session identifier

    Returns:
        Dict with session metadata and messages
    """
    history = get_all_chat_history(session_id)
    return {
        "session_id": session_id,
        "message_count": len(history),
        "messages": history,
    }

