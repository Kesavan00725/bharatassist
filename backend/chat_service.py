from __future__ import annotations

import json
import os
import uuid
from typing import Any, Optional

from openai import OpenAI

from database import fetch_recent_messages, insert_message


SYSTEM_PROMPT = """You are BharatAssist, a helpful assistant for Indian government schemes.

You MUST:
- Use only the provided eligibility results to inform responses
- Never hallucinate or claim knowledge beyond what was provided
- If unsure or data is insufficient, say "Insufficient data."
- Be concise and practical
- Never claim official authority; suggest verifying on official portals
- Help users understand their eligibility and next steps

Guidelines:
- Ask 1-3 clarifying questions about missing eligibility details (age, income, state, category, occupation) if needed
- Provide actionable next steps
- Reference specific schemes by name when relevant
- Highlight required documents for eligible schemes

Output format: Always respond with JSON containing:
{
  "reply": "your message to the user (string)",
  "scheme_suggestions": ["scheme_id_1", "scheme_id_2"] (or empty list if not applicable),
  "clarification_needed": ["field1", "field2"] (or empty list if all data available)
}"""


def _get_client() -> Optional[OpenAI]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    return OpenAI(api_key=api_key)


def get_or_create_session_id(session_id: Optional[str]) -> str:
    if session_id and str(session_id).strip():
        return str(session_id).strip()
    return uuid.uuid4().hex


def _build_context_prompt(
    user_profile: dict[str, Any], eligibility_results: Optional[dict[str, Any]]
) -> str:
    """Build context about user profile and eligibility for the system prompt."""
    context_lines = ["## User Context:\n"]

    # Add user profile
    context_lines.append("**User Profile:**")
    for key, value in user_profile.items():
        if value is not None:
            context_lines.append(f"- {key}: {value}")

    # Add eligibility results
    if eligibility_results:
        context_lines.append("\n**Eligibility Results:**")
        if eligibility_results.get("best_match"):
            best = eligibility_results["best_match"]
            context_lines.append(
                f"- Best Match: {best['scheme_name']} (Score: {best['score']}/100, Official: {best['official_link']})"
            )

        if eligibility_results.get("eligible_schemes"):
            context_lines.append(
                f"- {len(eligibility_results['eligible_schemes'])} eligible scheme(s):"
            )
            for scheme in eligibility_results["eligible_schemes"]:
                context_lines.append(f"  - {scheme['scheme_name']} (score: {scheme['score']})")

        if eligibility_results.get("not_eligible_schemes"):
            context_lines.append(
                f"- {len(eligibility_results['not_eligible_schemes'])} not eligible scheme(s)"
            )

    return "\n".join(context_lines)


def chat_reply(
    session_id: str,
    user_message: str,
    user_profile: Optional[dict[str, Any]] = None,
    eligibility_results: Optional[dict[str, Any]] = None,
) -> str:
    """
    Generate a chat reply with eligibility context.

    Args:
        session_id: Chat session identifier
        user_message: User's message
        user_profile: User profile data (age, income, state, etc.)
        eligibility_results: Results from eligibility engine

    Returns:
        Reply text (or JSON if response_format enforced)
    """
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

    # Build system prompt with context
    system_prompt = SYSTEM_PROMPT
    if user_profile or eligibility_results:
        context = _build_context_prompt(user_profile or {}, eligibility_results)
        system_prompt = f"{SYSTEM_PROMPT}\n\n{context}"

    messages = [{"role": "system", "content": system_prompt}, *history]

    try:
        resp = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=messages,
            temperature=0.3,
            response_format={"type": "json_object"},
        )
        response_text = (resp.choices[0].message.content or "").strip()

        # Parse JSON response
        try:
            response_json = json.loads(response_text)
            reply = response_json.get("reply", response_text)
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            reply = response_text or "Sorry, I couldn't generate a reply."

    except Exception as e:
        reply = f"Chat service error: {type(e).__name__}. Try again in a moment."

    insert_message(session_id, "assistant", reply)
    return reply


def chat_reply_with_json(
    session_id: str,
    user_message: str,
    user_profile: Optional[dict[str, Any]] = None,
    eligibility_results: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """
    Generate a chat reply and return full JSON response.

    Returns:
        Dict with reply, scheme_suggestions, clarification_needed
    """
    insert_message(session_id, "user", user_message)

    client = _get_client()
    if client is None:
        response = {
            "reply": "OpenAI is not configured (missing `OPENAI_API_KEY`). Please provide your profile details.",
            "scheme_suggestions": [],
            "clarification_needed": ["age", "income_inr", "state", "occupation"],
        }
        insert_message(session_id, "assistant", response["reply"])
        return response

    history = fetch_recent_messages(session_id, limit=10)

    # Build system prompt with context
    system_prompt = SYSTEM_PROMPT
    if user_profile or eligibility_results:
        context = _build_context_prompt(user_profile or {}, eligibility_results)
        system_prompt = f"{SYSTEM_PROMPT}\n\n{context}"

    messages = [{"role": "system", "content": system_prompt}, *history]

    try:
        resp = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=messages,
            temperature=0.3,
            response_format={"type": "json_object"},
        )
        response_text = (resp.choices[0].message.content or "").strip()
        response_json = json.loads(response_text)

        # Ensure required fields
        response = {
            "reply": response_json.get("reply", ""),
            "scheme_suggestions": response_json.get("scheme_suggestions", []),
            "clarification_needed": response_json.get("clarification_needed", []),
        }

    except json.JSONDecodeError as e:
        response = {
            "reply": f"Response parsing error: {str(e)[:50]}",
            "scheme_suggestions": [],
            "clarification_needed": [],
        }
    except Exception as e:
        response = {
            "reply": f"Chat service error: {type(e).__name__}. Try again in a moment.",
            "scheme_suggestions": [],
            "clarification_needed": [],
        }

    insert_message(session_id, "assistant", response["reply"])
    return response

