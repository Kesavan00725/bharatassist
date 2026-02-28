from __future__ import annotations

import os
import uuid
from typing import Optional

from openai import OpenAI

from database import fetch_recent_messages, insert_message


SYSTEM_PROMPT = """You are BharatAssist, a helpful assistant for Indian government schemes.
You must:
- Ask 1-3 short questions to clarify missing eligibility details when needed (age, income, state, category, occupation).
- Give simple, practical next steps.
- Never claim official authority; suggest verifying on official portals.
Keep answers concise."""


def _get_client() -> Optional[OpenAI]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    return OpenAI(api_key=api_key)


def get_or_create_session_id(session_id: Optional[str]) -> str:
    if session_id and str(session_id).strip():
        return str(session_id).strip()
    return uuid.uuid4().hex


def chat_reply(session_id: str, user_message: str) -> str:
    insert_message(session_id, "user", user_message)

    client = _get_client()
    if client is None:
        reply = (
            "OpenAI is not configured (missing `OPENAI_API_KEY`). "
            "I can still help: tell me your age, annual income (INR), state, and occupation."
        )
        insert_message(session_id, "assistant", reply)
        return reply

    history = fetch_recent_messages(session_id, limit=10)
    messages = [{"role": "system", "content": SYSTEM_PROMPT}, *history]

    try:
        resp = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=messages,
            temperature=0.3,
        )
        reply = (resp.choices[0].message.content or "").strip() or "Sorry, I couldn't generate a reply."
    except Exception as e:
        reply = f"Chat service error: {type(e).__name__}. Try again in a moment."

    insert_message(session_id, "assistant", reply)
    return reply
