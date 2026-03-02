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


def _extract_profile_from_message(message: str) -> dict[str, Any]:
    """Extract user profile from natural language message."""
    import re

    profile = {}
    message_lower = message.lower()

    # Extract age
    age_match = re.search(r'(\d{1,3})\s*(?:years?|yr|yrs|age)', message_lower)
    if age_match:
        age = int(age_match.group(1))
        if 0 <= age <= 120:
            profile['age'] = age

    # Extract income (look for numbers followed by lac/lakh/crore/rupees/inr/₹)
    # Match number that is followed by income keywords or preceded by currency symbols
    income_match = re.search(
        r'(?:₹|rs\.?|inr)?\s*(\d+(?:[.,]\d+)?)\s*(?:lac|lakh|crore|rupees?)',
        message_lower
    )
    if income_match:
        income_str = income_match.group(1).replace(',', '')
        income_num = float(income_str)
        # Determine multiplier based on keyword
        if 'crore' in message_lower[income_match.start():income_match.end()]:
            income_num *= 10000000
        elif 'lakh' in message_lower[income_match.start():income_match.end()] or 'lac' in message_lower[income_match.start():income_match.end()]:
            income_num *= 100000
        profile['income_inr'] = int(income_num)

    # Extract state
    states = [
        'andhra pradesh', 'arunachal pradesh', 'assam', 'bihar', 'chhattisgarh',
        'goa', 'gujarat', 'haryana', 'himachal pradesh', 'jharkhand',
        'karnataka', 'kerala', 'madhya pradesh', 'maharashtra', 'manipur',
        'meghalaya', 'mizoram', 'nagaland', 'odisha', 'punjab', 'rajasthan',
        'sikkim', 'tamil nadu', 'telangana', 'tripura', 'uttar pradesh',
        'uttarakhand', 'west bengal', 'delhi'
    ]
    for state in states:
        if state in message_lower:
            profile['state'] = state.title()
            break

    # Extract occupation
    occupations = ['farmer', 'student', 'retired', 'self-employed', 'employed',
                   'unemployed', 'laborer', 'worker', 'trader', 'business']
    for occupation in occupations:
        if occupation in message_lower:
            profile['occupation'] = occupation
            break

    # Check for disability mention
    if 'disable' in message_lower or 'disabled' in message_lower or 'disability' in message_lower:
        profile['is_disabled'] = True

    # Check for rural mention
    if 'rural' in message_lower or 'village' in message_lower:
        profile['rural'] = True
    elif 'urban' in message_lower or 'city' in message_lower:
        profile['rural'] = False

    # Check for category
    categories = ['sc', 'st', 'obc', 'ews', 'general']
    for cat in categories:
        if cat in message_lower:
            profile['category'] = cat.upper()
            break

    return profile


def _format_eligibility_reply(results: dict[str, Any], profile: dict[str, Any]) -> str:
    """Format eligibility results as a readable message."""
    lines = []

    # Add profile summary
    profile_parts = []
    if profile.get('age'):
        profile_parts.append(f"Age: {profile['age']}")
    if profile.get('income_inr'):
        profile_parts.append(f"Income: ₹{profile['income_inr']:,}")
    if profile.get('state'):
        profile_parts.append(f"State: {profile['state']}")
    if profile.get('occupation'):
        profile_parts.append(f"Occupation: {profile['occupation']}")

    if profile_parts:
        lines.append(f"Profile: {', '.join(profile_parts)}\n")

    # Add best match
    if results.get('best_match'):
        best = results['best_match']
        lines.append(f"✓ BEST MATCH: {best['scheme_name']}")
        lines.append(f"  Score: {best['score']}/100")
        if best.get('benefits'):
            lines.append(f"  Benefits: {', '.join(best['benefits'][:3])}")
        lines.append("")

    # Add eligible schemes count
    eligible = results.get('eligible_schemes', [])
    if eligible:
        lines.append(f"✓ You are eligible for {len(eligible)} scheme(s):")
        for scheme in eligible[:3]:  # Show top 3
            lines.append(f"  • {scheme['scheme_name']} (Score: {scheme['score']}/100)")
        if len(eligible) > 3:
            lines.append(f"  ... and {len(eligible) - 3} more")
        lines.append("")

    # Add not eligible schemes count
    not_eligible = results.get('not_eligible_schemes', [])
    if not_eligible:
        lines.append(f"✗ Not eligible for {len(not_eligible)} scheme(s)")
        lines.append("")

    # Add call to action
    lines.append("Visit the eligibility checker page for detailed results and to verify documents.")

    return "\n".join(lines)


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
        # Fallback when no OpenAI key: try to extract profile from message
        from eligibility_engine import evaluate_eligibility

        profile = _extract_profile_from_message(user_message)
        if profile and any([profile.get("age"), profile.get("income_inr"), profile.get("state")]):
            try:
                results = evaluate_eligibility(profile)
                reply = _format_eligibility_reply(results, profile)
                insert_message(session_id, "assistant", reply)
                return reply
            except Exception:
                pass

        reply = (
            "I can help you find eligible schemes. Please tell me your age, annual income (INR), state, and occupation."
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
        # Fallback when no OpenAI key: try to extract profile from message
        from eligibility_engine import evaluate_eligibility

        profile = _extract_profile_from_message(user_message)
        if profile and any([profile.get("age"), profile.get("income_inr"), profile.get("state")]):
            try:
                results = evaluate_eligibility(profile)
                reply = _format_eligibility_reply(results, profile)
                scheme_suggestions = [s["id"] for s in results.get("eligible_schemes", [])][:3]
                response = {
                    "reply": reply,
                    "scheme_suggestions": scheme_suggestions,
                    "clarification_needed": [],
                }
                insert_message(session_id, "assistant", reply)
                return response
            except Exception:
                pass

        missing = []
        if not profile.get("age"):
            missing.append("age")
        if not profile.get("income_inr"):
            missing.append("income_inr")
        if not profile.get("state"):
            missing.append("state")
        if not profile.get("occupation"):
            missing.append("occupation")

        response = {
            "reply": "Please provide your profile details so I can suggest eligible schemes.",
            "scheme_suggestions": [],
            "clarification_needed": missing or ["age", "income_inr", "state", "occupation"],
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

